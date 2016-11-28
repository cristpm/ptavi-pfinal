#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Programa cliente SIP."""

import socket
import sys


METODO = sys.argv[1]
RECEPTOR = sys.argv[2].split('@')
# Login, Dirección IP, Puerto del servidor.
LOGIN = RECEPTOR[0]
IP = RECEPTOR[1].split(':')[0]
PORT = int(RECEPTOR[1].split(':')[-1])

# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
my_socket.connect((IP, PORT))

# Contenido que vamos a enviar
MENSAJE = METODO + ' sip:' + LOGIN + '@' + IP + ' SIP/2.0\r\n'
my_socket.send(bytes(MENSAJE, 'utf-8') + b'\r\n')
print('Enviando -- ')
print(MENSAJE)

# Contenido que recibimos de respuesta
data = my_socket.recv(1024)
print('Recibido -- ')
print(data.decode('utf-8'))

if METODO == 'INVITE':
    MENSAJE = 'ACK sip:' + LOGIN + '@' + IP + ' SIP/2.0\r\n'
    my_socket.send(bytes(MENSAJE, 'utf-8') + b'\r\n')
    print('Enviando -- ')
    print(MENSAJE)
my_socket.close()
