# -*- coding: utf-8 -*-
"""
Created on Sun Feb 21 20:48:51 2021

@author: Usuario
"""
import serial
import time

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
    #    self.ConfigurarMonocromador()
        self.posicion = 0    # FALTA CALIBRAR
        
    #def ConfigurarMonocromador(self):
    
    def Mover(self, LongitudDeOnda_Step): 
        comando = '#MRL\r1\r' + str(LongitudDeOnda_Step) + '\r'
        self.address.write(comando.encode())
        self.posicion = LongitudDeOnda_Step
        time.sleep(self.CalcularTiempoSleep(LongitudDeOnda_Step))
        
    def CalcularTiempoSleep(self, LongitudDeOnda_Step):
        TiempoMonocromador = abs(LongitudDeOnda_Step-self.posicion)*0.00625 # Hay que medirlo
        return TiempoMonocromador
    
    
#%%%

monoBis = serial.Serial(
                port = 'COM4',
                baudrate = 9600,
                bytesize = 8,
                stopbits = 1,
                parity = 'N',
                timeout = 1,
                xonxoff = False,
                rtscts = False,
                dsrdtr = False)

#INICIALIZAR y mandar a 400nm. Leer velocidad