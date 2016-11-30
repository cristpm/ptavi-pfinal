#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Programa cliente SIP."""

import socket
import sys


METODO = sys.argv[1]
OPCION = sys.argv[2]
PE = sys.argv[3]
#Dirección IP, Puerto del servidor PROXY.
IP = '127.0.0.1'#provicional
PORT_Proxy = 5555#provicional

# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
my_socket.connect((IP, PORT_Proxy))

# Contenido que vamos a enviar
if METODO == 'REGISTER':
    MENSAJE = METODO + ' sip:penny@bigbang.org:' + PE + ' SIP/2.0\r\nExpires: ' + OPCION + '\r\n'    
else:
    MENSAJE = METODO + ' sip:' + OPCION + ' SIP/2.0\r\n'
my_socket.send(bytes(MENSAJE, 'utf-8') + b'\r\n')
print('Enviando -- ')
print(MENSAJE)

# Contenido que recibimos de respuesta
data = my_socket.recv(1024)
respuesta = data.decode('utf-8')
print('Recibido -- ')
print(respuesta)
num_respuesta = respuesta.split(' ')[1]
print(num_respuesta)
if METODO == 'INVITE' and num_respuesta != '404':
    MENSAJE = 'ACK sip:' + OPCION + ' SIP/2.0\r\n'
    my_socket.send(bytes(MENSAJE, 'utf-8') + b'\r\n')
    print('Enviando -- ')
    print(MENSAJE)
my_socket.close()
