import serial
from serial.tools import list_ports
from serial.tools import miniterm
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
                xonxoff = True,
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
            time.sleep(0.3)
            self.address.write(b'1TS\r\n')
            time.sleep(0.3)
            lectura = self.LeerBuffer()
            if 'TS' in lectura:
                valor = 1
                if any(x in lectura for x in estadosReady):
                    self.posicion = abs(round(self.LeerPosicion(),5))
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
            time.sleep(0.3)
            self.address.write(b'1TS\r\n')
            time.sleep(0.3)
            lectura = self.LeerBuffer()
            if 'TS' in lectura:
                valor = lectura.find('32')
        self.posicion = 0
    def LeerPosicion(self):
        valor = -1
        while valor == -1:
            self.address.write(b'1TH\r\n')
            time.sleep(0.3)
            lectura = self.LeerBuffer()
            if 'TH' in lectura:
                a = lectura.split('\r')[0]
                b = a.split('TH')[len(a.split('TH'))-1]
                return float(b)
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
    def LeerBuffer(self):
        lectura = 'a'
        lecturaTotal = ''
        while lectura != '\n' and lectura != '': 
            time.sleep(0.3)
            lectura = self.address.read()
            print(lectura)
            lectura = lectura.decode('windows-1252')
            lecturaTotal = lecturaTotal + lectura
        return lecturaTotal        