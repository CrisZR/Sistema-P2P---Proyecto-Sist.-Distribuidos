# node.py
import sys
import network

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso:")
        print("Servidor: python node.py server <HOST> <PORT>")
        print("Cliente: python node.py client <HOST1> <HOST2> <PORT> <FILENAME>")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "server":
        host = sys.argv[2]
        port = int(sys.argv[3])
        network.start_server(host, port)

    elif mode == "client":
        hosts = sys.argv[2:-2]  # Los primeros argumentos son los hosts de los nodos
        port = int(sys.argv[-2])  # El penúltimo argumento es el puerto
        filename = sys.argv[-1]  # El último argumento es el nombre del archivo
        network.connect_to_peer_multiple(hosts, port, filename)

    else:
        print("Modo desconocido. Usa 'server' o 'client'.")
