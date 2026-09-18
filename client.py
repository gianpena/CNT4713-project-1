import socket
print("Starting client...")
command = input()
parts = command.split()
if parts[0] == "connect":
    server_ip = parts[1]
    server_port = int(parts[2])
    control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    control_socket.connect((server_ip, server_port))
    response = control_socket.recv(1024).decode("utf-8")
    response_parts = response.split()
    status_code = response_parts[0]
    data_port = int(response_parts[1].strip("\0"))
    print(f"Status: {status_code}\nData code: {data_port}")
    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.bind(("", data_port))
    data_socket.listen(1)
    data_connection, address = data_socket.accept()



