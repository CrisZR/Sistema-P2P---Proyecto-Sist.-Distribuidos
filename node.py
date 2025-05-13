# node.py
import sys
import threading
import network

def start_node(host, port, peer_hosts=None, filename=None):
    # Iniciar el servidor en un hilo
    server_thread = threading.Thread(target=network.start_server, args=(host, port), daemon=True)
    server_thread.start()

    # Si se proporcionaron peers y un archivo, actuar también como cliente
    if peer_hosts and filename:
        network.connect_to_peer_multiple(peer_hosts, port, filename)
    else:
        print("[*] Nodo funcionando solo como servidor. Esperando conexiones...")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso:")
        print("Nodo servidor solamente:")
        print("  python node.py <HOST> <PORT>")
        print("Nodo cliente y servidor:")
        print("  python node.py <HOST> <PORT> <PEER1> <PEER2> ... <FILENAME>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])

    if len(sys.argv) > 4:
        peers = sys.argv[3:-1]
        filename = sys.argv[-1]
    else:
        peers = None
        filename = None

    start_node(host, port, peers, filename)
