import socket
import time

# IP-ul și portul serverului
SERVER_IP = '198.7.0.2'
SERVER_PORT = 10000

# Crearea socketului TCP
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind-uim socketul cu adresa IP și portul serverului
server_socket.bind((SERVER_IP, SERVER_PORT))
# server_socket.TCPServer.allow_reuse_address = True # pt debug, nu merge

# Ascultăm conexiuni
server_socket.listen(1)

# Acceptăm o conexiune
client_socket, client_address = server_socket.accept()
print("Connected to:", client_address)

try:
    cnt = 0
    while True:
        # Primim un mesaj de la client
        message = client_socket.recv(1024).decode()
        print("Client:", message)

        # Trimitem un mesaj la client
        response = f"Hello, client! {cnt}"
        cnt += 1
        client_socket.send(response.encode())

        # Așteptăm 1 secundă înainte de a trimite următorul mesaj
        time.sleep(1)
except KeyboardInterrupt:
    client_socket.close()
    server_socket.close()
    
finally:
    # Închidem conexiunea la client
    client_socket.close()

    # Închidem serverul
    server_socket.close()