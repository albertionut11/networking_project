import socket
import time

# IP-ul și portul serverului
SERVER_IP = '198.7.0.2'
SERVER_PORT = 10000

# Crearea socketului TCP
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Conectarea la server
client_socket.connect((SERVER_IP, SERVER_PORT))

try:
    cnt = 0
    while True:
        # Trimitem un mesaj la server
        message = f"Hello, server! {cnt}"
        cnt += 1
        client_socket.send(message.encode())

        # Primim un mesaj de la server
        response = client_socket.recv(1024).decode()
        print("Server:", response)

        # Așteptăm 1 secundă înainte de a trimite următorul mesaj
        time.sleep(1)
except KeyboardInterrupt:
    client_socket.close()
    
finally:
    # Închidem conexiunea la server
    client_socket.close()