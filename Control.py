# -*- coding: utf-8 -*-
"""
Created on Fri Sep 27 18:27:54 2019

@author: LEC
"""

import serial
import pyvisa
import time
import csv

SMC = serial.Serial(
        port = 'COM5',
        baudrate = 57600,
        bytesize = 8,
        stopbits = 1,
        parity = 'N',
        timeout = 1,
        xonxoff = False,
        rtscts = False,
        dsrdtr = False)

Mono = serial.Serial(
        port = 'COM4',
        baudrate = 9600,
        bytesize = 8,
        stopbits = 1,
        parity = 'N',
        timeout = 1,
        xonxoff = False,
        rtscts = False,
        dsrdtr = False)

rm = pyvisa.ResourceManager()
LockIn = rm.open_resource('GPIB0::11::INSTR')

#Osci = rm.open_resource('adress')


#Setear posición y configuración del Monocromador


PosicionInicial_Stp = 5000 # stp 0.1um
PosicionFinal_Stp = 15000 # Stp 0.1um

PosicionInicial = 5000/10000 # mm
PosicionFinal = 15000/10000 # mm

PasoTornillo_Stp = 1000 # Stp 0.1um
PasoTornillo = 1000/10000 # mm

Offset_Stp = int(500/0.03125) #nm/step
LongitudDeOndaInicial_Stp = int(400/0.03125) #nm/step
LongitudDeOndaFinal_Stp = int(500/0.03125) #nm/step
StepMonoInicial = LongitudDeOndaInicial_Stp - Offset_Stp # VER OFFSET
PasoMono = int(10/0.03125) #nm/step ----> Deben ser INTEGER, chequear multiplos

comando1 = '#MRL\r1\r' + str(StepMonoInicial) + '\r'
Mono.write(comando1.encode())
time.sleep(15)
comando2 = '1PA' + str(PosicionInicial) + '\r\n'
SMC.write(comando2.encode())
time.sleep(15)

StepActual = StepMonoInicial

for i in range(LongitudDeOndaInicial_Stp,LongitudDeOndaFinal_Stp,PasoMono):
    #LockIn.query()
    #Osci.query()
    #ver como generar archivo o vector o matriz
    time.sleep(5)
    for j in range(PosicionInicial_Stp,PosicionFinal_Stp,PasoTornillo_Stp):
        comando = '1PR' + str(PasoTornillo) + '\r\n'
        SMC.write(comando.encode())
        time.sleep(5)
        #LockIn.query()
        #Osci.query()
        #ver como generar archivo o vector o matriz
    SMC.write(comando2.encode())
    time.sleep(30)
    StepActual = StepActual + PasoMono
    comandoMoverMono = '#MRL\r1\r' + str(StepActual) + '\r'
    Mono.write(comandoMoverMono.encode())
    time.sleep(5)

def CrearArchivo(PosicionTornillo,PosicionMonocromador):
    with open('datos.csv', 'w') as csvfile:
    filewriter = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    filewriter.writerow(['','','X', 'Y', 'R', 'O'])
    for i in range(1,20):
        a = LockIn.query("SNAP?1,2{,3,4}")
        b = a.replace('\n','')
        filewriter.writerow([b])
        time.sleep(1)