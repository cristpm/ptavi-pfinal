#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Servidor sobre UDP implementado como Register SIP y PROXY."""

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import socketserver
import sys
import time
import json
import socket
import random
import hashlib


def Writer_toLOG(f, mensaje):
    """Escribir en el fichero log."""
    gmt = time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time())) + ' '
    M = mensaje.split('\r\n')
    S = ' '.join(M)
    outfile = open(f, 'a')
    outfile.write(gmt + S + '\n')
    outfile.close()


def Cabecera_Proxy(mensaje):
    """Devuelve el mensaje con la cabera proxy."""
    E = mensaje.split('\r\n')
    header = 'Via: SIP/2.0/UDP' + ' proxy.' + miXML['server']['ip'] + ':' + \
             miXML['server']['puerto'] + ';branch=uyvfg7236ftgu4b\r\n'
    if E[-2] == '':  # Si el mensaje no tiene cuerpo
        E[-2] = header
    else:
        E[E.index('')] = header
    Nuevo_Mensaje = '\r\n'.join(E)
    return Nuevo_Mensaje


class XML_PR(ContentHandler):
    """Clase para manejar XML."""

    def __init__(self):
        """Constructor. Inicializamos las variables."""
        self.misdatos = {}

    def startElement(self, name, attrs):
        """Se utiliza cuando se abre una etiqueta."""
        dat_atrib = {}
        server = ['name', 'ip', 'puerto']
        database = ['path', 'passwdpath']
        log = ['path']
        etiquetas = {'log': log, 'server': server, 'database': database}
        if name in etiquetas:  # esta en el dic etiquetas
            for atributo in etiquetas[name]:
                # etiquetas es una lista con los atributos de cada etiqueta
                if attrs.get(atributo, "") != "":
                    dat_atrib[atributo] = attrs.get(atributo, "")
            self.misdatos[name] = dat_atrib

    def get_tags(self):
        """Devuelve un a dista con los datos del xml."""
        return self.misdatos


class SIPRegisterHandler(socketserver.DatagramRequestHandler):
    """Echo server Register Proxy class."""

    clientes = []
    respuestas = {}

    def handle(self):
        """Handle Register/Proxy SIP."""
        self.json2registered()
        self.expiration()
        Ip_emisor = str(self.client_address[0])
        P_emisor = str(self.client_address[1])
        line = self.rfile.read()
        data = line.decode('utf-8')
        Writer_toLOG(Path_Log, 'Received to ' + Ip_emisor + ':' + P_emisor +
                     ': ' + data)
        print("'Recibido --")
        print(data)
        METODO = data.split(' ')[0]
        METODOS = ['REGISTER', 'INVITE', 'BYE', 'ACK']
        if METODO in METODOS:
            if METODO == 'REGISTER':
                self.Autentificacion_Register(data)
            else:
                if self.Client_Registrado(data) == "TRUE":
                    self.Server_Proxy(data)
                else:
                    Writer_toLOG(Path_Log, 'Send to ' + Ip_emisor + ':' +
                                 P_emisor + ': ' +
                                 'SIP/2.0 404 User Not Found')
                    self.wfile.write(b"SIP/2.0 404 User Not Found\r\n\r\n")
        elif METODO not in METODOS:
            Writer_toLOG(Path_Log, 'Send to ' + Ip_emisor + ':' +
                         P_emisor + ': ' + 'SIP/2.0 405 Method Not Allowed')
            self.wfile.write(b"SIP/2.0 405 Method Not Allowed\r\n\r\n")
        else:
            Writer_toLOG(Path_Log, 'Send to ' + Ip_emisor + ':' +
                         P_emisor + ': ' + 'SIP/2.0 400 Bad Request')
            self.wfile.write(b"SIP/2.0 400 Bad Request\r\n\r\n")

    def Server_Proxy(self, mensaje):
        """Inicia la funcionalidad servidor proxy."""
        Dir_SIP = mensaje.split(' ')[1][4:]
        for user in self.clientes:
            if user[0] == Dir_SIP:
                client = user
        IP = str(client[1]["IP"])
        PUERTO = str(client[1]["Puerto"])
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((IP, int(PUERTO)))
        Nuevo_Mensaje = Cabecera_Proxy(mensaje)
        Writer_toLOG(Path_Log, 'Send to ' + IP + ':' + PUERTO + ': ' +
                     Nuevo_Mensaje)
        print('Renviando ------------------------')
        print(Nuevo_Mensaje)
        my_socket.send(bytes(Nuevo_Mensaje, 'utf-8'))
        METODO = Nuevo_Mensaje.split(' ')[0]
        if METODO != 'ACK':
            respuesta = my_socket.recv(1024)
            Writer_toLOG(Path_Log, 'Received to ' + IP + ':' + PUERTO +
                         ': ' + respuesta.decode('utf-8'))
            Nueva_Respuesta = Cabecera_Proxy(respuesta.decode('utf-8'))
            Writer_toLOG(Path_Log, 'Send to ' + IP + ':' + PUERTO + ': ' +
                         Nueva_Respuesta)
            print('Enviando respuesta ------------------------ ')
            print(Nueva_Respuesta)
            self.wfile.write(bytes(Nueva_Respuesta, 'utf-8'))
            my_socket.close()

    def Register(self, mensaje):
        """Gestiona Register valido."""
        Ip_client = self.client_address[0]
        client_Puert_A = mensaje.split(' ')[1]
        Dir_SIP = client_Puert_A.split(':')[1]
        Puert_A = int(client_Puert_A.split(':')[2])
        Expires = int(mensaje.split('\r\n')[1][9:])
        Time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()))
        Time_exp = time.strftime('%Y-%m-%d %H:%M:%S',
                                 time.gmtime(time.time() + Expires))
        client = [Dir_SIP, {"IP": Ip_client, "Puerto": Puert_A,
                            "Expires": Expires, "Time_registro": Time,
                            "Time_expiracion": Time_exp}]
        if Expires == 0:
            for user in self.clientes:
                if user[0] == Dir_SIP:
                    self.clientes.remove(user)
        if Expires > 0:
            for user in self.clientes:
                if user[0] == Dir_SIP:
                    self.clientes.remove(user)
            self.clientes.append(client)
        print('Lista clientes registrados')
        print(self.clientes)

    def Client_Registrado(self, mensaje):
        """Devuelve un String para comprobar el registro del cliente."""
        Dir_SIP = mensaje.split(' ')[1][4:]
        S = 'FALSE'
        if len(self.clientes) > 0:
            for user in self.clientes:
                if user[0] == Dir_SIP:
                    S = 'TRUE'
        return S

    def Autentificacion_Register(self, data):
        """Realiza todo el proceso de un Register."""
        Ip_emisor = str(self.client_address[0])
        P_emisor = str(self.client_address[1])
        client_Puert_A = data.split(' ')[1]
        Dir_SIP = client_Puert_A.split(':')[1]
        if len(data.split(' ')) <= 4:
            # Si es el primer Register pedimos autentificacion
            nonce = str(random.randint(1, 89898989879))
            Cabecera = 'WWW-Authenticate: Digest nonce="' + nonce + '"'
            Writer_toLOG(Path_Log, 'Send to ' + Ip_emisor + ':' + P_emisor +
                         ': ' + 'SIP/2.0 401 Unauthorized ' + Cabecera)
            self.wfile.write(b"SIP/2.0 401 Unauthorized\r\n" +
                             bytes(Cabecera, 'utf-8') + b"\r\n\r\n")
            # Buscamos la contraseña de este usuario en el fichero de password
            f = open(miXML['database']['passwdpath'], 'r')
            lines = f.read()
            clientes = lines.split('\n')
            for cliente in clientes:
                if cliente.split(':')[0] == Dir_SIP:
                    contraseña = cliente.split(':')[-1]
                    # guardamos el response que tendriamos que recibir
                    r = hashlib.md5()
                    r.update(bytes(contraseña, 'utf-8'))
                    r.update(bytes(nonce, 'utf-8'))
                    self.respuestas[Dir_SIP] = r.hexdigest()
        else:  # Si nos llega el segundo register con el response
            response = data.split('"')[-2]
            try:
                if response == self.respuestas[Dir_SIP]:
                    self.Register(data)  # Registramos al cliente
                    self.register2json()
                    Writer_toLOG(Path_Log, 'Send to ' + Ip_emisor + ':' +
                                 P_emisor + ': ' + 'SIP/2.0 200 OK')
                    self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
                else:
                    Writer_toLOG(Path_Log, 'Send to ' + Ip_emisor + ':' +
                                 P_emisor + ': ' + 'SIP/2.0 400 Bad Request' +
                                 'response recibido incorrecto')
                    self.wfile.write(b"SIP/2.0 400 Bad Request\r\n\r\n")
            except KeyError:  # Este cliente no tiene cuenta
                Writer_toLOG(Path_Log, 'Send to ' + Ip_emisor + ':' +
                             P_emisor + ': ' + 'SIP/2.0 400 Bad Request' +
                             'Cliente sin cuenta previa')
                self.wfile.write(b"SIP/2.0 400 Bad Request\r\n\r\n")

    def register2json(self):
        """passe customer lists to json."""
        json.dump(self.clientes, open(miXML['database']['path'], 'w'),
                  indent=4)

    def expiration(self):
        """remove clients expired."""
        gmt = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()))
        for user in self.clientes:
            if gmt > user[1]["Time_expiracion"]:
                self.clientes.remove(user)

    def json2registered(self):
        """Customer copy a file json."""
        try:
            with open(miXML['database']['path']) as data_file:
                self.clientes = json.load(data_file)
        except:
            pass


if __name__ == "__main__":
    try:
        parser = make_parser()
        cHandler = XML_PR()
        parser.setContentHandler(cHandler)
        parser.parse(open(sys.argv[1]))
        miXML = cHandler.get_tags()
        IP = miXML['server']['ip']
        PORT = int(miXML['server']['puerto'])
        Path_Log = miXML['log']['path']
        serv = socketserver.UDPServer(('', PORT), SIPRegisterHandler)
        Writer_toLOG(Path_Log, 'Starting')
        print('Server MiServidor' + miXML['server']['name'] +
              ' listening at port ' + str(PORT) + '...')
    except IndexError:
        sys.exit("Usage: python proxy_registrar.py config")
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        Writer_toLOG(Path_Log, 'Finishing')
        print("Finalizado servidor")
