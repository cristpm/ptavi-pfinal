#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Programa cliente SIP."""

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from threading import Thread
from uaserver import Envio_RTP
from uaserver import Escucha_VLC
from uaserver import Writer_toLOG
import uaserver
import socket
import hashlib
import time
import sys
import os


if __name__ == "__main__":
    """
    Programa principal
    """
    try:
        parser = make_parser()
        cHandler = uaserver.XML_UA()
        parser.setContentHandler(cHandler)
        parser.parse(open(sys.argv[1]))
        miXML = cHandler.get_tags()
        METODO = sys.argv[2]
        OPCION = sys.argv[3]
        Path_Log = miXML['log']['path']
        Writer_toLOG(Path_Log, 'Starting....')
    except IndexError:
        sys.exit("Usage: python uaclient.py config method option")

    Sip = miXML['acount']['username']
    IP_Proxy = miXML['regproxy']['ip']
    PORT_Proxy = miXML['regproxy']['puerto']

    #  Creamos socket, lo configuramos y lo atamos al Servidor REGISTER/PROXY
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((IP_Proxy, int(PORT_Proxy)))

    if METODO == 'REGISTER':
        MENSAJE = METODO + ' sip:' + Sip + ':' + PE + \
            ' SIP/2.0\r\nExpires: ' + OPCION + '\r\n'
    else:
        MENSAJE = METODO + ' sip:' + OPCION + ' SIP/2.0\r\n'
        if METODO == 'INVITE':
            O = 'o=' + Sip + ' ' + IP + '\r\n'
            P = miXML['rtpaudio']['puerto']
            SDP = 'v=0\r\n' + O + 's=misesion\r\nt=0\r\nm=audio ' + P + ' RTP'
            MENSAJE = MENSAJE + 'Content-Type: application/sdp\r\n\r\n' + SDP
        if METODO == 'BYE':
            os.system('killall mp32rtp 2> /dev/null')
            os.system('killall vlc 2> /dev/null')
    Writer_toLOG(Path_Log, 'Send to ' + IP_Proxy + ':' + PORT_Proxy + ': ' +
                 MENSAJE)
    my_socket.send(bytes(MENSAJE, 'utf-8') + b'\r\n')
    print('Enviando ------------------------ ')
    print(MENSAJE)

    #  Contenido que recibimos de respuesta
    try:
        data = my_socket.recv(1024)
        respuesta = data.decode('utf-8')
        Writer_toLOG(Path_Log, 'Received to ' + IP_Proxy + ':' + PORT_Proxy +
                     ': ' + respuesta)
        print('Recibido ------------------------ ')
        print(respuesta)
        if METODO == 'REGISTER' and respuesta.split(' ')[1] == '401':
            nonce = respuesta.split('"')[-2]
            r = hashlib.md5()
            r.update(bytes(miXML['acount']['passwd'], 'utf-8'))
            r.update(bytes(nonce, 'utf-8'))
            resp = r.hexdigest()
            MENSAJE = MENSAJE + 'Authorization: Digest response="' + resp + '"'
            Writer_toLOG(Path_Log, 'Send to ' + IP_Proxy + ':' + PORT_Proxy +
                         ': ' + MENSAJE)
            my_socket.send(bytes(MENSAJE, 'utf-8') + b'\r\n\r\n')
            print('Enviando ------------------------ ')
            print(MENSAJE)
            data = my_socket.recv(1024)
            Writer_toLOG(Path_Log, 'Received to ' + IP_Proxy + ':' +
                         PORT_Proxy + ': ' + data.decode('utf-8'))
            print('Recibido ------------------------ ')
            print(data.decode('utf-8'))
        if METODO == 'INVITE' and respuesta.split(' ')[1] != '404':
            MENSAJE = 'ACK sip:' + OPCION + ' SIP/2.0\r\n'
            Writer_toLOG(Path_Log, 'Send to ' + IP_Proxy + ':' + PORT_Proxy +
                         ': ' + MENSAJE)
            my_socket.send(bytes(MENSAJE, 'utf-8') + b'\r\n')
            print('Enviando ------------------------ ')
            print(MENSAJE)
            #  ENVIO RTP sacar ip y puerto RTP del sdp que llega en el 200 ok
            IP_RTP = respuesta.split(' ')[-3][0:9]
            P_RTP = respuesta.split(' ')[-2]
            #  Enviamo RTP a la ip y puerto sacados del sdp EL MEDIO INDICADO
            Medio = miXML['audio']['path']
            thread1 = Thread(target=Envio_RTP, args=(IP_RTP, P_RTP, Medio, ))
            #  Escucha del medio por VLC
            thread2 = Thread(target=Escucha_VLC, args=(IP_RTP, P_RTP, ))
            #  Iniciamos hilos
            Writer_toLOG(Path_Log, "Vamos a ejecutar RTP Dirigido a" +
                         IP_RTP + ':' + P_RTP)
            thread1.start()
            Writer_toLOG(Path_Log, "Envio Satisfactorio")
            time.sleep(0.15)
            thread2.start()
        my_socket.close()
        Writer_toLOG(Path_Log, 'Finishing...')
    except ConnectionRefusedError:
        Writer_toLOG(Path_Log, 'Conexion con el PROXY/REGISTER fallido')
        sys.exit("Conexion con el PROXY/REGISTER fallido")
