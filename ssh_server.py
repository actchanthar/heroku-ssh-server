import paramiko
import socket
import threading
import os
import asyncio
import websockets
from paramiko import RSAKey

host_key = RSAKey.generate(2048)

class SSHServer(paramiko.ServerInterface):
    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        if username == "user" and password == "securepassword123":
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

def start_ssh_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", 2222))
    server_socket.listen(100)

    print("SSH server running on port 2222...")
    while True:
        client_socket, addr = server_socket.accept()
        transport = paramiko.Transport(client_socket)
        transport.add_server_key(host_key)
        server = SSHServer()
        transport.start_server(server=server)
        chan = transport.accept(20)
        if chan:
            print(f"Client connected: {addr}")
            chan.close()

async def ssh_websocket_handler(websocket, path):
    print("WebSocket client connected")
    ssh_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Connect to the internal SSH server on port 2222
        ssh_socket.connect(("localhost", 2222))
        print("Connected to internal SSH server")

        # Forward data between WebSocket and SSH socket
        async def forward_ws_to_ssh():
            while True:
                data = await websocket.recv()
                ssh_socket.sendall(data)

        async def forward_ssh_to_ws():
            while True:
                data = ssh_socket.recv(1024)
                if not data:
                    break
                await websocket.send(data)

        # Run both forwarding tasks concurrently
        await asyncio.gather(forward_ws_to_ssh(), forward_ssh_to_ws())

    except Exception as e:
        print(f"Error in WebSocket handler: {e}")
    finally:
        ssh_socket.close()

def start_websocket_server():
    port = int(os.getenv("PORT", 2222))  # Use Heroku's $PORT
    print(f"Starting WebSocket server on port {port}")
    start_server = websockets.serve(ssh_websocket_handler, "0.0.0.0", port)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    # Start the SSH server in a separate thread
    ssh_thread = threading.Thread(target=start_ssh_server)
    ssh_thread.start()

    # Start the WebSocket server in the main thread
    start_websocket_server()