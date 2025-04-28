import socket
import threading
import os
import hashlib

BUFFER_SIZE = 4096  # Tamaño de cada paquete que enviamos
SEPARATOR = "<SEPARATOR>"  # Separador para enviar metadata

# ===== Servidor =====
def start_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"[+] Servidor escuchando en {host}:{port}...")

    while True:
        client_socket, address = server_socket.accept()
        print(f"[+] Conexión aceptada de {address}")
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.start()

def handle_client(client_socket):
    received = client_socket.recv(BUFFER_SIZE).decode()

    if received.startswith("SEARCH"):
        _, filename = received.split(SEPARATOR)
        filename = filename.strip()
        if os.path.exists(f"files/{filename}"):
            client_socket.send("FOUND".encode())
        else:
            client_socket.send("NOT_FOUND".encode())
    
    else:
        filename = received.strip()
        print(f"[+] Cliente pidió el archivo: {filename}")

        if os.path.exists(f"files/{filename}"):
            send_file(client_socket, f"files/{filename}")
        else:
            client_socket.send(f"ERROR: Archivo {filename} no encontrado".encode())

    client_socket.close()

# ===== Cliente =====
def connect_to_peer(host, port, filename):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    print(f"[+] Conectado a {host}:{port}")

    # Enviar nombre del archivo que queremos
    client_socket.send(filename.encode())

    # Recibir archivo
    receive_file(client_socket, filename)
    client_socket.close()

# ===== Búsqueda de archivo =====
def search_file(host, port, filename):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    client_socket.send(f"SEARCH{SEPARATOR}{filename}".encode())
    response = client_socket.recv(BUFFER_SIZE).decode()
    client_socket.close()
    return response == "FOUND"

# ===== Enviar archivo =====
def send_file(conn, filepath):
    filesize = os.path.getsize(filepath)
    # Calcular el hash del archivo
    file_hash = calculate_hash(filepath)
    
    conn.send(f"{os.path.basename(filepath)}{SEPARATOR}{filesize}{SEPARATOR}{file_hash}".encode())

    with open(filepath, "rb") as f:
        while True:
            bytes_read = f.read(BUFFER_SIZE)
            if not bytes_read:
                break
            conn.sendall(bytes_read)

# ===== Recibir archivo =====
def receive_file(conn, filename):
    received = conn.recv(BUFFER_SIZE).decode()
    if received.startswith("ERROR"):
        print(received)
        return

    file_name, file_size, file_hash = received.split(SEPARATOR)
    file_size = int(file_size)

    os.makedirs("files", exist_ok=True)  # Asegura que la carpeta files existe

    with open(f"files/{filename}", "wb") as f:
        total_received = 0
        while total_received < file_size:
            bytes_read = conn.recv(BUFFER_SIZE)
            if not bytes_read:
                break
            f.write(bytes_read)
            total_received += len(bytes_read)

    # Verificar la integridad del archivo
    received_hash = calculate_hash(f"files/{filename}")
    if received_hash == file_hash:
        print(f"[+] Archivo {filename} recibido exitosamente y la integridad está verificada!")
    else:
        print(f"[-] Error: La integridad del archivo {filename} no se ha verificado correctamente!")

# ===== Calcular hash =====
def calculate_hash(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()
