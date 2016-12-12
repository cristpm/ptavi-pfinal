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
    Clase para manejar XML
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
        # Etiquetas UA
        account = ['username', 'passwd']
        uaserver = ['ip', 'puerto']
        rtpaudio = ['puerto']
        regproxy = ['ip', 'puerto']
        log = ['path']
        audio = ['path']
        # eiquetas PROXY/REGISTER - log
        server = ['name', 'ip', 'puerto']
        database = ['path', 'passwdpath']
        etiquetas = {'acount': account, 'uaserver': uaserver, 'rtpaudio': 
                    rtpaudio, 'regproxy': regproxy, 'log': log, 'audio': audio,
                    'server': server, 'database': database}
        if name in etiquetas:# siel nombre de la entique esta en el dic etiquetas
            for atributo in etiquetas[name]:
            # etiquetas[name] es una lista con los atributos de cada etiqueta
                if attrs.get(atributo, "") != "":
                    dat_atrib[atributo] = attrs.get(atributo, "")
            self.misdatos[name] = dat_atrib

    def get_tags(self):
        return self.misdatos
        

class ServerHandler(socketserver.DatagramRequestHandler):
    """Server SIP."""
    
    Rtp = {}

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
                #sacar ip y puerto rtp del sdp
                self.Rtp['IP']= data.split(' ')[4][0:9]
                self.Rtp['P'] = data.split(' ')[-2]
                print(self.Rtp)
                self.wfile.write(b"SIP/2.0 100 Trying\r\n\r\n")
                self.wfile.write(b"SIP/2.0 180 Ring\r\n\r\n")
                # SDP de vuelta
                O = '0=' + Sip_E + ' ' + IP + '\r\n'
                P_RTP = miXML['rtpaudio']['puerto']
                Cabecera = 'Content-Type: application/sdp\r\n\r\n'
                SDP = 'v=0\r\n' + O + 's=misesion\r\nt=0\r\nm=audio ' + P_RTP + ' RTP'
                self.wfile.write(b"SIP/2.0 200 OK\r\n" + bytes(Cabecera, 'utf-8')+ bytes(SDP, 'utf-8') + b"\r\n")     
            elif METODO == 'ACK':
                print(self.Rtp)
                aEjecutar = 'mp32rtp -i ' + self.Rtp['IP'] + ' -p ' + self.Rtp['P'] +' < ' + miXML['audio']['path']
                print("Vamos a ejecutar RTP")
                os.system(aEjecutar)
                print("Envio Satisfactorio")
                self.Rtp.clear()
                print(self.Rtp)
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

        # Direccion SIP IP Y Puerto de escucha del UA server
        Sip_E = miXML['acount']['username'] 
        IP = miXML['uaserver']['ip']
        PORT = int(miXML['uaserver']['puerto'])
        serv = socketserver.UDPServer((IP, PORT), ServerHandler)
        print("Listening...")
    except IndexError:
        sys.exit("Usage: python uaserver.py config")
    try:
        # bucle esperando peticiones
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
