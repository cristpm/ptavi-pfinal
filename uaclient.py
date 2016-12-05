#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Programa cliente SIP."""

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import uaserver
import socket
import sys
import hashlib


if __name__ == "__main__":
    """
    Programa principal
    """
    try:
        parser = make_parser()
        cHandler = uaserver.XMLHandler()
        parser.setContentHandler(cHandler)
        parser.parse(open(sys.argv[1]))
        miXML = cHandler.get_tags()
        METODO = sys.argv[2]
        OPCION = sys.argv[3]# Direccion sip del receptor o tiempo de expiracion
    except IndexError:
        sys.exit("Usage: python uaclient.py config method option")
    
    #Direccion SIP del UA 
    Sip_E = miXML['acount']['username']
    
    #Puerto de escucha del UA server IP?????
    IP = miXML['uaserver']['ip']
    PE = miXML['uaserver']['puerto']
    
    #Dirección IP y Puerto del servidor PROXY.
    IP_Proxy = miXML['regproxy']['ip']
    PORT_Proxy = int(miXML['regproxy']['puerto'])

    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto PROXY
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((IP_Proxy, PORT_Proxy))

    # Contenido que vamos a enviar
    if METODO == 'REGISTER':
        MENSAJE = METODO + ' sip:' + Sip_E + ':' + PE + ' SIP/2.0\r\nExpires: ' + OPCION + '\r\n'
    else:
        MENSAJE = METODO + ' sip:' + OPCION + ' SIP/2.0\r\n'
        if METODO == 'INVITE':
            O = '0=' + Sip_E + ' ' + IP + '\r\n'
            P_RTP = miXML['rtpaudio']['puerto']
            SDP = 'v=0\r\n' + O + 's=misesion\r\nt=0\r\nm=audio' + P_RTP + 'RTP'
            MENSAJE = MENSAJE + 'Content-Type: application/sdp\r\n\r\n' + SDP
    my_socket.send(bytes(MENSAJE, 'utf-8') + b'\r\n')
    print('Enviando -- ')
    print(MENSAJE)

    # Contenido que recibimos de respuesta
    try:
        data = my_socket.recv(1024)
        respuesta = data.decode('utf-8')
        print('Recibido -- ')
        print(respuesta)
        num_respuesta = respuesta.split(' ')[1]
        if METODO == 'REGISTER' and num_respuesta == '401':
            nonce = respuesta.split('"')[-2]
            r = hashlib.md5()
            r.update(b'superman') # contraseña provicional
            r.update(bytes(nonce, 'utf-8'))
            response = r.hexdigest()
            print(response)
            MENSAJE = MENSAJE + 'Authorization: Digest response="' + response + '"'
            my_socket.send(bytes(MENSAJE, 'utf-8') + b'\r\n')
            print('Enviando -- ')
            print(MENSAJE)
            data = my_socket.recv(1024)
            respuesta = data.decode('utf-8')
            print('Recibido -- ')
            print(respuesta)
        if METODO == 'INVITE' and num_respuesta != '404':
            MENSAJE = 'ACK sip:' + OPCION + ' SIP/2.0\r\n'
            my_socket.send(bytes(MENSAJE, 'utf-8') + b'\r\n')
            print('Enviando -- ')
            print(MENSAJE)
        my_socket.close()
    except ConnectionRefusedError:
        sys.exit("Intento de conexion fallido")
