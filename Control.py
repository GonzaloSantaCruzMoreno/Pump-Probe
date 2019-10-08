# -*- coding: utf-8 -*-
"""
Created on Fri Sep 27 18:27:54 2019

@author: LEC
"""

import serial
import pyvisa
import time
import csv
import pandas

def InicializarSMC():  #Buscar los instrumentos en los puertos
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

def InicializarMonocromador():
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

def InicializarLockIn():
    rm = pyvisa.ResourceManager()
    LockIn = rm.open_resource('GPIB0::11::INSTR')

def InicializarOsciloscopio():
    
    
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


def ConfigurarSMC():

def ConfigurarMonocromador():

def ConfigurarLockIn():
    LockIn.write("OUTX1") #Setea en GPIB=1 o RSR232=0
    LockIn.write("FMOD0") #Setea el Lock In con fuente externa de modulacion---> interna=1
    LockIn.write("RSLP1") #Setea Slope TTL up ---> Sin=0, TTLdown=2
    LockIn.write("ISRC0") #Setea la inpunt configuration---->0=A, 1=a-b, 2,3=I en distintas escalas
    LockIn.write("IGND1") #Setea ground=1 o float=0
    LockIn.write("ICPL0") #Setea Coupling en AC=0 o DC=1
    LockIn.write("ILIN3") #Todos los filtros activados
    LockIn.write("RMOD0") #Reserva dinamica 0=HR, 1=Normal, 2=LN
    LockIn.write("OFSL0") #Setea Low Pass Filter Slope en 0=6, 1=12, 2=18 y 3=24 DB/octava
    LockIn.write("SYNC0") #Synchronous Filter off=0 or on below 200hz=1
    LockIn.write("OVRM1") #Setea Remote Control Override en on=1, off=0
    LockIn.write("LOCL0") #Setea control en Local=0, Remote=1, Remote Lockout=2


def ConfigurarOsciloscopio():

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
def CalcularTiempoDeIntegracion(NumeroDeConstantesDeTiempo):
    TiempoDeIntegracion = 0
    a = LockIn.query("OFLT?")
    a = a.replace('\n','')
    a = int(a)
    if (a % 2) == 0:
        TiempoDeIntegracion = 10*(10^(-6))*(10^(a/2))
    else:
        TiempoDeIntegracion = 30*(10^(-6))*(10^((a-1)/2))
    TiempoDeIntegracionTotal = TiempoDeIntegracion*NumeroDeConstantesDeTiempo
    return TiempoDeIntegracionTotal
    
def MedicionCompleta(NombreArchivo,NumeroDeConstantesDeTiempo,VectorLongitudDeOndaIncial_Stp,VectorLongitudDeOndaFinal_Stp,VectorPasoLongitudDeOnda_Stp,VectorPosicionInicialSMC_stp,VectorPosicionFinalSMC_Stp,VectorPasoSMC_Stp): #Pedirle al usuario el nombre del archivo en la interfaz grafica
    TiempoDeIntegracionTotal = CalcularTiempoDeIntegracion(NumeroDeConstantesDeTiempo)
    with open(nombreArchivo, 'w') as csvfile: #
        filewriter = csv.writer(csvfile, delimiter=',')
        filewriter.writerow(['X', 'Y', 'R', 'O','FREF','PLATAFORMA','LAMBDA','DC'])
    for i in range(0,len(VectorLongitudDeOndaInicial_Stp))
        BarridoCompleto(NombreArchivo,TiempoDeIntegracionTotal,VectorLongitudDeOndaInicial_Stp[i],VectorLongitudDeOndaFinal_Stp[i],VectorPasoLongitudDeOnda_Stp[i],VectorPosicionInicialSMC_Stp,VectorPosicionFinalSMC_Stp,VectorPasoSMC_Stp)
#Setear posición y configuración del Monocromador

def BarridoCompleto(NombreArchivo,TiempoDeIntegracionTotal,LongitudDeOndaInicial_Stp,LongitudDeOndaFinal_Stp,PasoLongitudDeOnda_Stp,VectorPosicionInicialSMC_Stp,VectorPosicionFinalSMC_Stp,VectorPasoSMC_stp)
    MoverMonocromador(LongitudDeOndaInicial_Stp)
    for i in range(LongitudDeOndaInicial_Stp,LongitudDeOndaFinal_Stp,PasoLongitudDeOnda_Stp):
        MoverSMC(VectorPosicionInicialSMC_Stp[0])
        Adquisicion(NombreArchivo,TiempoDeIntegracionTotal)
        BarridoSMC(NombreArchivo,TiempoDeIntegracionTotal,VectorPosicionInicialSMC_Stp,VectorPosicionFinalSMC_Stp,VectorPasoSMC_stp)
        MoverMonocromador(PasoLongitudDeOnda_Stp+PosicionMonocromador)

def BarridoSMC(NombreArchivo,TiempoDeIntegracionTotal,VectorPosicionInicialSMC_Stp,VectorPosicionFinalSMC_Stp,VectorPasoSMC_stp):
    for i in range(0,len(VectorPosicionInicialSMC_Stp)):
        for j in range(VectorPosicionInicialSMC_Stp[i],VectorPosicionFinalSMC_Stp[i],VectorPasoSMC_Stp[i]):
            MoverSMC(VectorPasoSMC_Stp[i]+PosicionSMC)
            Adquisicion(NombreArchivo,TiempoDeIntegracionTotal)
            
def MoverMonocromador(LongitudDeOnda_Stp): 
    comando1 = '#MRL\r1\r' + str(LongitudDeOnda_Stp) + '\r'
    Mono.write(comando1.encode())
    PosicionMonocromador = LongitudDeOnda_Stp
    time.sleep(CalcularTiempoSleepMonocromador(LongitudDeOnda_Stp))
    
def MoverSMC(PosicionSMC_Stp): # Configurar Velocidad
    comando2 = '1PA' + str(PosicionSMC_Stp) + '\r\n'
    SMC.write(comando2.encode())
    PosicionSMC = PosicionSMC_Stp
    time.sleep(CalcularTiempoSleepSMC(PosicionSMC_Stp))
    
def CalcularTiempoSleepMonocromador(LongitudDeOnda_Stp):
    TiempoMonocromador = abs(LongitudDeOnda_Stp-PosicionMonocromador)*0.00625 # Hay que medirlo
    return TiempoMonocromador

def CalcularTiempoSleepSMC(PosicionSMC_Stp):
    TiempoSMC = abs(PosicionSMC_Stp-PosicionSMC)*0.5 # Hay que medirlo
    return TiempoSMC

def Adquisicion(NombreArchivo,TiempoDeIntegracionTotal):
    with open(NombreArchivo, 'a') as csvfile:
        filewriter = csv.writer(csvfile, delimiter=',')
        time.sleep(TiempoDeIntegracionTotal)
        a = LockIn.query("SNAP?1,2{,3,4,9}")
        a = a.replace('\n','')
        #VoltajeDC = Osciloscopio.query()
        a = a + ',' + str(PosicionSMC) + ',' + str(PosicionMonocromador) + ',' + VoltajeDC
        b = a.split(',')
        filewriter.writerow(b)
        

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#CONDICIONES INICIALES

VectorLongitudDeOndaInicial_Stp = [400,500,700]
VectorLongitudDeOndaFinal_Stp = [500,700,1000]
VectorPasoLongitudDeOnda_Stp = [5,10,15]

VectorPosicionInicialSMC_Stp = [5000,15000]
VectorPosicionFinalSMC_Stp = [15000,40000]
VectorPasoSMC_Stp = [1000,1000]

#POSICIONES

PosicionMonocromador = 0
PosicionSMC = 0

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

PosicionInicialSMC_Stp = 5000 # stp 0.1um
PosicionFinalSMC_Stp = 15000 # Stp 0.1um

PosicionInicialSMC = 5000/10000 # mm
PosicionFinalSMC = 15000/10000 # mm

PasoSMC_Stp = 1000 # Stp 0.1um
PasoSMC = 1000/10000 # mm

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
        filewriter = csv.writer(csvfile, delimiter=',')
        for i in range(1,20):
            a = LockIn.query("SNAP?1,2{,3,4}")
            b = a.replace('\n','')
            filewriter.writerow([b])
            time.sleep(1)


    

