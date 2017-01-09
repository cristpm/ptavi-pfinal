#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Clase (y programa principal) para un servidor SIP."""

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import socketserver
import sys
import os
import time

class LOGHandler():
    """
    Configuración del fichero Log
    """
    def Writer(self, f, mensaje):
        """ Método para escribir en el fichero log """
    
        gmt = time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time())) + ' '
        M = mensaje.split('\r\n')
        S = ' '.join(M);
        outfile = open(f, 'a') 
        outfile.write(gmt + S + '\n')
        outfile.close()

class XML_UA(ContentHandler):
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
        account = ['username', 'passwd']
        uaserver = ['ip', 'puerto']
        rtpaudio = ['puerto']
        regproxy = ['ip', 'puerto']
        log = ['path']
        audio = ['path']
        etiquetas = {'acount': account, 'uaserver': uaserver, 'rtpaudio': 
                    rtpaudio, 'regproxy': regproxy, 'log': log, 'audio': audio}
        if name in etiquetas:#  esta en el dic etiquetas
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
        Ip_emisor = str(self.client_address[0])
        P_emisor = str(self.client_address[1])
        line = self.rfile.read()
        data = line.decode('utf-8')
        miLOG.Writer(Path_Log, 'Received to ' + Ip_emisor + ':' + P_emisor + \
        ': ' + data)
        print("'Recibido -- ")
        print(data)
        METODO = data.split(' ')[0]
        METODOS = ['INVITE', 'BYE', 'ACK']
        if METODO in METODOS:
            if METODO == 'INVITE':
                self.Rtp['IP']= data.split(' ')[-3][0:9]
                self.Rtp['P'] = data.split(' ')[-2]
                # SDP de vuelta
                O = 'o=' + Sip_E + ' ' + IP + '\r\n'
                P = miXML['rtpaudio']['puerto']
                C = 'Content-Type: application/sdp\r\n\r\n'
                SDP = 'v=0\r\n' + O + 's=misesion\r\nt=0\r\nm=audio ' + P + \
                ' RTP'
                Respuesta = "SIP/2.0 100 Trying\r\n\r\n" + \
                "SIP/2.0 180 Ring\r\n\r\n" + "SIP/2.0 200 OK\r\n" + \
                C + SDP + "\r\n"
                miLOG.Writer(Path_Log, 'Send to ' + Ip_emisor + ':' + \
                P_emisor + ': ' + Respuesta)
                self.wfile.write(bytes(Respuesta, 'utf-8'))     
            elif METODO == 'ACK':
                VLC = 'cvlc rtp://@' + IP + ':' + miXML['rtpaudio']['puerto']
                #os.system(VLC)
                aEjecutar = './mp32rtp -i ' + self.Rtp['IP'] + ' -p ' + \
                self.Rtp['P'] + ' < ' + miXML['audio']['path']
                print("Vamos a ejecutar RTP", aEjecutar )
                miLOG.Writer(Path_Log, aEjecutar)
                os.system(aEjecutar)
                print("Envio Satisfactorio")
                self.Rtp.clear()
            else:
                miLOG.Writer(Path_Log, 'Send to ' + Ip_emisor + ':' 
                + P_emisor + ': ' + 'SIP/2.0 200 OK')
                self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
        elif METODO not in METODOS:
            miLOG.Writer(Path_Log, 'Send to ' + Ip_emisor + ':' 
                + P_emisor + ': ' + 'SIP/2.0 405 Method Not Allowed')
            self.wfile.write(b"SIP/2.0 405 Method Not Allowed\r\n\r\n")
        else:
            miLOG.Writer(Path_Log, 'Send to ' + Ip_emisor + ':' 
                + P_emisor + ': ' + 'SIP/2.0 400 Bad Request')
            self.wfile.write(b"SIP/2.0 400 Bad Request\r\n\r\n")


if __name__ == "__main__":
    try:
        parser = make_parser()
        cHandler = XML_UA()
        parser.setContentHandler(cHandler)
        parser.parse(open(sys.argv[1]))
        miXML = cHandler.get_tags()
        miLOG = LOGHandler()
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
