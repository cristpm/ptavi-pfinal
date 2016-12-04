#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Clase (y programa principal) para un servidor SIP."""

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import socketserver
import sys
import os

class XMLHandler(ContentHandler):
    """
    Clase para manejar smil
    """

    def __init__(self):
        """
        Constructor. Inicializamos las variables
        """
        self.misdatos = {}

    def startElement(self, name, attrs):
        """
        Método que se llama cuando se abre una etiqueta
        """
        dat_atrib = {}
        #Etiquetas UA
        account = ['username', 'passwd']
        uaserver = ['ip', 'puerto']
        rtpaudio = ['puerto']
        regproxy = ['ip', 'puerto']
        log = ['path']
        audio = ['path']
        #eiquetas PROXY/REGISTER - log
        server = ['name', 'ip', 'puerto']
        database = ['path', 'passwdpath']
        
        
        etiquetas = {'acount': account, 'uaserver': uaserver, 'rtpaudio': 
                    rtpaudio, 'regproxy': regproxy, 'log': log, 'audio': audio,
                    'server': server, 'database': database}
        if name in etiquetas:#siel nombre de la entique esta en el dic etiquetas
            for atributo in etiquetas[name]:
            #etiquetas[name] es una lista con los atributos de cada etiqueta
                if attrs.get(atributo, "") != "":
                    dat_atrib[atributo] = attrs.get(atributo, "")
            self.misdatos[name] = dat_atrib

    def get_tags(self):
        return self.misdatos

class ServerHandler(socketserver.DatagramRequestHandler):
    """Server SIP."""

    def handle(self):
        """Handle Server SIP."""
        line = self.rfile.read()
        data = line.decode('utf-8')
        print("'Recibido -- ")
        print(data)
        METODO = data.split(' ')[0]
        METODOS = ['INVITE', 'BYE', 'ACK']
        if METODO in METODOS:
            if METODO == 'INVITE':
                self.wfile.write(b"SIP/2.0 100 Trying\r\n\r\n")
                self.wfile.write(b"SIP/2.0 180 Ring\r\n\r\n")
            if METODO == 'ACK':
                # aEjecutar es un string con lo que se ha de ejecutar en la
                # shell
                ##aEjecutar = 'mp32rtp -i ' + IP + ' -p 23032 < ' + fichero_audio
                print("Vamos a ejecutar RTP")#, aEjecutar)
                ##os.system(aEjecutar)
            else:
                self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
        elif METODO not in METODOS:
            self.wfile.write(b"SIP/2.0 405 Method Not Allowed\r\n\r\n")
        else:
            self.wfile.write(b"SIP/2.0 400 Bad Request\r\n\r\n")


if __name__ == "__main__":
    try:
        parser = make_parser()
        cHandler = XMLHandler()
        parser.setContentHandler(cHandler)
        parser.parse(open(sys.argv[1]))
        miXML = cHandler.get_tags()
        
        #IP Y Puerto de escucha del UA server 
        IP = miXML['uaserver']['ip']
        PORT = int(miXML['uaserver']['puerto'])
        ##fichero_audio = sys.argv[3]
        ##if not os.path.isfile(fichero_audio):
            ##sys.exit(fichero_audio + ": File not found")
        ##else:
        serv = socketserver.UDPServer((IP, PORT), ServerHandler)
        print("Listening...")
    except IndexError:
        sys.exit("Usage: python uaserver.py config")
    try:
        # bucle esperando peticiones
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
