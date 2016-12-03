#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Servidor sobre UDP implementado como Register SIP y PROXY."""

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import socketserver
import uaserver
import sys
import time
import json
import socket

class SIPRegisterHandler(socketserver.DatagramRequestHandler):
    """Echo server Register  class."""

    clientes = []

    def handle(self):  # TRATAMOS EL SOCKET COMO UN FICHERO
        """Handle Register/Proxy SIP."""
        ##self.json2registered()
        self.expiration()
        line = self.rfile.read()
        data = line.decode('utf-8')
        print("'Recibido --") 
        print(data)
        METODO = data.split(' ')[0]
        METODOS = ['REGISTER', 'INVITE', 'BYE', 'ACK']
        if METODO in METODOS:
            if METODO == 'REGISTER':
                self.Register(data)# Actuamos como un servidor SIP/REGISTER
                self.register2json()
                self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
            else:
                if self.Client_Registrado(data) == "TRUE":
                    self.Proxy(data)# Actuamos como un servidor PROXY   
                else:    
                    self.wfile.write(b"SIP/2.0 404 User Not Found\r\n\r\n")
        elif METODO not in METODOS:
            self.wfile.write(b"SIP/2.0 405 Method Not Allowed\r\n\r\n")
        else:
            self.wfile.write(b"SIP/2.0 400 Bad Request\r\n\r\n")
            
    def Proxy(self, mensaje):
        """Buscamos el UA al que renviar la informacion la renvia y espera"""
        """respuesta para enviarla al UA que inicio la peticion"""
        Dir_SIP = mensaje.split(' ')[1][4:]
        for user in self.clientes:
            if user[0] == Dir_SIP:
                client = user# datos del cliente al que renviamos el mensaje
        IP = client[1]["IP"]
        PUERTO = client[1]["Puerto"]
        # Creamos el socket,lo configuramos y lo atamos a un servidor/puerto UA
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((IP, PUERTO))
        print('Renviando -- ')
        my_socket.send(bytes(mensaje, 'utf-8'))
        print(mensaje)
        respuesta = my_socket.recv(1024)
        print('Enviando respuesta -- ')
        self.wfile.write(respuesta)
        
        print(mensaje)
            
                
    def Register(self, mensaje):
        """Gestionamos que hacer cuando un usuario nos envia un Register"""
        Ip_client = self.client_address[0]
        client_Puert_A = mensaje.split(' ')[1]
        Dir_SIP = client_Puert_A.split(':')[1]
        Puert_A = int(client_Puert_A.split(':')[2])
        
        Expires = int(mensaje.split(' ')[3][0:-4])
        Time_exp = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time() + Expires))
        client = [Dir_SIP, {"IP": Ip_client, "Puerto": Puert_A , "Time_exp": Time_exp}]
        if Expires == 0:
            for user in self.clientes:
                if user[0] == Dir_SIP:
                    self.clientes.remove(user)
        if Expires > 0:
            for user in self.clientes:
                if user[0] == Dir_SIP:
                    self.clientes.remove(user)
            self.clientes.append(client)
        print(self.clientes)
            
    def Client_Registrado(self, mensaje):
        """Funcion que devuelve un Booleano para comprobar el registro del cliente"""
        Dir_SIP = mensaje.split(' ')[1][4:]
        S = 'FALSE'
        if len(self.clientes) > 0:
            for user in self.clientes:
                print(user)
                if user[0] == Dir_SIP:
                    S = 'TRUE'
        return S      
        
    def register2json(self):
        """passe customer lists to json."""
        json.dump(self.clientes, open('registered.json', 'w'), indent=4)

    def expiration(self):
        """remove clients expired."""
        gmt = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()))
        for user in self.clientes:
            if gmt > user[1]["Time_exp"]:
                self.clientes.remove(user)

    def json2registered(self):
        """Customer copy a file json."""
        try:
            with open('registered.json') as data_file:
                self.clientes = json.load(data_file)
        except:
            pass


if __name__ == "__main__":
    parser = make_parser()
    cHandler = uaserver.XMLHandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(sys.argv[1]))
    miXML = cHandler.get_tags()
    IP = miXML['server']['ip']
    PORT = int(miXML['server']['puerto'])#
    serv = socketserver.UDPServer(('', PORT), SIPRegisterHandler)
    print('Lanzando servidor PROXY/REGISTER '+ miXML['server']['name'] + ' ...')
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
