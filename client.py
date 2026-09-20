import socket
import threading

print("Starting client...")

current_command = ""
username = ""
quit_response = threading.Event()


def receive_message(connection):
    message = b""
    while True:
        character = connection.recv(1)
        if not character:
            return None
        if character == b"\0":
            return message.decode("utf-8")
        message += character


def listen_for_messages(data_connection):
    global current_command

    while True:
        response = receive_message(data_connection)
        if response is None:
            quit_response.set()
            break
        status_code, _, data = response.partition("\n\n")
        status_code = status_code.strip()
        parts = data.splitlines()

        if status_code == "500":
            print(f"{status_code} status code received.")
            if data:
                print(data)
            failed_command = current_command
            current_command = ""
            if failed_command == "quit":
                quit_response.set()
            continue

        # Login response
        if current_command == "login" and not parts:
            print(f"{status_code} status code received. Login successful")
            current_command = ""

        # Private message confirmation
        elif current_command == "private" and not parts:
            print(f"{status_code} status code received. Message sent.")
            current_command = ""

        # Quit confirmation
        elif current_command == "quit" and not parts:
            print(f"{status_code} status code received.")
            quit_response.set()
            break

        # Private message
        elif parts and parts[0] == "Private":
            sender = parts[1]
            message = "\n".join(parts[2:])
            print(f"{status_code} status code received.")
            print(f"{sender}: {message}")

        # Broadcast message
        elif parts and parts[0] == "Broadcast":
            sender = parts[1]
            message = "\n".join(parts[2:])

            print(f"{status_code} status code received.")
            print(f"Broadcast message from {sender}: {message}")

        # Join notification
        elif parts and parts[0] == "join":
            if current_command == "login" and parts[1] == username:
                print(f"{status_code} status code received. Login successful")
                current_command = ""

        # Who response
        elif current_command == "who":
            if parts and parts[0] == "ACTIVE USERS":
                parts = parts[1:]
            users = ", ".join(parts)

            print(
                f"{status_code} status code received. "
                f"Users currently connected: {users}"
            )

            current_command = ""


while True:
    command = input()
    parts = command.split()

    if parts[0] == "connect":
        server_ip = parts[1]
        server_port = int(parts[2])

        control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        control_socket.connect((server_ip, server_port))

        response = receive_message(control_socket)
        if response is None:
            control_socket.close()
            continue
        response_parts = response.split()

        status_code = response_parts[0]
        if status_code != "200":
            print(f"{status_code} status code received.")
            control_socket.close()
            continue
        data_port = int(response_parts[1])

        print(
            f"{status_code} status code received. "
            f"Starting data connection on port {data_port}"
        )

        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_socket.bind(("", data_port))
        data_socket.listen(1)

        data_connection, address = data_socket.accept()
        data_socket.close()

        listener = threading.Thread(
            target=listen_for_messages,
            args=(data_connection,)
        )
        listener.daemon = True
        listener.start()

    elif parts[0] == "login":
        username = parts[1]
        current_command = "login"
        control_socket.sendall((command + "\0").encode("utf-8"))

    elif parts[0] == "who":
        current_command = "who"
        control_socket.sendall((command + "\0").encode("utf-8"))

    elif parts[0] == "broadcast":
        control_socket.sendall((command + "\0").encode("utf-8"))

    elif parts[0] == "private":
        current_command = "private"
        control_socket.sendall((command + "\0").encode("utf-8"))

    elif parts[0] == "quit":
        quit_response.clear()
        current_command = "quit"
        control_socket.sendall((command + "\0").encode("utf-8"))
        quit_response.wait()
        if current_command != "quit":
            continue
        data_connection.close()
        control_socket.close()
        break

