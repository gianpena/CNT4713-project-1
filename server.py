import socketserver, socket, sys, re
from collections import deque

available_ports = deque(range(10000,65537))
active_users = {}

def broadcast(msg):
    for socket in active_users.values():
        socket.sendall(msg)

class TCPServerRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            ip = self.request.getpeername()[0]
            next_data_port = available_ports.popleft()
            self.request.sendall(f"200\n\n{next_data_port}\0".encode("utf-8"))

            # if needed a delay can be added here
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as data_socket:
                data_socket.connect((ip, next_data_port))
                username = ""

                while True:
                    pieces = [b'']
                    total = 0
                    while b'\0' not in pieces[-1] and total < 4096:
                        pieces.append(self.request.recv(128))
                        total += len(pieces[-1])
        
                    data = b''.join(pieces)
                    command = data.decode("utf-8").strip("\0")
                    
                    if command.startswith("login"):
                        username = command.split()[1]
                        if username in active_users:
                            data_socket.sendall(b"500\n\nThe username you entered is already taken.\0")
                            continue
                        
                        active_users[username] = data_socket
                        broadcast(f"200\n\njoin\n{username}\0".encode("utf-8"))
                    elif command.startswith("who"):
                        if not username:
                            data_socket.sendall(b"500\n\nYou must be logged in to use this command.\0")
                            continue

                        data_socket.sendall(f"200\n\nACTIVE USERS\n{"\n".join(user for user in active_users.keys())}\0".encode("utf-8"))
                    elif command.startswith("broadcast"):
                        match = re.search(r"^broadcast (.+)$", command)
                        msg = match.group(1)
                        if not username:
                            data_socket.sendall(b"500\n\nYou must be logged in to use this command.\0")
                            continue

                        broadcast(f"200\n\nBroadcast\n{username}\n{msg}\0".encode("utf-8"))
                    elif command.startswith("private"):
                        if not username:
                            data_socket.sendall(b"500\n\nYou must be logged in to use this command.\0")
                            continue

                        match = re.search(r"^private ([^\s]+) (.+)$", command)
                        user, msg = match.group(1), match.group(2)
                        if user not in active_users:
                            data_socket.sendall(f"500\n\nUser {user} is not an active user.\0".encode("utf-8"))
                            continue

                        active_users[user].sendall(f"200\n\nPrivate\n{username}\n{msg}\0".encode("utf-8"))


    
                available_ports.append(next_data_port)
        except ConnectionError:
            available_ports.appendleft(next_data_port)


if len(sys.argv) < 2:
    print("Please enter the port.")

HOST, PORT = "0.0.0.0", int(sys.argv[1])
with socketserver.ThreadingTCPServer((HOST, PORT), TCPServerRequestHandler) as server:
    server.serve_forever()