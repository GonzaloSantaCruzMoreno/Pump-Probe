# -*- coding: utf-8 -*-
"""
Created on Tue Mar  9 15:34:52 2021
@author: LEC
"""

import serial
import pyvisa
import time
import csv
import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading as th

class Monocromador():
    def __init__(self,puerto):
        self.address = serial.Serial(
                port = puerto,
                baudrate = 9600,
                bytesize = 8,
                stopbits = 1,
                parity = 'N',
                timeout = 1,
                xonxoff = False,
                rtscts = False,
                dsrdtr = False)
        self.puerto = puerto
        self.posicion = self.leerPosicion()
#        self.posicion = -87
#        self.posicion = 400
        self.velocidadNmPorSegundo = 9
#        self.ConfigurarMonocromador()
    def leerPosicion(self):
        self.address.write(b'1CL?\r3\r')
        time.sleep(1)
        valor = -1
        lecturaTotal = ''
        while valor == -1:
            lectura = ''
            lecturaTotal = ''
            while lectura != '\n':
                lectura = self.address.read()
                lectura = lectura.decode('windows-1252')
                lecturaTotal = lecturaTotal + lectura
                time.sleep(0.5)
            valor = lecturaTotal.find('CL?')
        lecturaSpliteada = lecturaTotal.split('\r')
        lecturaSpliteadaBis = lecturaSpliteada[0].split(' ')
        posicionEnNm = float(lecturaSpliteadaBis[len(lecturaSpliteadaBis)-1])
        return posicionEnNm
    def ConfigurarMonocromador(self): # AGREGAR SETEO DE MULT Y OFFSET PARA CAMBIAR DE RED
        comando = '#SLM\r3\r'
        self.address.write(comando.encode())
        time.sleep(5)
        self.Mover(400)
    def Mover(self, LongitudDeOnda_nm): 
        comando = '#MCL\r3\r' + str(LongitudDeOnda_nm) + '\r' #EN EL PROGRAMA INGRESAR LA LONGITUD DE ONDA CON .
        self.address.write(comando.encode())
        time.sleep(self.CalcularTiempoSleep(LongitudDeOnda_nm))
        self.posicion = LongitudDeOnda_nm
    def CalcularTiempoSleep(self, LongitudDeOnda_nm):
        TiempoMonocromador = 0
        if (LongitudDeOnda_nm-self.posicion) == 0:
            time.sleep(1)
        else:
            TiempoMonocromador = abs(LongitudDeOnda_nm-self.posicion)/(self.velocidadNmPorSegundo) # Hay que medirlo
        return TiempoMonocromador