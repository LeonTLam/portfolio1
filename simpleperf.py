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
        if time <= 0:
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
parser = argparse.ArgumentParser(description="Simplified version of Iperf - measuring bandwidth and network performance.")

# Create a group for server-arguments
sParse = parser.add_argument_group('Server') 
# Add all available options to invoke the server 
sParse.add_argument('-s', '--server', action='store_true', help='Enable server mode.')
sParse.add_argument('-b', '--bind', type=str, default='127.0.0.1', help="Enter server's ip address using dotted commas.")
sParse.add_argument('-sp','--sport', type=int, default=8088, action=PortInRangeAction, help="Enter server's port (1024, 65535)")
sParse.add_argument('-sf','--sformat', type=str, default='MB', action=ValidFormatAction, help="Enter the format of the results in B, KB or MB (default).")

# Create a group for client-arguments
cParse = parser.add_argument_group('Client')
cParse.add_argument('-c', '--client', action='store_true', help='Enable client mode.')
cParse.add_argument('-I', '--serverip', type=str, default='127.0.0.1', help="Enter server's ip address using dotted commas.")
cParse.add_argument('-cp','--cserverport', type=int, default=8088, action=PortInRangeAction, help="Enter server's port (1024, 65535)")
cParse.add_argument('-t','--time', type=int, default=2, action=LargerThanZeroAction, help="Enter total duration in seconds for which data should be generated.")
cParse.add_argument('-cf','--cformat', type=str, default='MB', action=ValidFormatAction, help="Enter the format of the results in B, KB or MB (default).")
cParse.add_argument('-i','--interval', type=int, default=0, action=LargerThanEqualZeroAction, help="Enter seconds between each print og statistics.")
cParse.add_argument('-p','--parallel', type=int, default=1, action=ParallelInRangeAction, help="Enter amount of parallel connections (1-5).")
cParse.add_argument('-n','--num', type=str, default='1234567890123B', action=ParseSizeAction, help="Enter total size of data to be sent (B, KB, MB).")

# Parse the commands line arguments
args = parser.parse_args()

# If program is invoked as server
if args.server and not args.client:
    
    # Initialize the arguments used to invoke the program as a server
    resultFormat = args.sformat # Which unit the result(s) will be displayed
    chunksData = 1000 # Size of chunks data will be sent in (bits)
    outResult = '' # Results to be saved until all tasks are complete and all threads have closed
    
    
    # Function to handle client and receive packets from client
    def handle_client(conn, addr, thread):
        global outResult
        print(f'Client with {addr} is connected with {args.bind}:{args.sport}.')
        data = b'' # Initialize variable to store bits
        startTime = time.time() # Keep count of when the task has begun, if not already started. Also calls a function that counts.
        
        try:
            while time.time() - startTime < 4: ##MÅFIKSES
                chunk = conn.recv(chunksData)
                if chunk.decode().strip() == 'BYE': # If chunks are no longer received or client sends "BYE"-message
                    endTime = time.time() # Record time when finished and stops counting function
                    conn.send("ACK: BYE".encode())
                    break
                data += chunk
            endTime = time.time()
            duration = endTime - startTime # Duration data was sent in seconds
            dataSize = parse_size_result(len(data), resultFormat) # Total size of data received in requested format
            bandwidth = dataSize / duration
            
            outResult += f"{addr}\t{startTime:.2f} - {endTime:.2f}\t{dataSize} {resultFormat}\t{bandwidth} {unit_per_second(resultFormat)}\n"
            
            print('ID\t\t\tInterval\t\t\tTransfer\tBandwidth')
            print(outResult)
                
        except Exception as e:
            print(f'Error communicating with {addr}: {e}')
        
        finally:
            # Closes client connection when finished
            conn.close()
    
    def start_server():
        # Prepare a server socket and bind IP and Port.
        serverHost = '127.0.0.1'
        serverPort = 8088
        t = ''
        try: 
        # Bind hostname and port to listen to maximum 5 clients
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serverSocket:
                serverSocket.bind((serverHost,serverPort))
                serverSocket.listen(5)
                print('------------------------------------------------')
                print(f'A simpleperf server is listening on port {serverPort}')
                print('------------------------------------------------')
                
                # Accepting clients and creating threads for parallel connections
                
                clientSocket, clientAddress = serverSocket.accept()
                
                # Handling each thread with corresponding arguments
                t = threading.Thread(target=handle_client, args=(clientSocket, clientAddress, t))
                t.start()
                    
                # Closing server bind when all threads are finished
                serverSocket.close()
        
        except Exception as e:
            print(f'Error binding server to {serverHost}: {e}')
        
    start_server()

# If program is invoked as client
elif args.client and not args.server:
    
    # Initialize the arguments used to invoke the program as a client
    dataPacket = b'0' * 1000 # Format the packets of data in a size of 1000 bits
    timePerConnection = args.time # Duration in seconds for which data should be generated and sent
    resultFormat = args.cformat # Which unit the result(s) will be displayed
    resultInterval = args.interval # Which interval the results will be displayed
    numThreads = args.parallel # Amount of parallel connections of clients will send data to server
    totalData = parse_size(args.num) # Total amount of data in bits that will be sent to server
    
    # Initialize supporting variables 
   
    outResult = [] # Results to be saved until all tasks are complete and all threads have closed
    
    def send_data(host, port, thread):
        # Create socket connection
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientSocket:
            global outResult
            global timePerConnection
            message = 'BYE'
            # Connect client socket to server 
            clientSocket.connect((host, port))
            clientIp, clientPort = clientSocket.getsockname()
            
            dataSent = 0 # Supporting variable which will help keep count of the amount packets that have been sent
            startTime = time.time() # Keep count of when the task has begun, if not already started. Also calls a function that counts.
            
            # While maximum data sent and maximum time elapsed is not exceeded, packets are sent to the server from each client connection
            while time.time() - startTime < timePerConnection:
                if dataSent >= totalData:
                    clientSocket.send(message.encode())
                    endTime = time.time()
                    break
                clientSocket.send(dataPacket)
                dataSent += len(dataPacket)
              
            endTime = time.time()
            
            duration = endTime - startTime
            dataSize = parse_size_result(dataSent, resultFormat)
            bandwidth = dataSize / duration
            
            outResult.append(f"{clientIp}:{clientPort}\t{startTime:.2f} - {endTime:.2f}\t{dataSize} {resultFormat}\t{bandwidth} {unit_per_second(resultFormat)}")
            
            # If there are no longer any active threads and server sends acknowledgement, result proceeds to be printed to the client
            print('ID\t\tInterval\t\t\tTransfer\tBandwidth')
            for e in outResult:
                print(e)
                time.sleep(resultInterval)
            
        
        clientSocket.close()           
    
    
        
          
            
    
    # Function to create thread(s) to be further connected to the addressed server        
    def connect_server():
        # Prepare server's IP address and port
        serverHost = args.serverip
        serverPort = args.cserverport
        th = ''
        print('------------------------------------------------------------')
        print(f'Simpleperf client(s) connecting to server {serverHost}, port {serverPort}')
        print('------------------------------------------------------------')
        
        # Create the amount of parallel connections requested
        for i in range(numThreads):
            th = threading.Thread(target=send_data, args=(serverHost,serverPort,th))
            th.start()
            
    connect_server()

# If program is neither invoked as server nor client
else:
    print("Error: you must run either in server or client mode")
    sys.exit()