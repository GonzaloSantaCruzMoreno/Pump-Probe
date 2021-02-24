# -*- coding: utf-8 -*-
"""
Created on Sun Feb 21 20:48:51 2021

@author: Usuario
"""
import serial
import time

class Monocromador():
    def __init__(self):
        self.address = serial.Serial(
                port = 'COM3',
                baudrate = 9600,
                bytesize = 8,
                stopbits = 1,
                parity = 'N',
                timeout = 1,
                xonxoff = False,
                rtscts = False,
                dsrdtr = False)
        self.posicion = -87
        self.velocidadNmPorSegundo = 9
        self.ConfigurarMonocromador()

        
    def ConfigurarMonocromador(self):
        comando = '#SLM\r3\r'
        self.address.write(comando.encode())
        time.sleep(1)
        self.Mover(400)
    
    def Mover(self, LongitudDeOnda_nm): 
        comando = '#MCL\r3\r' + str(LongitudDeOnda_nm) + '\r' #EN EL PROGRAMA INGRESAR LA LONGITUD DE ONDA CON .
        self.address.write(comando.encode())
        self.posicion = LongitudDeOnda_nm
        time.sleep(self.CalcularTiempoSleep(LongitudDeOnda_nm))
        
    def CalcularTiempoSleep(self, LongitudDeOnda_nm):
        TiempoMonocromador = 0
        if (LongitudDeOnda_nm-self.posicion) == 0:
            time.sleep(1)
        else:
            TiempoMonocromador = abs(LongitudDeOnda_nm-self.posicion)/(self.velocidadNmPorSegundo) # Hay que medirlo
        return TiempoMonocromador
    
mono = Monocromador()
    
    
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

#%%%

for i in range (1,80,1):
    mono.Mover(425+(i*25)/400)