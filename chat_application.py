import socket
import threading
import time
from flask import Flask, request, jsonify

# Constants
SERVER_PORT = 5000
BROADCAST_PORT = 5001
BROADCAST_INTERVAL = 5
MAX_CLIENTS = 20
PASSWORD = "11709"

# Global Variables
clients = []
clients_lock = threading.Lock()
messages = []  # Store messages
client_count = 0  # Track number of connected clients

# Flask setup
app = Flask(__name__)

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
    global client_count
    with clients_lock:
        client_count += 1
    print(f"New connection from {addr}")
    welcome_message = f"{addr} has joined the chat!"
    broadcast(welcome_message.encode(), client_socket)

    while True:
        try:
            message = client_socket.recv(1024)
            if message:
                print(f"Received from {addr}: {message.decode()}")
                messages.append(message.decode())  # Store received message
                broadcast(message, client_socket)
            else:
                remove_client(client_socket)
                break
        except Exception:
            remove_client(client_socket)
            break

# Function to remove disconnected clients
def remove_client(client_socket):
    global client_count
    with clients_lock:
        if client_socket in clients:
            clients.remove(client_socket)
            client_count -= 1  # Decrement client count
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

# Flask routes
@app.route('/messages', methods=['GET'])
def get_messages():
    return jsonify({'messages': messages})

@app.route('/send', methods=['POST'])
def send_message():
    data = request.get_json()
    message = data.get('message')
    messages.append(message)
    broadcast(f"Client: {message}".encode())
    return '', 204

@app.route('/clients', methods=['GET'])
def get_client_count():
    return jsonify({'count': client_count})

if __name__ == "__main__":
    # Start the server in a thread
    server_thread = threading.Thread(target=start_server)
    server_thread.start()
    app.run(host='0.0.0.0', port=int(SERVER_PORT), use_reloader=False)  # Start Flask server
