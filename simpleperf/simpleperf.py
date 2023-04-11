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
        format = format.strip().upper()
        units = {'B':'B', 'KB':'Kb', 'MB':'Mb'} # Dictionary value with correct capilization to be used as i.e. '{Mb}ps' or '{Mb}'
        if format not in units:
            raise argparse.ArgumentError(self, f'{format} is an invalid format of unit.')
        setattr(namespace, self.dest, units[format])

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

def unit_per_second(result_format):
        unit = result_format.strip().lower()
        unitsPerSecond = {'b': 'Bps', 'kb': 'Kbps', 'mb': 'Mbps'}
        return unitsPerSecond[unit]

out = []
# Function to handle client and receive packets from client
def handle_client(conn, addr, args: argparse.Namespace):
    # Client connected message
    print(f'Client with {addr} is connected with {args.bind}:{args.port}.')

    # Supporting variables
    data = b'' # Initialize variable to store bits
    startInterval = 0
    startTime = time.time() # Keep count of when the task has begun, if not already started. Also calls a function that counts.
    global outResult
    try:
        # Receive packets from client
        while True: 
            chunk = conn.recv(1000)
            # If an error occurs on client-side, server is informed and cancels further operations
            if chunk.decode().strip() == 'exit':
                raise Exception("Client has Disconnected")
            if not chunk or chunk.decode().strip()[-3:] == 'BYE': # If chunks are no longer received or client sends "BYE"-message as the last three letters from a packet
                endTime = time.time() # Record time when finished and stops counting function
                conn.send("ACK: BYE".encode()) # Server informs the client that all packets are received
                break
            data += chunk # Total data is stored in supporting variable
        
        # Process data to be used in result(s)
        elapsedTime = endTime - startTime # Duration data was sent in seconds
        endInterval = elapsedTime
        dataSize = parse_size_result(len(data), args.format) # Total size of data received in requested format
        bandwidth = parse_size_result(len(data), 'MB') / elapsedTime

        # Print result(s) 
        print('ID\t\tInterval\tTransfer\tBandwidth')
        if args.format.lower() == 'mb': # Print out total number of bytes received with two decimals if requested format is in 'MB'
            print(f"{addr}\t\t{startInterval:.1f} - {endInterval:.1f}\t{dataSize:.2f} {args.format}\t{bandwidth:.2f} {unit_per_second('Mb')}")
        else: # Print out total bytes as a whole number if requested format is a smaller form than 'MB'
            print(f"{addr}\t\t{startInterval:.1f} - {endInterval:.1f}\t{int(dataSize)} {args.format}\t{bandwidth:.2f} {unit_per_second('Mb')}")
    except Exception as e:
        print(f'Error communicating with {addr}: {e}')
    
    finally:
        # Closes client connection when finished
        conn.close()
        
    
def start_server(args: argparse.Namespace):
    
    # Prepare a server socket and bind IP and Port.
    serverHost = args.bind
    serverPort = args.port
    
    
    # Bind hostname and port to listen to maximum 5 clients
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serverSocket:
        serverSocket.bind((serverHost,serverPort))
        serverSocket.listen(5)
        print('------------------------------------------------')
        print(f'A simpleperf server is listening on port {serverPort}')
        print('------------------------------------------------')
        
        threads = []
        
        try: 
            while True: # Mangler å gå ut av løkke når det ikke er flere clienter som kobles til 
                try:
                    # Accepting clients and creating threads for parallel connections
                    clientSocket, clientAddress = serverSocket.accept()
                except KeyboardInterrupt:
                    print('Closing server')
                    sys.exit(1)
                
                # Handling each thread with corresponding arguments
                t = threading.Thread(target=handle_client, args=(clientSocket, clientAddress, args))
                t.start()
                
        except Exception as e:
            print(f'Server {serverHost}:{serverPort}: {e}') # Reports issues when binding server or when server closes
        
        # Closing server bind when all threads are finished
        serverSocket.close() 

# Initialize supporting variables 
outResult = [] # Results to be saved until all tasks are complete and all threads have closed

def send_data(clientSocket, args, mode, endTime):
    dataPacket = b'0' * 1000 # Format the packets of data in a size of 1000 bits
    dataSent = 0 # Supporting variable which will help keep count of the amount packets sent in total
    startInterval  = 0 # Supporting variable to display start-interval
    global outResult # Store multiple items in global variable in case of multiple threads calling function "send_data()"
    
    clientIp, clientPort = clientSocket.getsockname()

    # Print results for each interval every second requested by user-input 'args.interval'
    def print_interval():
        startSent = 0 # Supporting variable to calculate how much data was sent during an interval
        startTime = time.time()
        currentTime = startTime
        currentSent = 0
        if mode == 'time':
            # Print intervals within user-inputted time-frame
            while currentTime < endTime:
                time.sleep(args.interval)
                currentTime = time.time()
                elapsedTime = currentTime - startTime
                startInterval = elapsedTime - args.interval
                
                currentSent = dataSent
                diffSent = currentSent - startSent
                startSent = currentSent
                
                formatSent = parse_size_result(diffSent, args.format)
                bandwidth = formatSent / elapsedTime
                if args.format.lower() == 'mb': # Print out total number of bytes received with two decimals if requested format is in 'MB'
                    print(f"{clientIp}:{clientPort}\t{startInterval:.1f} - {elapsedTime:.1f}\t{formatSent:.2f} {args.format}\t{bandwidth:.2f} {unit_per_second('Mb')}")
                else: # Print out total bytes as a whole number if requested format is a smaller form than 'MB'
                    print(f"{clientIp}:{clientPort}\t{startInterval:.1f} - {elapsedTime:.1f}\t{int(formatSent)} {args.format}\t{bandwidth:.2f} {unit_per_second('Mb')}")
               
        elif mode == 'num':
            # Print intervals within user-inputted max-data
            while currentSent < parse_size(args.num): # Parse args.num in bits 
                time.sleep(args.interval)
                currentTime = time.time()
                elapsedTime = currentTime - startTime
                startInterval = elapsedTime - args.interval
                
                currentSent = dataSent
                diffSent = currentSent - startSent
                startSent = currentSent
                
                formatSent = parse_size_result(diffSent, args.format)
                bandwidth = formatSent / elapsedTime
                
                if args.format.lower() == 'mb': # Print out total number of bytes received with two decimals if requested format is in 'MB'
                    print(f"{clientIp}:{clientPort}\t{startInterval:.1f} - {elapsedTime:.1f}\t{formatSent:.2f} {args.format}\t{bandwidth:.2f} {unit_per_second('Mb')}")
                else: # Print out total bytes as a whole number if requested format is a smaller form than 'MB'
                    print(f"{clientIp}:{clientPort}\t{startInterval:.1f} - {elapsedTime:.1f}\t{int(formatSent)} {args.format}\t{bandwidth:.2f} {unit_per_second('Mb')}")
               
    if args.interval:
        intervalThread = threading.Thread(target=print_interval)
        intervalThread.start()
    
    # If client is invoked with argument -t or --time
    if mode == 'time':
        try:
        # While elapsed time <= args.time
            while time.time() < endTime:
                # Continously send packets to server and keep track of how many packets sent
                clientSocket.sendall(dataPacket) 
                dataSent += len(dataPacket)
        except socket.error:
            pass
        
    # If client is invoked with argument -n or --num
    elif mode == 'num':
        try:
            # While the amount of data sent <= user-inputted max data TO BE sent
            while dataSent <= parse_size(args.num):
                clientSocket.send(dataPacket)
                dataSent += len(dataPacket)
        except socket.error:
            pass
              
    if args.interval:
                intervalThread.join()
                
    # After total time or max data is exceeded, client sends confirmation to the server
    clientSocket.sendall('BYE'.encode()) 
    
    # Client waits for server's response 
    while True:
        message = clientSocket.recv(1024)
        # Store "endTime" if server responds with confirmation
        if message.decode().strip() == "ACK: BYE":
            break

    # Process data to be used in result(s)
    elapsedTime = time.time() - (endTime - args.time)
    dataSize = parse_size_result(dataSent, args.format)
    bandwidth = dataSize / elapsedTime
    
    if args.format.lower() == 'mb': # Print out total number of bytes received with two decimals if requested format is in 'MB'
        outResult.append(f"{clientIp}:{clientPort}\t{startInterval:.1f} - {elapsedTime:.1f}\t{dataSize:.2f} {args.format}\t{bandwidth:.2f} {unit_per_second('Mb')}")
    else: # Print out total bytes as a whole number if requested format is a smaller form than 'MB'
        outResult.append(f"{clientIp}:{clientPort}\t{startInterval:.1f} - {elapsedTime:.1f}\t{int(dataSize)} {args.format}\t{bandwidth:.2f} {unit_per_second('Mb')}")
               
    clientSocket.close()
        

# Function to create thread(s) to be further connected to the addressed server    

def connect_server(args: argparse.Namespace, mode):
    # Prepare server's IP address and port
    serverHost = args.serverip
    serverPort = args.port
    
    print('------------------------------------------------------------')
    print(f'Simpleperf client(s) connecting to server {serverHost}, port {serverPort}')
    print('------------------------------------------------------------')
    
    connections = []
    threads = []
    
    # Create the amount of parallel connections requested
    for i in range(args.parallel):
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((serverHost, serverPort))
        connections.append(clientSocket)
        
    endTime = time.time() + args.time
    
    for clients in connections:
        t = threading.Thread(target=send_data, args=(clients, args, mode, endTime))
        t.start()
        threads.append(t)
    
    print('ID\t\tInterval\tTransfer\tBandwidth')
    
    for thread in threads:
        thread.join()

def main():
            
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

    # If program is invoked as server
    if args.server and not args.client:
        try:
            start_server(args)
        except Exception as e:
            print(f'{args.bind}:{args.port} : {e}')
            sys.exit()
        

    # If program is invoked as client
    elif args.client and not args.server:
        # If the client is invoked with arguement -t or --time, the run-function is called without a value for -n or --num
        if args.time and args.num == '1234567890123B':
            mode = 'time'
            connect_server(args, mode)
        
            # If intervals are printed along the way, print a line to separate the results into two sections
            if args.interval:
                print('------------------------------------------------------------')
            # If there are no longer any active threads and server sends acknowledgement, result and interval is returned
            for e in outResult:
                print(e)
        # If the client is invoked with arguement -n or --num, the run-function is called without a value for -t or --time
        elif args.num != '1234567890123B' and args.time == 25:
            mode = 'num'
            connect_server(args, mode)
        
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
        
if __name__ == "__main__":
    main()