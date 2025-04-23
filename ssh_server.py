import paramiko
import socket
import threading
import os
import asyncio
from aiohttp import web
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

async def handle_ssh_over_http(request):
    ssh_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        ssh_socket.connect(("localhost", 2222))
        print("Connected to internal SSH server")

        data = await request.read()
        ssh_socket.sendall(data)

        response_data = b""
        while True:
            chunk = ssh_socket.recv(1024)
            if not chunk:
                break
            response_data += chunk

        return web.Response(body=response_data)

    except Exception as e:
        print(f"Error in HTTP handler: {e}")
        return web.Response(text=f"Error: {e}", status=500)
    finally:
        ssh_socket.close()

async def start_http_server():
    port = int(os.getenv("PORT", 2222))
    print(f"Starting HTTP server on port {port}")
    app = web.Application()
    app.router.add_route('*', '/ssh', handle_ssh_over_http)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

if __name__ == "__main__":
    ssh_thread = threading.Thread(target=start_ssh_server)
    ssh_thread.start()

    # Create a new event loop and run the HTTP server
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_http_server())
    loop.run_forever()