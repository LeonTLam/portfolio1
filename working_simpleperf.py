import sys
import argparse
import socket
import time
import threading
from typing import Tuple

def format_bytes(size: int, unit: str) -> float:
    if unit == 'KB':
        return size / 1000
    elif unit == 'MB':
        return size / 1000 / 1000
    else:
        return size

def handle_client(client_socket: socket.socket, client_address: Tuple[str, int], server_address: Tuple[str, int], args: argparse.Namespace) -> None:
    total_received = 0
    start_time = time.time()

    while True:
        data = client_socket.recv(1000)
        if data == b'BYE':
            break
        total_received += len(data)

    elapsed_time = time.time() - start_time
    received_formatted = format_bytes(total_received, args.format)
    rate = (total_received * 8) / (elapsed_time * 1000 * 1000)

    client_socket.sendall(b'ACK: BYE')
    
    client_socket.close()

    print(f"A simpleperf client with {client_address} is connected with {server_address}")
    print("\tID\t\tInterval\tReceived\tRate")
    print(f"{client_address}\t0.0 - {elapsed_time:.2f}\t{received_formatted:.0f} {args.format}\t\t{rate:.2f} Mbps")        

def server_mode(args: argparse.Namespace) -> None:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_ip = socket.gethostbyname(socket.gethostname())
    server_address = (args.bind if args.bind else server_ip, args.port)
    server_socket.bind(server_address)
    server_socket.listen(5)

    print("---------------------------------------------")
    print(f"A simpleperf server is listening on port {args.port}")
    print("---------------------------------------------")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address, server_address, args))
            client_handler.start()
    except KeyboardInterrupt:
        print("Closing server.")
    finally:
        server_socket.close()

def client_send(client_socket, server_address, args, end_time):
    total_sent = 0
    data_chunk = b'\x00' * 1000

    def print_stats():
        start_time = time.time()
        current_time = start_time

        while current_time < end_time:
            time.sleep(args.interval)
            current_time = time.time()
            elapsed_time = current_time - start_time
            interval_start = elapsed_time - args.interval
            sent_formatted = format_bytes(total_sent, args.format)
            rate = (total_sent * 8) / (elapsed_time * 1000 * 1000)

            print(f"{server_address}\t{interval_start:.1f}-{elapsed_time:.2f}\t{sent_formatted:.0f} {args.format}\t\t{rate:.2f} Mbps")

    if args.interval:
        stats_thread = threading.Thread(target=print_stats)
        stats_thread.start()

    try:
        while time.time() < end_time:
            client_socket.sendall(data_chunk)
            total_sent += len(data_chunk)
    except socket.error:
        pass

    if args.interval:
        stats_thread.join()

    client_socket.sendall(b'BYE')
    response = client_socket.recv(1024)

    elapsed_time = time.time() - (end_time - args.time)
    sent_formatted = format_bytes(total_sent, args.format)
    rate = (total_sent * 8) / (elapsed_time * 1000 * 1000)

    print("----------------------------------------------------")
    print(f"{server_address}\t0.0 - {elapsed_time:.2f}\t{sent_formatted:.0f} {args.format}\t\t{rate:.2f} Mbps")

    client_socket.close()



def client_mode(args: argparse.Namespace) -> None:
    server_address = (args.serverip, args.port)
    
    print("-------------------------------------------------------")
    print(f"A simpleperf client connecting to server {args.serverip}, port {args.port}")
    print("-------------------------------------------------------")
    
    connections = []
    threads = []
    
    for _ in range(args.parallel):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(server_address)
        connections.append(client_socket)
        print(f"Client connected with {args.serverip} port {args.port}")

    start_time = time.time()
    end_time = start_time + args.time

    for client_socket in connections:
        t = threading.Thread(target=client_send, args=(client_socket, server_address, args, end_time))
        t.start()
        threads.append(t)

    print("\tID\t\tInterval\tTransfer\tBandwidth")

    for t in threads:
        t.join()



def main() -> None:
    parser = argparse.ArgumentParser(description='simpleperf network throughput measurement tool')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-s', '--server', action='store_true', help='enable server mode')
    group.add_argument('-c', '--client', action='store_true', help='enable client mode')

    parser.add_argument('-b', '--bind', type=str, metavar='IP', help='bind IP address for server')
    parser.add_argument('-I', '--serverip', type=str, metavar='IP', help='server IP address for client')
    parser.add_argument('-p', '--port', type=int, metavar='PORT', default=8088, help='port number (default: 8088)')
    parser.add_argument('-t', '--time', type=int, metavar='TIME', default=25, help='duration in seconds (default: 25)')
    parser.add_argument('-f', '--format', type=str, metavar='UNIT', default='MB', choices=['B', 'KB', 'MB'], help='result format (default: MB)')
    parser.add_argument('-i', '--interval', type=int, metavar='SECONDS', help='print statistics per interval in seconds')
    parser.add_argument('-P', '--parallel', type=int, metavar='N', default=1, help='number of parallel connections (default: 1)')
    parser.add_argument('-n', '--num', type=str, metavar='SIZE', help='transfer specified number of bytes (B, KB, or MB)')


    args = parser.parse_args()
    if args.server:
        server_mode(args)
    elif args.client:
        client_mode(args)
    else:
        print("Error: you must run either in server or client mode")
        sys.exit(1)

if _name_ == '_main_':
    main()