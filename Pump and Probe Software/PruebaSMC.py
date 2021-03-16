import serial
import pyvisa
import time
import csv
import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.axes_grid1 import make_axes_locatable
import threading as th

global t

class SMC():
    def __init__(self,puerto):
        self.address = serial.Serial(
                port = puerto,
                baudrate = 57600,
                bytesize = 8,
                stopbits = 1,
                parity = 'N',
                timeout = 1,
                xonxoff = False,
                rtscts = False,
                dsrdtr = False)
        self.puerto = puerto
        self.posicion = 0 # Solo para inicializar la variable. Al configurar se lee la posición.
        self.velocidadMmPorSegundo = 0.16
        self.ConfigurarSMC()
    def ConfigurarSMC(self):    
        valor = -1
        estadosReady = ['32','33','34']
        while valor == -1:
            time.sleep(1)
            self.address.write(b'1TS\r\n')
            time.sleep(2)
            lectura = ''
            lecturaTotal = ''
            while lectura != '\n' and lectura != '': 
                time.sleep(1)
                lectura = self.address.read()
                print(lectura)
                lectura = lectura.decode('windows-1252')
                print(lectura)
                lecturaTotal = lecturaTotal + lectura
            if any(x in lecturaTotal for x in estadosReady) and 'TS' in lecturaTotal:
                valor = 1
                self.posicion = self.LeerPosicion()
                return
        self.address.write(b'1RS\r\n')
        time.sleep(7)
        self.address.write(b'1PW1\r\n')
        time.sleep(2)
        self.address.write(b'1HT0\r\n')
        time.sleep(2)
        self.address.write(b'1PW0\r\n')
        time.sleep(2)
        self.address.write(b'1OR\r\n')
        time.sleep(2)
        valor = -1
        while valor == -1:
            time.sleep(1)
            self.address.write(b'1TS\r\n')
            time.sleep(2)
            lectura = ''
            lecturaTotal = ''
            while lectura != '\n' and lectura != '': 
                time.sleep(1)
                lectura = self.address.read()
                print(lectura)
                lectura = lectura.decode('windows-1252')
                print(lectura)
                lecturaTotal = lecturaTotal + lectura
            valor = lecturaTotal.find('32')
        self.posicion = 0
    def LeerPosicion(self):
        self.address.write(b'1TH\r\n')
        time.sleep(1)
        valor = -1
        while valor == -1:
            time.sleep(2)
            lectura = ''
            lecturaTotal = ''
            while lectura != '\n' and lectura != '': 
                time.sleep(1)
                lectura = self.address.read()
                print(lectura)
                lectura = lectura.decode('windows-1252')
                print(lectura)
                lecturaTotal = lecturaTotal + lectura
            print(lecturaTotal)
            if 'TH' in lecturaTotal:
                a = lecturaTotal.split('\r')
                b = a[0]
                c = b.split(' ')
                d = c[len(c)-1]
                return float(d)
            self.address.write(b'1TH\r\n')
    def Mover(self, PosicionSMC_mm): 
        comando = '1PA' + str(PosicionSMC_mm) + '\r\n'
        self.address.write(comando.encode())
        time.sleep(self.CalcularTiempoSleep(PosicionSMC_mm))
        PosicionSMC_mm = round(PosicionSMC_mm, 6)
        self.posicion = PosicionSMC_mm
    def CalcularTiempoSleep(self, PosicionSMC_mm):
        TiempoSMC = 0
        if (PosicionSMC_mm-self.posicion) == 0:
            time.sleep(0.5)
        else:
            TiempoSMC = abs(PosicionSMC_mm-self.posicion)/self.velocidadMmPorSegundo + 1
        return TiempoSMC