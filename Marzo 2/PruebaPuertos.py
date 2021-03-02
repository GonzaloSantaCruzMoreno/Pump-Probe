import serial
import pyvisa
import time
import csv
import pandas
import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading as th

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
        self.posicion = 0
        self.velocidadMmPorSegundo = 0.16
        self.ConfigurarSMC()
    def ConfigurarSMC(self):    
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
        self.address.write(b'1TS\r\n')
        valor = -1
        while valor == -1:
            lectura = ''
            lecturaTotal = ''
            while lectura != '\n':   
                lectura = self.address.read()
                lectura = lectura.decode('windows-1252')
                lecturaTotal = lecturaTotal + lectura
            valor = lecturaTotal.find('32')
            time.sleep(5)
            self.address.write(b'1TS\r\n')
    def Mover(self, PosicionSMC_mm): 
        comando = '1PA' + str(PosicionSMC_mm) + '\r\n'
        self.address.write(comando.encode())
        time.sleep(self.CalcularTiempoSleep(PosicionSMC_mm))
        self.posicion = PosicionSMC_mm
    def CalcularTiempoSleep(self, PosicionSMC_mm):
        TiempoSMC = 0
        if (PosicionSMC_mm-self.posicion) == 0:
            time.sleep(0.5)
        else:
            TiempoSMC = abs(PosicionSMC_mm-self.posicion)/self.velocidadMmPorSegundo + time.sleep(1)
        return TiempoSMC