# node.py
import sys
import network

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("Servidor: python node.py server <HOST> <PORT>")
        print("Cliente: python node.py client <HOST> <PORT> <FILENAME>")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "server":
        host = sys.argv[2]
        port = int(sys.argv[3])
        network.start_server(host, port)

    elif mode == "client":
        host = sys.argv[2]
        port = int(sys.argv[3])
        filename = sys.argv[4]
        network.connect_to_peer(host, port, filename)

    else:
        print("Modo desconocido. Usa 'server' o 'client'.")
