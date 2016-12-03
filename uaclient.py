#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Programa cliente SIP."""

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import uaserver
import socket
import sys



if __name__ == "__main__":
    """
    Programa principal
    """
    parser = make_parser()
    cHandler = uaserver.XMLHandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(sys.argv[1]))
    miXML = cHandler.get_tags()
    METODO = sys.argv[2]
    OPCION = sys.argv[3]# Direccion sip o tiempo de expiracion
    
    #Puerto de escucha del UA server IP?????
    PE = miXML['uaserver']['puerto']
    
    #Dirección IP, Puerto del servidor PROXY.
    IP = miXML['regproxy']['ip']
    PORT_Proxy = int(miXML['regproxy']['puerto'])

    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto PROXY
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((IP, PORT_Proxy))

    # Contenido que vamos a enviar
    if METODO == 'REGISTER':
        MENSAJE = METODO + ' ' + miXML['acount']['username'] + PE + ' SIP/2.0\r\nExpires: ' + OPCION + '\r\n'    
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
    if METODO == 'INVITE' and num_respuesta != '404':
        MENSAJE = 'ACK sip:' + OPCION + ' SIP/2.0\r\n'
        my_socket.send(bytes(MENSAJE, 'utf-8') + b'\r\n')
        print('Enviando -- ')
        print(MENSAJE)
    my_socket.close()
