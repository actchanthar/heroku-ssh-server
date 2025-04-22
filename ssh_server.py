import paramiko
import socket
import threading
import os
from paramiko import RSAKey
from pyngrok import ngrok

host_key = RSAKey.generate(2048)

class SSHServer(paramiko.ServerInterface):
    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        if username == os.getenv("SSH_USERNAME") and password == os.getenv("SSH_PASSWORD"):
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

def start_server():
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

def start_ngrok():
    ngrok.set_auth_token("2w4bYabT1dLCfLue2PhWGQgerbs_NTCtqFcpHQbNYABbxXAy")
    tunnel = ngrok.connect(2222, "tcp")
    print(f"ngrok tunnel created: {tunnel.public_url}")

if __name__ == "__main__":
    ngrok_thread = threading.Thread(target=start_ngrok)
    ngrok_thread.start()
    start_server()