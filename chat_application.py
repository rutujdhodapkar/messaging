import socket
import threading
import time

# Constants
SERVER_PORT = 5000
BROADCAST_PORT = 5001
BROADCAST_INTERVAL = 5
MAX_CLIENTS = 20
PASSWORD = "11709"

# Global Variables
clients = []
clients_lock = threading.Lock()

# Function to broadcast messages to all connected clients
def broadcast(message, sender_socket=None):
    with clients_lock:
        for client in clients:
            if client != sender_socket:
                try:
                    client.send(message)
                except:
                    remove_client(client)

# Function to handle client connections
def handle_client(client_socket, addr):
    print(f"New connection from {addr}")
    welcome_message = f"{addr} has joined the chat!"
    broadcast(welcome_message.encode(), client_socket)

    while True:
        try:
            message = client_socket.recv(1024)
            if message:
                print(f"Received from {addr}: {message.decode()}")
                broadcast(message, client_socket)
            else:
                remove_client(client_socket)
                break
        except Exception:
            remove_client(client_socket)
            break

# Function to remove disconnected clients
def remove_client(client_socket):
    with clients_lock:
        if client_socket in clients:
            clients.remove(client_socket)
            try:
                client_socket.close()
            except Exception as e:
                print(f"Error closing client socket: {e}")
            broadcast(f"A client has left the chat.".encode(), client_socket)

# Function to broadcast server availability
def broadcast_server():
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    while True:
        message = "CHAT_SERVER_AVAILABLE".encode()
        broadcast_socket.sendto(message, ('<broadcast>', BROADCAST_PORT))
        time.sleep(BROADCAST_INTERVAL)

# Function for the server to send messages
def send_server_messages():
    while True:
        message = input('Server: ')
        if message.strip():
            broadcast(f"Server: {message}".encode())

# Function to start the server
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', SERVER_PORT))
    server_socket.listen()
    print(f"Server started and listening on port {SERVER_PORT}")

    broadcast_thread = threading.Thread(target=broadcast_server, daemon=True)
    broadcast_thread.start()

    while True:
        if len(clients) < MAX_CLIENTS:
            client_socket, addr = server_socket.accept()
            with clients_lock:
                clients.append(client_socket)
            client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
            client_thread.start()
        else:
            print("Max clients connected!")

# Function to discover the server
def discover_server():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client_socket.bind(('', BROADCAST_PORT))
    print("Looking for server...")

    while True:
        message, addr = client_socket.recvfrom(1024)
        if message.decode() == "CHAT_SERVER_AVAILABLE":
            print(f"Server found at {addr[0]}:{SERVER_PORT}")
            return addr[0]

# Function to check if the server is running
def is_server_running():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        result = sock.connect_ex(('localhost', SERVER_PORT))
        return result == 0  # Return True if the connection was successful (server is running)

# Function to run the client
def run_client():
    server_ip = discover_server()
    if server_ip:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_ip, SERVER_PORT))

        def receive_messages():
            while True:
                try:
                    message = client_socket.recv(1024).decode()
                    if message:
                        print(message)
                    else:
                        break
                except Exception:
                    print("Connection to server lost.")
                    break

        receive_thread = threading.Thread(target=receive_messages)
        receive_thread.start()

        while True:
            message = input('You: ')
            if message.strip():
                client_socket.send(message.encode())

# Main function to start server or client
def main():
    if is_server_running():
        print("Server is already running.")
        role = 'c'  # Automatically run as client
    else:
        role = input("Do you want to be a Server or Client? (s/c): ").strip().lower()

    if role == 's':
        password = input("Enter server password: ")
        if password == PASSWORD:
            start_server()
        else:
            print("Incorrect password. Exiting.")
    elif role == 'c':
        run_client()
    else:
        print("Invalid choice. Exiting.")

if __name__ == "__main__":
    main()
