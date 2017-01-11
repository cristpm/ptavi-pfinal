#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Clase (y programa principal) para un servidor SIP."""

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from threading import Thread
import socketserver
import sys
import os
import time


def Writer_toLOG(f, mensaje):
    """Escribir en el fichero log."""
    gmt = time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time())) + ' '
    M = mensaje.split('\r\n')
    S = ' '.join(M)
    outfile = open(f, 'a')
    outfile.write(gmt + S + '\n')
    outfile.close()


def Envio_RTP(ip, puerto, medio):
    """Metodo para enviar RTP."""
    aEjecutar = './mp32rtp -i ' + ip + ' -p ' + puerto + ' < ' + medio
    print("Vamos a ejecutar RTP Dirigido a", ip + ':' + puerto)
    os.system(aEjecutar)
    print("Envio Satisfactorio")


def Escucha_VLC(ip, puerto):
    """Metodo para enscuchar en una ip y puerto con VLC."""
    VLC = 'cvlc rtp://@' + ip + ':' + puerto + ' 2> /dev/null &'
    print('ejecutando: ' + VLC)
    os.system(VLC)


class XML_UA(ContentHandler):
    """Clase para manejar XML."""

    def __init__(self):
        """Constructor. Inicializamos las variables."""
        self.misdatos = {}

    def startElement(self, name, attrs):
        """Se utiliza cuando se abre una etiqueta."""
        dat_atrib = {}
        account = ['username', 'passwd']
        uaserver = ['ip', 'puerto']
        rtpaudio = ['puerto']
        regproxy = ['ip', 'puerto']
        log = ['path']
        audio = ['path']
        etiquetas = {'acount': account, 'uaserver': uaserver, 'rtpaudio':
                     rtpaudio, 'regproxy': regproxy, 'log': log, 'audio':
                     audio}
        if name in etiquetas:
            for atributo in etiquetas[name]:
                if attrs.get(atributo, "") != "":
                    dat_atrib[atributo] = attrs.get(atributo, "")
            self.misdatos[name] = dat_atrib

    def get_tags(self):
        """Devuelve un a dista con los datos del xml."""
        return self.misdatos


class ServerHandler(socketserver.DatagramRequestHandler):
    """Server SIP."""

    Rtp = {}

    def handle(self):
        """Handle Server SIP."""
        Ip_emisor = str(self.client_address[0])
        P_emisor = str(self.client_address[1])
        line = self.rfile.read()
        data = line.decode('utf-8')
        Writer_toLOG(Path_Log, 'Received to ' + Ip_emisor + ':' + P_emisor +
                     ': ' + data)
        print("'Recibido -- ")
        print(data)
        METODO = data.split(' ')[0]
        METODOS = ['INVITE', 'BYE', 'ACK']
        if METODO in METODOS:
            if METODO == 'INVITE':
                self.Rtp['IP'] = data.split(' ')[-3][0:9]
                self.Rtp['P'] = data.split(' ')[-2]
                # SDP de vuelta
                O = 'o=' + Sip_E + ' ' + IP + '\r\n'
                P = miXML['rtpaudio']['puerto']
                C = 'Content-Type: application/sdp\r\n\r\n'
                SDP = 'v=0\r\n' + O + 's=misesion\r\nt=0\r\nm=audio ' + P + \
                    ' RTP'
                Respuesta = "SIP/2.0 100 Trying\r\n\r\n" + \
                            "SIP/2.0 180 Ring\r\n\r\n" + \
                            "SIP/2.0 200 OK\r\n" + \
                            C + SDP + "\r\n"
                Writer_toLOG(Path_Log, 'Send to ' + Ip_emisor + ':' +
                             P_emisor + ': ' + Respuesta)
                self.wfile.write(bytes(Respuesta, 'utf-8'))
            elif METODO == 'ACK':
                # Sacar ip y puerto RTP del sdp que llega en el 200 ok
                IP_RTP = self.Rtp['IP']
                P_RTP = self.Rtp['P']
                # Enviamo RTP
                Medio = miXML['audio']['path']
                thread1 = Thread(target=Envio_RTP,
                                 args=(IP_RTP, P_RTP, Medio, ))
                # Escucha del medio por VLC
                thread2 = Thread(target=Escucha_VLC, args=(IP_RTP, P_RTP, ))
                # Iniciamos hilos
                Writer_toLOG(Path_Log, "Vamos a ejecutar RTP Dirigido a" +
                             IP_RTP + ':' + P_RTP)
                thread1.start()
                time.sleep(0.1)
                thread2.start()
                self.Rtp.clear()
            else:
                Writer_toLOG(Path_Log, 'Send to ' + Ip_emisor + ':' +
                             P_emisor + ': ' + 'SIP/2.0 200 OK')
                self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
        elif METODO not in METODOS:
            Writer_toLOG(Path_Log, 'Send to ' + Ip_emisor + ':' + P_emisor +
                         ': ' + 'SIP/2.0 405 Method Not Allowed')
            self.wfile.write(b"SIP/2.0 405 Method Not Allowed\r\n\r\n")
        else:
            Writer_toLOG(Path_Log, 'Send to ' + Ip_emisor + ':' +
                         P_emisor + ': ' + 'SIP/2.0 400 Bad Request')
            self.wfile.write(b"SIP/2.0 400 Bad Request\r\n\r\n")


if __name__ == "__main__":
    try:
        parser = make_parser()
        cHandler = XML_UA()
        parser.setContentHandler(cHandler)
        parser.parse(open(sys.argv[1]))
        miXML = cHandler.get_tags()
        Sip_E = miXML['acount']['username']
        IP = miXML['uaserver']['ip']
        PORT = int(miXML['uaserver']['puerto'])
        Path_Log = miXML['log']['path']
        serv = socketserver.UDPServer((IP, PORT), ServerHandler)
        print("Listening...")
    except IndexError:
        sys.exit("Usage: python uaserver.py config")
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
