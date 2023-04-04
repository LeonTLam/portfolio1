import socket
import argparse
import sys
import threading
import time

# Define a custom action to retrieve ports ∊ [1024, 65535]
class PortInRangeAction(argparse.Action):
    def __call__(self, parser, namespace, port, option_string=None):
        if port < 1024 or port > 65535:
            raise argparse.ArgumentError(self, f"{port} is not in range of [1024, 65535].")
        setattr(namespace, self.dest, port) # Keep the data if within range
        
# Define a custom action to check if time > 0
class LargerThanZeroAction(argparse.Action):
    def __call__(self, parser, namespace, time, option_string=None):
        if time < 0:
            raise argparse.ArgumentError(self, "Time entered must be larger than 0.")
        setattr(namespace, self.dest, time)
        
# Define a custom action to check if interval >= 0
class LargerThanEqualZeroAction(argparse.Action):
    def __call__(self, parser, namespace, interval, option_string=None):
        if interval <= 0:
            raise argparse.ArgumentError(self, "Interval entered must be larger than 0.")
        setattr(namespace, self.dest, interval)

# Define a custom action to ensure the amount of parallel connections ∊ [1,5]        
class ParallelInRangeAction(argparse.Action):
    def __call__(self, parser, namespace, parallel, option_string=None):
        if parallel < 1 or parallel > 5:
            raise argparse.ArgumentError(self, f"The amount of parallel connections can only be between 1 and 5.")     
        setattr(namespace, self.dest, parallel)   

# Define a custom action to check for valid total size of data
class ParseSizeAction(argparse.Action):
    def __call__(self, parser, namespace, num, option_string=None):
        size_str = num.strip().lower()
        units = {'b': 1, 'kb': 1000, 'mb': 1000**2}
        size = ''.join(char for char in size_str if not char.isalpha()) # Remove the unit to further use in convertion
        unit = ''.join(char for char in size_str if not char.isdigit()) # Remove the size to validate given unit to ensure correct convertion
        if unit not in units:
            raise argparse.ArgumentError(self, f'{unit} is an invalid format of unit.')
        setattr(namespace, self.dest, num)

# Define a custom action to check for valid format of unit        
class ValidFormatAction(argparse.Action):
    def __call__(self, parser, namespace, format, option_string=None):
        format = format.strip().lower()
        units = ['b', 'kb', 'mb']
        if format not in units:
            raise argparse.ArgumentError(self, f'{format} is an invalid format of unit.')

# Define a function to convert given size of unit to Bits       
def parse_size(size_str):
    if size_str == None:
        return size_str
    else:
        size_str = size_str.strip().lower()
        units = {'b': 1, 'kb': 1000, 'mb': 1000**2}
        size = ''.join(char for char in size_str if not char.isalpha()) 
        unit = ''.join(char for char in size_str if not char.isdigit()) 
        if unit not in units:
            raise ValueError('Invalid size unit')
        return int(size) * units[unit]     

# Define a function to convert the result into requested format
def parse_size_result(size, result_format):
    units = {'b': 1, 'kb': 1000, 'mb': 1000**2}
    if result_format.strip().lower() not in units:
        raise ValueError('Invalid size unit')
    totBits = int(size) 
    return totBits / units[result_format.strip().lower()]


# Define a function to convert result unit into its corresponding 'unit per second'
def unit_per_second(result_format):
    unit = result_format.strip().lower()
    unitsPerSecond = {'b': 'Bps', 'kb': 'Kbps', 'mb': 'Mbps'}
    return unitsPerSecond[unit]
        
# Create an argument parser
parser = argparse.ArgumentParser(description="Simplified version of Iperf - invoke as server or client")

# Add all options common for server and client
parser.add_argument('-p','--port', type=int, default=8088, action=PortInRangeAction, help="Enter server's port: 1024 - 65535 (Default - 8080)")
parser.add_argument('-f','--format', type=str, default='MB', action=ValidFormatAction, help="Enter the format of the results in B, KB or MB (Default - MB).")

# Create a group for server-arguments
serverParser = parser.add_argument_group('Server')
# Add all available options to invoke the server 
serverParser.add_argument('-s', '--server', action='store_true',  help='Enable server mode.')
serverParser.add_argument('-b', '--bind', type=str, default='127.0.0.1', help="Enter server's ip address using dotted commas.")


# Create a group for client-arguments
clientParse = parser.add_argument_group('Client')
# Add all available options to invoke the client
clientParse.add_argument('-c', '--client', action='store_true', help='Enable client mode.')
clientParse.add_argument('-I', '--serverip', type=str, default='127.0.0.1', help="Enter server's ip address using dotted commas (Default - 127.0.0.1)")
clientParse.add_argument('-i','--interval', type=int, default=None, action=LargerThanEqualZeroAction, help="Enter seconds between each interval and corresponding results (Default - Null).")
clientParse.add_argument('-P','--parallel', type=int, default=1, action=ParallelInRangeAction, help="Enter amount of parallel connections: 1-5 (Default - 1).")
# Add an exclusivity to ensure only one of the arguments are provided at the time
maxGroup = clientParse.add_mutually_exclusive_group() 
maxGroup.add_argument('-n','--num', type=str, default='1234567890123B', action=ParseSizeAction, help="Enter total size of data to be sent: B, KB, MB (Cannot be used with -t or --time)")
maxGroup.add_argument('-t','--time', type=int, default=25, action=LargerThanZeroAction, help="Enter total duration in seconds for which data should be generated (Cannot be used with -n or --num)")


# Parse the commands line arguments
args = parser.parse_args()
out = [] # Results to be saved until all tasks are complete and all threads have closed
serverThreads = []

def run_server(bind , port, format):

    chunksData = 1000 # Size of chunks data will be sent in (bits)

    # Function to handle client and receive packets from client
    def handle_client(conn, addr):
        # Client connected message
        print(f'Client with {addr} is connected with {bind}:{port}.')

        # Supporting variables
        data = b'' # Initialize variable to store bits
        startInterval = 0
        endInterval = 0
        startTime = time.time() # Keep count of when the task has begun, if not already started. Also calls a function that counts.
        
        try:
            # Receive packets from client
            while True: 
                chunk = conn.recv(chunksData)
                # If an error occurs on client-side, server is informed and cancels further operations
                if chunk.decode().strip() == 'exit':
                    raise Exception("Client has Disconnected")
                if not chunk or chunk.decode().strip()[-3:] == 'BYE': # If chunks are no longer received or client sends "BYE"-message as the last three letters from a packet
                    endTime = time.time() # Record time when finished and stops counting function
                    conn.send("ACK: BYE".encode()) # Server informs the client that all packets are received
                    break
                data += chunk # Total data is stored in supporting variable
            
            # Process data to be used in result(s)
            duration = endTime - startTime # Duration data was sent in seconds
            endInterval = duration
            dataSize = parse_size_result(len(data), format) # Total size of data received in requested format
            bandwidth = dataSize / duration

            # Storing result(s) to be printed when all operations are complete
            out.append(f"{addr}\t{startInterval:.1f} - {endInterval:.4f}\t{dataSize:.4f} {format}\t\t{bandwidth:.4f} {unit_per_second(format)}")
            
        except Exception as e:
            print(f'Error communicating with {addr}: {e}')
        
        finally:
            # Closes client connection when finished
            conn.close()
            
    
    def start_server(bind, port):
        
        # Prepare a server socket and bind IP and Port.
        serverHost = bind
        serverPort = port
        
        try: 
            # Bind hostname and port to listen to maximum 5 clients
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serverSocket:
                serverSocket.bind((serverHost,serverPort))
                serverSocket.listen(5)
                print('------------------------------------------------')
                print(f'A simpleperf server is listening on port {serverPort}')
                print('------------------------------------------------')
                for i in range(2): # Mangler å gå ut av løkke når det ikke er flere clienter som kobles til 
    
                    # Accepting clients and creating threads for parallel connections
                    clientSocket, clientAddress = serverSocket.accept()
                    # Handling each thread with corresponding arguments
                    t = threading.Thread(target=handle_client, args=(clientSocket, clientAddress))
                    t.start()
                    serverThreads.append(t)
                    for thread in serverThreads:
                        thread.join()
                        
                    
                            
        except Exception as e:
            print(f'Error binding server to {serverHost}: {e}')
            sys.exit()
        
        finally:
            # Closing server bind when all threads are finished
            serverSocket.close() 
        
    start_server(bind, port)

# Initialize supporting variables 
clientThreads = []
outResult = [] # Results to be saved until all tasks are complete and all threads have closed

def run_client(host, port, totTime, format, interval, parallel, num):
    
    dataPacket = b'0' * 1000 # Format the packets of data in a size of 1000 bits
    totalData = parse_size(num) # Total amount of data in bits that will be sent to server

    def send_data(host, port):

        # Create socket connection
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
       
        try:
            global outResult # Store multiple items in global variable in case of multiple threads calling function "send_data()"
            # Connect client socket to server 
            clientSocket.connect((host, port))
            clientIp, clientPort = clientSocket.getsockname()

            # Supporting variables to process time
            startInterval = endInterval = tempInterval = 0

            startTime = time.time() # Keep track of when the task began
            tempStart = time.time() # Keep track of when the interval began
            # If client is invoked with argument -t or --time
            if totTime:
                dataSent = 0 # Supporting variable which will help keep count of the amount packets sent in total
                startSent = 0 # Supporting variable which help keep count of the amount of packets sent during interval
                # While elapsed time <= args.time
                while (time.time() - startTime) <= totTime:
                    # Continously send packets to server and keep track of how many packets sent
                    clientSocket.send(dataPacket) 
                    dataSent += len(dataPacket)
                    # If client invoked with argument -i or --interval
                    if interval:
                        # If elapsed time exceeds user-inputted interval, execute code
                        if time.time() - tempStart >= interval:
                            # Reset the "start"-time for the next interval
                            tempStart = time.time()

                            # Number of bits from start of interval to end of interval
                            currSent = dataSent
                            diffSent = currSent - startSent
                            startSent = currSent

                            # Supporting variables for length of interval
                            tempInterval = endInterval
                            endInterval += interval

                            # Datasize parsed in requested dataformat and bandwidth based on interval length and data sent during interval
                            dataSize = parse_size_result(diffSent, format)
                            bandwidth = dataSize / (interval)

                            # Print interval, data sent during interval and bandwidth during interval
                            print(f"{clientIp}:{clientPort}\t{tempInterval:.1f} - {endInterval:.1f}\t{dataSize:.4f} {format}\t\t{bandwidth:.4f} {unit_per_second(format)}") 
                        # If user-inputted interval lasts longer than total time of operation
                        elif interval >= totTime:
                            print(f'No data on interval - Interval {interval} is larger than or equal total time {totTime}!')
                            clientSocket.send('exit'.encode())
                            sys.exit()
            # If client is invoked with argument -n or --num
            if totalData:
                dataSent = 0 # Supporting variable which will help keep count of the amount packets that have been sent
                startSent = 0 # Supporting variable which help keep count of the amount of packets sent during interval
                # While the amount of data sent <= user-inputted max data TO BE sent
                while dataSent <= totalData:
                    clientSocket.send(dataPacket)
                    dataSent += len(dataPacket)
                    # If client invoked with argument -i or --interval
                    if interval:
                        # If elapsed time exceeds user-inputted interval, execute code
                        if time.time() - tempStart >= interval:
                            # Reset the "start"-time for the next interval
                            tempStart = time.time()

                            # Number of bits from start of interval to end of interval
                            currSent = dataSent
                            diffSent = currSent - startSent
                            startSent = currSent

                            # Supporting variables for length of interval
                            tempInterval = endInterval
                            endInterval += interval

                            # Datasize parsed in requested dataformat and bandwidth based on interval length and data sent during interval
                            dataSize = parse_size_result(diffSent, format)
                            bandwidth = dataSize / (interval)

                            # Print interval, data sent during interval and bandwidth during interval
                            print(f"{clientIp}:{clientPort}\t{tempInterval:.1f} - {endInterval:.1f}\t{dataSize:.4f} {format}\t\t{bandwidth:.4f} {unit_per_second(format)}") 
            
            # After total time or max data is exceeded, client sends confirmation to the server
            clientSocket.send('BYE'.encode()) 
            # Client waits for server's response 
            while True:
                message = clientSocket.recv(1024)
                # Store "endTime" if server responds with confirmation
                if message.decode().strip() == "ACK: BYE":
                    endTime = time.time()
                    break

            # Process data to be used in result(s)
            duration = float(endTime) - float(startTime)
            endInterval = duration
            dataSize = parse_size_result(dataSent, format)
            bandwidth = dataSize / duration
            
            outResult.append(f"{clientIp}:{clientPort}\t{startInterval:.1f} - {endInterval:.4f}\t{dataSize:.4f} {format}\t\t{bandwidth:.4f} {unit_per_second(format)}")
        
        except Exception as e:
            print(f'Error connecting to {host}:{port}: {e}')
        
        finally:
            clientSocket.close()          
    
    # Function to create thread(s) to be further connected to the addressed server    

    def connect_server(host, port):
        # Prepare server's IP address and port
        serverHost = host
        serverPort = port
        th = ''
        print('------------------------------------------------------------')
        print(f'Simpleperf client(s) connecting to server {serverHost}, port {serverPort}')
        print('------------------------------------------------------------')
        print('ID\t\tInterval\tTransfer\tBandwidth')
        # Create the amount of parallel connections requested
        for i in range(parallel):
            th = threading.Thread(target=send_data, args=(serverHost,serverPort))
            th.start()
            clientThreads.append(th)
        
        for thread in clientThreads:
            thread.join()

    connect_server(host, port)

# If program is invoked as server
if args.server and not args.client:
    try:
        run_server(args.bind, args.port, args.format)
    except Exception as e:
        sys.exit()
    finally:
        print('ID\t\tInterval\tTransfer\tBandwidth')
        for e in out:
            print(e)
    

# If program is invoked as client
elif args.client and not args.server:
    # If the client is invoked with arguement -t or --time, the run-function is called without a value for -n or --num
    if args.time and args.num == '1234567890123B':
        try:
            print('time')
            run_client(args.serverip, args.port, args.time, args.format, args.interval, args.parallel, None)
        except Exception as e:
            sys.exit()
        finally:
            # If intervals are printed along the way, print a line to separate the results into two sections
            if args.interval:
                print('------------------------------------------------------------')
            # If there are no longer any active threads and server sends acknowledgement, result and interval is returned
            for e in outResult:
                print(e)
    # If the client is invoked with arguement -n or --num, the run-function is called without a value for -t or --time
    elif args.num != '1234567890123B' and args.time == 25:
        try:
            print('num')
            run_client(args.serverip, args.port, None, args.format, args.interval, args.parallel, args.num)
        except Exception as e:
            sys.exit()
        finally:
            # If intervals are printed along the way, print a line to separate the results into two sections
            if args.interval:
                print('------------------------------------------------------------')
            # If there are no longer any active threads and server sends acknowledgement, result and interval is returned
            for e in outResult:
                print(e)
    else:
        print("Error: you must run either -t or -n (if none, -t will be used)")
        sys.exit()

# If program is neither invoked as server nor client
else:
    print("Error: you must run either in server or client mode")
    parser.print_help()
    sys.exit()