# -*- coding: utf-8 -*-
"""
Created on Sun Feb 21 20:18:14 2021

@author: Usuario
"""

import serial
import time

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
        self.ConfigurarSMC()
        self.posicion = 0
        
    def ConfigurarSMC(self):    
        self.address.write(b'1RS\r\n')
        time.sleep(5)
        self.address.write(b'1PW1\r\n')
        time.sleep(0.5)
        self.address.write(b'1HT0\r\n')
        time.sleep(0.2)
#        self.address.write(b'1VA???\r\n')
        time.sleep(0.2)
        self.address.write(b'1PW0\r\n')
        time.sleep(2)
        self.address.write(b'1OR\r\n')   # HAY QUE ESPERAR QUE EL SMC SE PONGA EN VERDE!!!
    
    def Mover(self, PosicionSMC_Step): # Configurar Velocidad
        comando = '1PA' + str(PosicionSMC_Step) + '\r\n'
        self.address.write(comando.encode())
        self.posicion = PosicionSMC_Step
        time.sleep(self.CalcularTiempoSleep(PosicionSMC_Step))
        
    def CalcularTiempoSleep(self, PosicionSMC_Step):
        TiempoSMC = abs(PosicionSMC_Step-self.posicion)/self.velocidad # Hay que medirlo
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

