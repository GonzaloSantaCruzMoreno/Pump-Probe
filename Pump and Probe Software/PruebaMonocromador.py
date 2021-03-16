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
        self.velocidadNmPorSegundo = 9
        self.ConfigurarMonocromador()
        self.posicion = self.leerPosicion()
        if self.posicion < 400:
            self.Mover(400)    
    def leerPosicion(self):
        self.address.write(b'#CL?\r3\r')
        time.sleep(1)
        valor = -1
        lecturaTotal = ''
        while valor == -1:
            lectura = ''
            lecturaTotal = ''
            while lectura != '\n':
                lectura = self.address.read()
                print(lectura)
                lectura = lectura.decode('windows-1252')
                print(lectura)
                lecturaTotal = lecturaTotal + lectura
                time.sleep(0.8)
            valor = lecturaTotal.find('CL?')
        lecturaSpliteada = lecturaTotal.split('\r')
        lecturaSpliteadaBis = lecturaSpliteada[0].split(' ')
        lecturaSpliteadaBisBis = lecturaSpliteadaBis[len(lecturaSpliteadaBis)-1]
        lecturaSpliteadaBisBisBis = lecturaSpliteadaBisBis.split('!!')
        posicionEnString = lecturaSpliteadaBisBisBis[0]
        if posicionEnString[len(posicionEnString)-3] == '.':
            posicionEnString = posicionEnString.split('.')[0]
            print(posicionEnString)
        posicionEnNm = float(posicionEnString)
        return posicionEnNm
    def ConfigurarMonocromador(self): # AGREGAR SETEO DE MULT Y OFFSET PARA CAMBIAR DE RED
        comando = '#SLM\r3\r'
        self.address.write(comando.encode())
        time.sleep(3)
    def Mover(self, LongitudDeOnda_nm): 
        comando = '#MCL\r3\r' + str(LongitudDeOnda_nm) + '\r'
        self.address.write(comando.encode())
        time.sleep(self.CalcularTiempoSleep(LongitudDeOnda_nm))
        self.posicion = LongitudDeOnda_nm
    def CalcularTiempoSleep(self, LongitudDeOnda_nm):
        TiempoMonocromador = 0
        if (LongitudDeOnda_nm-self.posicion) == 0:
            time.sleep(1)
        else:
            TiempoMonocromador = abs(LongitudDeOnda_nm-self.posicion)/(self.velocidadNmPorSegundo) + 2.5
        return TiempoMonocromador
