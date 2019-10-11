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
from tkinter import *
import numpy as np

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

#def InicializarOsciloscopio():
    
    
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


#def ConfigurarSMC():

#def ConfigurarMonocromador():

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


#def ConfigurarOsciloscopio():

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
PosicionMonocromador = 0
PosicionSMC = 0


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
    for i in range(0,len(VectorLongitudDeOndaInicial_Stp)):
        BarridoCompleto(NombreArchivo,TiempoDeIntegracionTotal,VectorLongitudDeOndaInicial_Stp[i],VectorLongitudDeOndaFinal_Stp[i],VectorPasoLongitudDeOnda_Stp[i],VectorPosicionInicialSMC_Stp,VectorPosicionFinalSMC_Stp,VectorPasoSMC_Stp)
#Setear posición y configuración del Monocromador

def BarridoCompleto(NombreArchivo,TiempoDeIntegracionTotal,LongitudDeOndaInicial_Stp,LongitudDeOndaFinal_Stp,PasoLongitudDeOnda_Stp,VectorPosicionInicialSMC_Stp,VectorPosicionFinalSMC_Stp,VectorPasoSMC_Stp):
    MoverMonocromador(LongitudDeOndaInicial_Stp)
    for i in range(LongitudDeOndaInicial_Stp,LongitudDeOndaFinal_Stp,PasoLongitudDeOnda_Stp):
        MoverSMC(VectorPosicionInicialSMC_Stp[0])
        Adquisicion(NombreArchivo,TiempoDeIntegracionTotal)
        BarridoSMC(NombreArchivo,TiempoDeIntegracionTotal,VectorPosicionInicialSMC_Stp,VectorPosicionFinalSMC_Stp,VectorPasoSMC_Stp)
        MoverMonocromador(PasoLongitudDeOnda_Stp+PosicionMonocromador)

def MedicionALambdaFija(NombreArchivo,numeroDeConstantesDeTiempo,longitudDeOndaFija_Stp,VectorPosicionInicialSMC_Stp,VectorPosicionFinalSMC_Stp,VectorPasoSMC_Stp):
    TiempoDeIntegracionTotal = CalcularTiempoDeIntegracion(NumeroDeConstantesDeTiempo)
    MoverMonocromador(longitudDeOndaFija_Stp)
    MoverSMC(VectorPosicionInicialSMC_Stp[0])
    BarridoSMC(NombreArchivo,TiempoDeIntegracionTotal,VectorPosicionInicialSMC_Stp,VectorPosicionFinalSMC_Stp,VectorPasoSMC_Stp)
    
def BarridoSMC(NombreArchivo,TiempoDeIntegracionTotal,VectorPosicionInicialSMC_Stp,VectorPosicionFinalSMC_Stp,VectorPasoSMC_Stp):
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
        a = a + ',' + str(PosicionSMC) + ',' + str(PosicionMonocromador)# + ',' + VoltajeDC
        b = a.split(',')
        filewriter.writerow(b)
        
def CrearArchivo(PosicionTornillo,PosicionMonocromador):
    with open('datos.csv', 'w') as csvfile:
        filewriter = csv.writer(csvfile, delimiter=',')
        for i in range(1,20):
            a = LockIn.query("SNAP?1,2{,3,4}")
            b = a.replace('\n','')
            filewriter.writerow([b])
            time.sleep(1)

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#CONDICIONES INICIALES

#VectorLongitudDeOndaInicial_Stp = [400,500,700]
#VectorLongitudDeOndaFinal_Stp = [500,700,1000]
#VectorPasoLongitudDeOnda_Stp = [5,10,15]

#VectorPosicionInicialSMC_Stp = [5000,15000]
#VectorPosicionFinalSMC_Stp = [15000,40000]
#VectorPasoSMC_Stp = [1000,1000]

#POSICIONES

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#PosicionInicialSMC_Stp = 5000 # stp 0.1um
#PosicionFinalSMC_Stp = 15000 # Stp 0.1um

#PosicionInicialSMC = 5000/10000 # mm
#PosicionFinalSMC = 15000/10000 # mm

#PasoSMC_Stp = 1000 # Stp 0.1um
#PasoSMC = 1000/10000 # mm

#Offset_Stp = int(500/0.03125) #nm/step
#LongitudDeOndaInicial_Stp = int(400/0.03125) #nm/step
#LongitudDeOndaFinal_Stp = int(500/0.03125) #nm/step
#StepMonoInicial = LongitudDeOndaInicial_Stp - Offset_Stp # VER OFFSET
#PasoMono = int(10/0.03125) #nm/step ----> Deben ser INTEGER, chequear multiplos

#comando1 = '#MRL\r1\r' + str(StepMonoInicial) + '\r'
#Mono.write(comando1.encode())
#time.sleep(15)
#comando2 = '1PA' + str(PosicionInicial) + '\r\n'
#SMC.write(comando2.encode())
#time.sleep(15)

#StepActual = StepMonoInicial


#for i in range(LongitudDeOndaInicial_Stp,LongitudDeOndaFinal_Stp,PasoMono):

    #LockIn.query()
    #Osci.query()
    #ver como generar archivo o vector o matriz
#    time.sleep(5)
#    for j in range(PosicionInicial_Stp,PosicionFinal_Stp,PasoTornillo_Stp):
#        comando = '1PR' + str(PasoTornillo) + '\r\n'
#        SMC.write(comando.encode())
#        time.sleep(5)
        #LockIn.query()
        #Osci.query()
        #ver como generar archivo o vector o matriz
#    SMC.write(comando2.encode())
#    time.sleep(30)
#    StepActual = StepActual + PasoMono
#    comandoMoverMono = '#MRL\r1\r' + str(StepActual) + '\r'
#    Mono.write(comandoMoverMono.encode())
#    time.sleep(5)


#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


def Programa():
    raiz = Tk()
    raiz.title('ventana de prueba')
    raiz.geometry('1000x800')
    btn1 = Button(raiz, text="A Lambda Fija", command=ProgramaMedicionALambdaFija)
    btn1.grid(column=1, row=0)
    btn2 = Button(raiz, text="A Posicion Fija", command=ProgramaMedicionAPosicionFija)
    btn2.grid(column=2, row=0)
    btn3 = Button(raiz, text="Completa", command=ProgramaMedicionCompleta)
    btn3.grid(column=3, row=0)
    raiz.mainloop()

def ProgramaMedicionALambdaFija():
    raiz1 = Tk()
    raiz1.title('Medicion a Lambda Fija')
    raiz1.geometry('1000x800')
    
    labelNombreArchivo = Label(raiz1, text="Ingrese el nombre del archivo con la extención .csv. Por ejemplo: datos2.csv")
    labelNombreArchivo.grid(column=0, row=0)
    textoNombreArchivo = Entry(raiz1,width=15)
    textoNombreArchivo.grid(column=1, row=0)
    
    labelNumeroDeConstantesDeTiempo = Label(raiz1, text="Ingrese el número de constantes de tiempo de integracion del Lock-In. Debe ser un número entero positivo.")
    labelNumeroDeConstantesDeTiempo.grid(column=0, row=1)
    textoNumeroDeConstantesDeTiempo = Entry(raiz1,width=15)
    textoNumeroDeConstantesDeTiempo.grid(column=1, row=1)
    
    labelLongitudDeOndaFija = Label(raiz1, text="Ingrese la longitud de onda fija en nanómetros a la que desea realizar la medición.")
    labelLongitudDeOndaFija.grid(column=0, row=2)
    textoLongitudDeOndaFija = Entry(raiz1,width=15)
    textoLongitudDeOndaFija.grid(column=1, row=2)
    
    labelNumeroDeSubintervalos = Label(raiz1, text="Ingrese la cantidad de barridos distintos en los que desea seccionar el barrido completo.")
    labelNumeroDeSubintervalos.grid(column=0, row=3)
    textoNumeroDeSubintervalos = Entry(raiz1,width=15)
    textoNumeroDeSubintervalos.grid(column=1, row=3)
    
    def SiguienteDeLambdaFija():
        numeroDeSubintervalos = int(textoNumeroDeSubintervalos.get())
        labelTituloInicial = Label(raiz1, text="Ingresar en milímetros: desde 0 a 25")
        labelTituloInicial.grid(column=0, row=5)
        labelTituloInicial = Label(raiz1, text="Posicion Inicial")
        labelTituloInicial.grid(column=1, row=5)
        labelTituloFinal = Label(raiz1, text="Posicion Final")
        labelTituloFinal.grid(column=2, row=5)
        labelTituloPaso = Label(raiz1, text="Paso")
        labelTituloPaso.grid(column=3, row=5)
        
        if numeroDeSubintervalos>=1:
            textoPosicionInicial1 = Entry(raiz1,width=15)
            textoPosicionInicial1.grid(column=1, row=6)
            textoPosicionFinal1 = Entry(raiz1,width=15)
            textoPosicionFinal1.grid(column=2, row=6)
            textoPaso1 = Entry(raiz1,width=15)
            textoPaso1.grid(column=3, row=6)
        if numeroDeSubintervalos>=2:
            textoPosicionInicial2 = Entry(raiz1,width=15)
            textoPosicionInicial2.grid(column=1, row=7)
            textoPosicionFinal2 = Entry(raiz1,width=15)
            textoPosicionFinal2.grid(column=2, row=7)
            textoPaso2 = Entry(raiz1,width=15)
            textoPaso2.grid(column=3, row=7)
        if numeroDeSubintervalos>=3:
            textoPosicionInicial3 = Entry(raiz1,width=15)
            textoPosicionInicial3.grid(column=1, row=8)
            textoPosicionFinal3 = Entry(raiz1,width=15)
            textoPosicionFinal3.grid(column=2, row=8)
            textoPaso3 = Entry(raiz1,width=15)
            textoPaso3.grid(column=3, row=8)
        if numeroDeSubintervalos>=4:
            textoPosicionInicial4 = Entry(raiz1,width=15)
            textoPosicionInicial4.grid(column=1, row=9)
            textoPosicionFinal4 = Entry(raiz1,width=15)
            textoPosicionFinal4.grid(column=2, row=9)
            textoPaso4 = Entry(raiz1,width=15)
            textoPaso4.grid(column=3, row=9)
        if numeroDeSubintervalos>=5:
            textoPosicionInicial5 = Entry(raiz1,width=15)
            textoPosicionInicial5.grid(column=1, row=10)
            textoPosicionFinal5 = Entry(raiz1,width=15)
            textoPosicionFinal5.grid(column=2, row=10)
            textoPaso5 = Entry(raiz1,width=15)
            textoPaso5.grid(column=3, row=10)
        
        nombreArchivo = textoNombreArchivo.get()
        numeroDeConstantesDeTiempo = int(textoNumeroDeConstantesDeTiempo.get())
        longitudDeOndaFija_Stp = int(float(textoLongitudDeOndaFija.get())/0.03125)
        
        def IniciarMedicion():
            VectorPosicionInicialSMC_Stp = np.zeros(numeroDeSubintervalos)
            VectorPosicionFinalSMC_Stp = np.zeros(numeroDeSubintervalos)
            VectorPasoSMC_Stp = np.zeros(numeroDeSubintervalos)
            if numeroDeSubintervalos>=1:
                VectorPosicionInicialSMC_Stp[0] = int(float(textoPosicionInicial1.get())*10000)
                VectorPosicionFinalSMC_Stp[0] = int(float(textoPosicionFinal1.get())*10000)
                VectorPasoSMC_Stp[0] = int(float(textoPaso1.get())*10000)
            if numeroDeSubintervalos>=2:
                VectorPosicionInicialSMC_Stp[1] = int(float(textoPosicionInicial2.get())*10000)
                VectorPosicionFinalSMC_Stp[1] = int(float(textoPosicionFinal2.get())*10000)
                VectorPasoSMC_Stp[1] = int(float(textoPaso2.get())*10000)
            if numeroDeSubintervalos>=3:
                VectorPosicionInicialSMC_Stp[2] = int(float(textoPosicionInicial3.get())*10000)
                VectorPosicionFinalSMC_Stp[2] = int(float(textoPosicionFinal3.get())*10000)
                VectorPasoSMC_Stp[2] = int(float(textoPaso3.get())*10000)
            if numeroDeSubintervalos>=4:
                VectorPosicionInicialSMC_Stp[3] = int(float(textoPosicionInicial4.get())*10000)
                VectorPosicionFinalSMC_Stp[3] = int(float(textoPosicionFinal4.get())*10000)
                VectorPasoSMC_Stp[3] = int(float(textoPaso4.get())*10000)
            if numeroDeSubintervalos>=5:
                VectorPosicionInicialSMC_Stp[4] = int(float(textoPosicionInicial5.get())*10000)
                VectorPosicionFinalSMC_Stp[4] = int(float(textoPosicionFinal5.get())*10000)
                VectorPasoSMC_Stp[4] = int(float(textoPaso5.get())*10000)
            MedicionALambdaFija(nombreArchivo,numeroDeConstantesDeTiempo,longitudDeOndaFija_Stp,VectorPosicionInicialSMC_Stp,VectorPosicionFinalSMC_Stp,VectorPasoSMC_Stp)
        
        botonIniciarMedicion = Button(raiz1, text="Iniciar Medicion", command=IniciarMedicion)
        botonIniciarMedicion.grid(column=3, row=11)
       
            
    botonSiguiente = Button(raiz1, text="Siguiente", command=SiguienteDeLambdaFija)
    botonSiguiente.grid(column=1, row=4)
    raiz.mainloop()
    

    
def ProgramaMedicionAPosicionFija():
    raiz2 = Tk()
    raiz2.title('Medicion a Posicion Fija')
    raiz2.geometry('1000x800')
    raiz.mainloop()

def ProgramaMedicionCompleta():
    raiz3 = Tk()
    raiz3.title('Medicion Completa')    
    raiz3.geometry('1000x800')
    raiz.mainloop()

 



 



 




