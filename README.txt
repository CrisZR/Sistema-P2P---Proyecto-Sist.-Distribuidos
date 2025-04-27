# Sistema P2P de Compartición de Archivos

Este proyecto es un sistema distribuido básico de compartición de archivos utilizando una arquitectura **Peer-to-Peer (P2P)** con **sockets en Python**.

Cada nodo puede actuar como **servidor** (ofrecer archivos) o como **cliente** (solicitar archivos).

---

## 📦 Estructura del proyecto
p2p_project/
├── node.py             # Ejecuta el nodo (modo servidor o cliente)
├── network.py          # Lógica de conexión y transferencia de archivos
├── files/              # Carpeta para archivos locales
└── README.md           # Este archivo



Requisitos
Python 3.x

Estar en la misma red local (Wi-Fi o LAN) o tener configurado el acceso público (Internet + port forwarding).


Comandos para correr el servidor (En Terminal):
python node.py server <IP_LOCAL> <PUERTO>
(Ejemplo: "python node.py server 192.168.1.5 5001")


Comandos para conexion del cliente (Terminal):
python node.py client <IP_SERVIDOR> <PUERTO> <NOMBRE_DEL_ARCHIVO>
(Ejemplo: "python node.py client 192.168.1.5 5001 test.txt")


Para obtenr IP de Maquina-Servidor (CMD):
ipconfig



