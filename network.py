import socket
import threading
import os
import hashlib

FRAGMENT_SIZE = 1024 * 64  # 64 KB por fragmento
FILES_DIR = os.path.join(os.path.dirname(__file__), "Files")
PEERS = {("127.0.0.1", 5000), ("127.0.0.1", 5001), ("127.0.0.1", 5002)}

def calcular_hash(data):
    return hashlib.sha256(data).hexdigest()

def indexar_archivos():
    if not os.path.exists(FILES_DIR):
        os.makedirs(FILES_DIR)
    archivos = [f for f in os.listdir(FILES_DIR) if os.path.isfile(os.path.join(FILES_DIR, f)) and not f.startswith("descargado_")]
    print("Archivos disponibles para compartir:")
    for archivo in archivos:
        print(f" - {archivo}")
    return archivos

def fragmentos_disponibles(filename):
    """Devuelve los índices de fragmentos disponibles localmente para un archivo."""
    filepath = os.path.join(FILES_DIR, filename)
    if not os.path.exists(filepath):
        return []
    filesize = os.path.getsize(filepath)
    num_fragments = (filesize + FRAGMENT_SIZE - 1) // FRAGMENT_SIZE
    return list(range(num_fragments))

def handle_client(conn, addr):
    print(f"Conexión desde {addr}")
    data = conn.recv(1024).decode()
    if data.startswith("INDEX"):
        archivos = indexar_archivos()
        conn.sendall(("\n".join(archivos)).encode())
    elif data.startswith("FRAGMENTS "):
        filename = data[10:].strip()
        indices = fragmentos_disponibles(filename)
        conn.sendall((",".join(map(str, indices))).encode())
    elif data.startswith("GETFRAG "):
        parts = data[8:].strip().split()
        filename = parts[0]
        frag_idx = int(parts[1])
        filepath = os.path.join(FILES_DIR, filename)
        try:
            with open(filepath, "rb") as f:
                f.seek(frag_idx * FRAGMENT_SIZE)
                fragment = f.read(FRAGMENT_SIZE)
                hash_fragment = calcular_hash(fragment).encode()
                conn.sendall(hash_fragment.ljust(64, b' '))
                conn.sendall(fragment)
            print(f"Fragmento {frag_idx} de '{filename}' enviado a {addr}")
        except Exception:
            conn.sendall(b"ERR")
    conn.close()

def server(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("0.0.0.0", port))
    s.listen()
    print(f"Servidor escuchando en el puerto {port}")
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

def obtener_fragmentos_peers(filename):
    """Consulta a todos los peers qué fragmentos tienen de un archivo."""
    fragment_map = {}
    for peer_ip, peer_port in PEERS:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect((peer_ip, peer_port))
            s.sendall(f"FRAGMENTS {filename}".encode())
            data = s.recv(4096).decode()
            indices = [int(idx) for idx in data.split(",") if idx.strip().isdigit()]
            for idx in indices:
                fragment_map.setdefault(idx, []).append((peer_ip, peer_port))
            s.close()
        except Exception:
            continue
    return fragment_map

def descargar_fragmento(filename, frag_idx, peer_ip, peer_port):
    """Descarga un fragmento específico de un peer."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((peer_ip, peer_port))
        s.sendall(f"GETFRAG {filename} {frag_idx}".encode())
        hash_fragment = s.recv(64).decode().strip()
        fragment = b''
        bytes_leidos = 0
        while bytes_leidos < FRAGMENT_SIZE:
            chunk = s.recv(min(FRAGMENT_SIZE - bytes_leidos, 4096))
            if not chunk:
                break
            fragment += chunk
            bytes_leidos += len(chunk)
            if len(chunk) < 4096:
                break
        s.close()
        if calcular_hash(fragment) != hash_fragment:
            print(f"Fragmento {frag_idx} corrupto desde {peer_ip}:{peer_port}")
            return None
        return fragment
    except Exception as e:
        print(f"Error descargando fragmento {frag_idx} de {peer_ip}:{peer_port}: {e}")
        return None

def client_multi_peer(filename):
    fragment_map = obtener_fragmentos_peers(filename)
    if not fragment_map:
        print("Archivo no encontrado en ningún peer.")
        return
    num_fragments = max(fragment_map.keys()) + 1
    print(f"Fragmentos encontrados: {sorted(fragment_map.keys())}")
    if not os.path.exists(FILES_DIR):
        os.makedirs(FILES_DIR)
    fragments = [None] * num_fragments
    for idx in range(num_fragments):
        if idx not in fragment_map:
            print(f"Fragmento {idx} no disponible en ningún peer.")
            return
        for peer in fragment_map[idx]:
            fragment = descargar_fragmento(filename, idx, *peer)
            if fragment:
                fragments[idx] = fragment
                # Replicación: guardar fragmento localmente
                with open(os.path.join(FILES_DIR, f"descargado_{filename}"), "r+b" if os.path.exists(os.path.join(FILES_DIR, f"descargado_{filename}")) else "wb") as f:
                    f.seek(idx * FRAGMENT_SIZE)
                    f.write(fragment)
                break
        if fragments[idx] is None:
            print(f"No se pudo descargar el fragmento {idx}")
            return
    print(f"Archivo {filename} descargado y ensamblado correctamente.")
    # Replicación: renombrar archivo para compartirlo
    os.rename(os.path.join(FILES_DIR, f"descargado_{filename}"), os.path.join(FILES_DIR, filename))
    print(f"Archivo replicado localmente como '{filename}'.")

def busqueda_distribuida(nombre_parcial):
    """Busca archivos que contengan 'nombre_parcial' en todos los peers."""
    resultados = {}
    for peer_ip, peer_port in PEERS:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect((peer_ip, peer_port))
            s.sendall("INDEX".encode())
            data = s.recv(4096).decode()
            archivos = [a.strip() for a in data.split("\n") if nombre_parcial in a]
            for archivo in archivos:
                resultados.setdefault(archivo, []).append(f"{peer_ip}:{peer_port}")
            s.close()
        except Exception:
            continue
    if resultados:
        print("Resultados de búsqueda distribuida:")
        for archivo, peers in resultados.items():
            print(f"  {archivo} -> {', '.join(peers)}")
    else:
        print("No se encontraron archivos que coincidan en la red.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python network.py server <puerto>")
        print("  python network.py client <archivo>")
        print("  python network.py search <nombre_parcial>")
        sys.exit(1)
    if sys.argv[1] == "server":
        if len(sys.argv) != 3:
            print("Uso: python network.py server <puerto>")
            sys.exit(1)
        indexar_archivos()
        server(int(sys.argv[2]))
    elif sys.argv[1] == "client":
        if len(sys.argv) != 3:
            print("Uso: python network.py client <archivo>")
            sys.exit(1)
        client_multi_peer(sys.argv[2])
    elif sys.argv[1] == "search":
        if len(sys.argv) != 3:
            print("Uso: python network.py search <nombre_parcial>")
            sys.exit(1)
        busqueda_distribuida(sys.argv[2])