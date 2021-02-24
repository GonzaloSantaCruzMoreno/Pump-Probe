# -*- coding: utf-8 -*-
"""
Created on Sun Feb 21 20:18:14 2021

@author: Usuario
"""

import serial
import time

class SMC():
    def __init__(self):
        self.address = serial.Serial(
                port = 'COM4',
                baudrate = 57600,
                bytesize = 8,
                stopbits = 1,
                parity = 'N',
                timeout = 1,
                xonxoff = False,
                rtscts = False,
                dsrdtr = False)
        self.posicion = 0
        self.velocidadMmPorSegundo = 0.16
        self.ConfigurarSMC()
        
        
    def ConfigurarSMC(self):    
        self.address.write(b'1RS\r\n')
        time.sleep(5)
        self.address.write(b'1PW1\r\n')
        time.sleep(0.5)
        self.address.write(b'1HT0\r\n')
        time.sleep(0.2)
        self.address.write(b'1PW0\r\n')
        time.sleep(2)
        self.address.write(b'1OR\r\n')   # HAY QUE ESPERAR QUE EL SMC SE PONGA EN VERDE!!!
        
        self.address.write(b'1TS\r\n')
        valor = -1
        while valor == -1:
            lectura = ''
            lecturaTotal = ''
            while lectura != '\n':   
                lectura = self.address.read()
                lectura = lectura.decode()
                lecturaTotal = lecturaTotal + lectura
                print(lectura)
                print(lectura != '\n')
                print(lecturaTotal)
            print(lecturaTotal)
            valor = lecturaTotal.find('32')
            time.sleep(5)
            self.address.write(b'1TS\r\n')
        print('Llego')
    
    def Mover(self, PosicionSMC_mm): # Configurar Velocidad
        PosicionSMC_Step = PosicionSMC_mm
        comando = '1PA' + str(PosicionSMC_Step) + '\r\n'
        self.address.write(comando.encode())
        self.posicion = PosicionSMC_mm
        time.sleep(self.CalcularTiempoSleep(PosicionSMC_mm))
        
    def CalcularTiempoSleep(self, PosicionSMC_mm):
        TiempoSMC = 0
        if (PosicionSMC_mm-self.posicion) == 0:
            time.sleep(0.5)
        else:
            TiempoSMC = abs(PosicionSMC_mm-self.posicion)/self.velocidadMmPorSegundo # Hay que medirlo
        return TiempoSMC


#%%%

smcBis = serial.Serial(
                port = 'COM5',
                baudrate = 57600,
                bytesize = 8,
                stopbits = 1,
                parity = 'N',
                timeout = 1,
                xonxoff = False,
                rtscts = False,
                dsrdtr = False)

smcBis.write(b'1RS\r\n')
time.sleep(5)
smcBis.write(b'1PW1\r\n')
time.sleep(1)
smcBis.write(b'1VA?\r\n')
#LEER VELOCIDAD

