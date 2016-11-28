#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Clase (y programa principal) para un servidor SIP."""

import socketserver
import sys
import os


class ServerHandler(socketserver.DatagramRequestHandler):
    """Server SIP."""

    def handle(self):
        """Handle Server SIP."""
        line = self.rfile.read()
        data = line.decode('utf-8')
        print("El cliente nos manda:")
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
                aEjecutar = 'mp32rtp -i ' + IP + ' -p 23032 < ' + fichero_audio
                print("Vamos a ejecutar", aEjecutar)
                os.system(aEjecutar)
            else:
                self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
        elif METODO not in METODOS:
            self.wfile.write(b"SIP/2.0 405 Method Not Allowed\r\n\r\n")
        else:
            self.wfile.write(b"SIP/2.0 400 Bad Request\r\n\r\n")


if __name__ == "__main__":
    try:
        IP = sys.argv[1]
        PORT = int(sys.argv[2])
        fichero_audio = sys.argv[3]
        if not os.path.isfile(fichero_audio):
            sys.exit(fichero_audio + ": File not found")
        else:
            serv = socketserver.UDPServer((IP, PORT), ServerHandler)
            print("Listening...")
    except IndexError:
        sys.exit("Usage: python server.py IP port audio_file")
    try:
        # bucle esperando peticiones
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
