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
def connect_to_peer_multiple(hosts, port, filename):
    # Lista de hilos para conexiones simultáneas
    threads = []
    
    # Conectarse a cada nodo y descargar fragmento en un hilo separado
    for host in hosts:
        thread = threading.Thread(target=connect_to_peer, args=(host, port, filename))
        threads.append(thread)
        thread.start()

    # Esperar a que todos los hilos terminen
    for thread in threads:
        thread.join()

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
    num_chunks = (filesize // BUFFER_SIZE) + 1  # Número de fragmentos

    # Enviar el nombre del archivo y la cantidad de fragmentos
    conn.send(f"{os.path.basename(filepath)}{SEPARATOR}{num_chunks}".encode())

    with open(filepath, "rb") as f:
        for _ in range(num_chunks):
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

    file_name, num_chunks = received.split(SEPARATOR)
    num_chunks = int(num_chunks)

    os.makedirs("files", exist_ok=True)  # Asegura que la carpeta files existe

    with open(f"files/{filename}", "wb") as f:
        total_received = 0
        while total_received < num_chunks * BUFFER_SIZE:
            bytes_read = conn.recv(BUFFER_SIZE)
            if not bytes_read:
                break
            f.write(bytes_read)
            total_received += len(bytes_read)

    # Verificar la integridad del archivo
    received_hash = calculate_hash(f"files/{filename}")
    print(f"Verificando integridad del archivo {filename}... ({received_hash})")

# ===== Calcular hash =====
def calculate_hash(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()
