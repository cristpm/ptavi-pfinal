#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Programa cliente SIP."""

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import uaserver
import socket
import sys
import hashlib
import os

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
        
    Sip = miXML['acount']['username']
    IP = miXML['uaserver']['ip']
    PE = miXML['uaserver']['puerto']
    IP_Proxy = miXML['regproxy']['ip']
    PORT_Proxy = int(miXML['regproxy']['puerto'])
    
    # Creamos el socket, lo configuramos y lo atamos al Servidor REGISTER/PROXY
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((IP_Proxy, PORT_Proxy))

    if METODO == 'REGISTER':
        MENSAJE = METODO + ' sip:' + Sip + ':' + PE + ' SIP/2.0\r\nExpires: ' + OPCION + '\r\n'
    else:
        MENSAJE = METODO + ' sip:' + OPCION + ' SIP/2.0\r\n'
        if METODO == 'INVITE':
            O = '0=' + Sip + ' ' + IP + '\r\n'
            P = miXML['rtpaudio']['puerto']
            SDP = 'v=0\r\n' + O + 's=misesion\r\nt=0\r\nm=audio ' + P + ' RTP'
            MENSAJE = MENSAJE + 'Content-Type: application/sdp\r\n\r\n' + SDP
    my_socket.send(bytes(MENSAJE, 'utf-8') + b'\r\n')
    print('Enviando ------------------------ ')
    print(MENSAJE)

    # Contenido que recibimos de respuesta
    try:
        data = my_socket.recv(1024)
        respuesta = data.decode('utf-8')
        print('Recibido ------------------------ ')
        print(respuesta)
        num_respuesta = respuesta.split(' ')[1]
        if METODO == 'REGISTER' and num_respuesta == '401':
            nonce = respuesta.split('"')[-2]
            r = hashlib.md5()
            r.update(bytes(miXML['acount']['passwd'], 'utf-8'))
            r.update(bytes(nonce, 'utf-8'))
            resp = r.hexdigest()
            MENSAJE = MENSAJE + 'Authorization: Digest response="' + resp + '"'
            my_socket.send(bytes(MENSAJE, 'utf-8') + b'\r\n')
            print('Enviando ------------------------ ')
            print(MENSAJE)
            data = my_socket.recv(1024)
            print('Recibido ------------------------ ')
            print(data.decode('utf-8'))
            my_socket.close()
        if METODO == 'INVITE' and num_respuesta != '404':
            MENSAJE = 'ACK sip:' + OPCION + ' SIP/2.0\r\n'
            my_socket.send(bytes(MENSAJE, 'utf-8') + b'\r\n')
            print('Enviando ------------------------ ')
            print(MENSAJE)
            #ENVIO RTP sacar ip y puerto RTP del sdp que llega en el 200 ok
            IP_RTP = respuesta.split(' ')[-3][0:9]
            Puerto_RTP = respuesta.split(' ')[-2]
            aEjecutar = 'mp32rtp -i ' + IP_RTP + ' -p ' + Puerto_RTP + ' < ' 
            + miXML['audio']['path']
            print("Vamos a ejecutar RTP")# aEjecutar)
            # os.system(aEjecutar)
            # print("Envio Satisfactorio")
        my_socket.close()
    except ConnectionRefusedError:
        sys.exit("Intento de conexion fallido")
