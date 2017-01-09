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
        cHandler = uaserver.XML_UA()
        parser.setContentHandler(cHandler)
        parser.parse(open(sys.argv[1]))
        miXML = cHandler.get_tags()
        METODO = sys.argv[2]
        OPCION = sys.argv[3]
        Path_Log = miXML['log']['path'] 
        miLOG = uaserver.LOGHandler()
        miLOG.Writer(Path_Log, 'Starting....')
    except IndexError:
        sys.exit("Usage: python uaclient.py config method option")
    
    Sip = miXML['acount']['username']
    IP = miXML['uaserver']['ip']# IP de la parte UAS del UA
    PE = miXML['uaserver']['puerto']# Puerto de escucha de la parte UAS del UA
    IP_Proxy = miXML['regproxy']['ip']
    PORT_Proxy = miXML['regproxy']['puerto']
    
    # Creamos el socket, lo configuramos y lo atamos al Servidor REGISTER/PROXY
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((IP_Proxy, int(PORT_Proxy)))

    if METODO == 'REGISTER':
        MENSAJE = METODO + ' sip:' + Sip + ':' + PE + \
        ' SIP/2.0\r\nExpires: '  +  OPCION + '\r\n'
    else:
        MENSAJE = METODO + ' sip:' + OPCION + ' SIP/2.0\r\n'
        if METODO == 'INVITE':
            O = 'o=' + Sip + ' ' + IP + '\r\n'
            P = miXML['rtpaudio']['puerto']
            SDP = 'v=0\r\n' + O + 's=misesion\r\nt=0\r\nm=audio ' + P + ' RTP'
            MENSAJE = MENSAJE + 'Content-Type: application/sdp\r\n\r\n' + SDP
    miLOG.Writer(Path_Log, 'Send to ' + IP_Proxy + ':' + PORT_Proxy + \
    ': ' + MENSAJE )
    my_socket.send(bytes(MENSAJE, 'utf-8') + b'\r\n')
    print('Enviando ------------------------ ')
    print(MENSAJE)

    # Contenido que recibimos de respuesta
    try:
        data = my_socket.recv(1024)
        respuesta = data.decode('utf-8')
        miLOG.Writer(Path_Log, 'Received to ' + IP_Proxy + ':' + PORT_Proxy + \
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
            miLOG.Writer(Path_Log, 'Send to ' + IP_Proxy + ':' + PORT_Proxy + \
            ': ' + MENSAJE )
            my_socket.send(bytes(MENSAJE, 'utf-8') + b'\r\n\r\n')
            print('Enviando ------------------------ ')
            print(MENSAJE)
            data = my_socket.recv(1024)
            miLOG.Writer(Path_Log, 'Received to ' + IP_Proxy + ':' + \
            PORT_Proxy + ': ' + data.decode('utf-8') )
            print('Recibido ------------------------ ')
            print(data.decode('utf-8'))
        if METODO == 'INVITE' and respuesta.split(' ')[1] != '404':
            MENSAJE = 'ACK sip:' + OPCION + ' SIP/2.0\r\n'
            miLOG.Writer(Path_Log, 'Send to ' +IP_Proxy + ':' + PORT_Proxy + \
            ': ' + MENSAJE )
            my_socket.send(bytes(MENSAJE, 'utf-8') + b'\r\n')
            print('Enviando ------------------------ ')
            print(MENSAJE)
            #ENVIO RTP sacar ip y puerto RTP del sdp que llega en el 200 ok
            IP_RTP = respuesta.split(' ')[-3][0:9]
            Puerto_RTP = respuesta.split(' ')[-2]
            aEjecutar = './mp32rtp -i ' + IP_RTP + ' -p ' + Puerto_RTP + \
            ' < ' + miXML['audio']['path']
            print("Vamos a ejecutar RTP", aEjecutar)
            miLOG.Writer(Path_Log, aEjecutar)
            os.system(aEjecutar)
            print("Envio Satisfactorio")
            VLC = 'cvlc rtp://@' + IP + ':' + miXML['rtpaudio']['puerto']
            #os.system(VLC)
        my_socket.close()
        miLOG.Writer(Path_Log, 'Finishing...' )
    except ConnectionRefusedError:
        miLOG.Writer(Path_Log, 'Conexion con el PROXY/REGISTER fallido' )
        sys.exit("Conexion con el PROXY/REGISTER fallido")
