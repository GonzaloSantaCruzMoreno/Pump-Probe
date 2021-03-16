# -*- coding: utf-8 -*-
"""
Created on Sat Mar 13 21:02:40 2021

@author: Usuario
"""

import serial
import pyvisa
import time
import csv
import tkinter as tk
from tkinter import font as tkfont
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.axes_grid1 import make_axes_locatable
import threading as th

global t


#%%%%%%

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
            while lectura != '\n' and lectura != '\x05': 
                time.sleep(1)
                lectura = self.address.read()
                print(lectura)
                lectura = lectura.decode('windows-1252')
                print(lectura)
                lecturaTotal = lecturaTotal + lectura
            valor = lecturaTotal.find('32')
            time.sleep(2)
            self.address.write(b'1TS\r\n')
    def Mover(self, PosicionSMC_mm): 
        comando = '1PA' + str(PosicionSMC_mm) + '\r\n'
        self.address.write(comando.encode())
        time.sleep(self.CalcularTiempoSleep(PosicionSMC_mm))
        PosicionSMC_mm = round(PosicionSMC_mm, 6)
        self.posicion = PosicionSMC_mm
    def CalcularTiempoSleep(self, PosicionSMC_mm):
        TiempoSMC = 0
        if (PosicionSMC_mm-self.posicion) == 0:
            time.sleep(0.5)
        else:
            TiempoSMC = abs(PosicionSMC_mm-self.posicion)/self.velocidadMmPorSegundo + 1
        return TiempoSMC
        
#%%%
        
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
        self.velocidadNmPorSegundo = 9
        self.ConfigurarMonocromador()
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
                lectura = lectura.decode('windows-1252')
                lecturaTotal = lecturaTotal + lectura
                time.sleep(0.8)
            valor = lecturaTotal.find('CL?')
        lecturaSpliteada = lecturaTotal.split('\r')
        lecturaSpliteadaBis = lecturaSpliteada[0].split(' ')
        posicionEnString = lecturaSpliteadaBis[len(lecturaSpliteadaBis)-1]
        if posicionEnString[len(posicionEnString)-3] == '.':
            posicionEnString = posicionEnString.split('.')[0]
        posicionEnNm = float(posicionEnString)
        return posicionEnNm
    def ConfigurarMonocromador(self): # AGREGAR SETEO DE MULT Y OFFSET PARA CAMBIAR DE RED
        comando = '#SLM\r3\r'
        self.address.write(comando.encode())
        time.sleep(5)
        self.Mover(400)
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
        
#%%%
    
class LockIn():
    def __init__(self,puerto):
        rm = pyvisa.ResourceManager()
        comando = 'GPIB0::' + str(puerto) + '::INSTR'
        self.address = rm.open_resource(comando)
        self.ConfigurarLockIn()
        self.puerto = puerto
    def ConfigurarLockIn(self):
        self.address.write("OUTX1") #Setea en GPIB=1 o RSR232=0
        time.sleep(0.2)
        self.address.write("FMOD0") #Setea el Lock In con fuente externa de modulacion---> interna=1
        time.sleep(0.2)
        self.address.write("RSLP1") #Setea Slope TTL up ---> Sin=0, TTLdown=2
        time.sleep(0.2)
        self.address.write("ISRC0") #Setea la inpunt configuration---->0=A, 1=a-b, 2,3=I en distintas escalas
        time.sleep(0.2)
        self.address.write("IGND1") #Setea ground=1 o float=0
        time.sleep(0.2)
        self.address.write("ICPL0") #Setea Coupling en AC=0 o DC=1
        time.sleep(0.2)
        self.address.write("ILIN3") #Todos los filtros activados
        time.sleep(0.2)
        self.address.write("RMOD0") #Reserva dinamica 0=HR, 1=Normal, 2=LN
        time.sleep(0.2)
        self.address.write("OFSL0") #Setea Low Pass Filter Slope en 0=6, 1=12, 2=18 y 3=24 DB/octava
        time.sleep(0.2)
        self.address.write("SYNC0") #Synchronous Filter off=0 or on below 200hz=1
        time.sleep(0.2)
        self.address.write("OVRM1") #Setea Remote Control Override en on=1, off=0
        time.sleep(0.2)
        self.address.write("LOCL0") #Setea control en Local=0, Remote=1, Remote Lockout=2
        time.sleep(0.2)
    def CalcularTiempoDeIntegracion(self, NumeroDeConstantesDeTiempo):
        TiempoDeIntegracion = 0
        a = self.address.query("OFLT?")
        a = a.replace('\n','')
        a = int(a)
        if (a % 2) == 0:
            TiempoDeIntegracion = 10*(10**(-6))*(10**(a/2))
        else:
            TiempoDeIntegracion = 30*(10**(-6))*(10**((a-1)/2))
        self.TiempoDeIntegracionTotal = TiempoDeIntegracion*NumeroDeConstantesDeTiempo
        return self.TiempoDeIntegracionTotal

#%%%        

class Grafico(): 
    def __init__(self, ValoresAGraficar, TipoDeMedicion, ejeX, VectorPosicionInicialSMC_mm = 0, VectorPosicionFinalSMC_mm = 0, VectorPasoSMC_mm = 0, VectorLongitudDeOndaInicial_nm = 0, VectorLongitudDeOndaFinal_nm = 0, VectorPasoMono_nm = 0, longitudDeOndaFija_nm = 0, posicionFijaSMC_mm = 0):
        self.TipoDeMedicion = TipoDeMedicion
        self.ValoresAGraficar = ValoresAGraficar
        self.ejeX = ejeX
        self.x = list()
        self.z = list()
        self.VectorX = 0
        self.VectorY = 0
        self.M1 = 0
        self.M2 = 0
        self.M3 = 0
        self.M4 = 0
        self.y1 = list()
        self.y2 = list()
        self.y3 = list()
        self.y4 = list()   
        self.fig = plt.figure(figsize=(17,13))
        if TipoDeMedicion == 0:
            if ValoresAGraficar[0]==1:
                self.ax1 = self.fig.add_subplot(221)    
                plt.title('X')
                if ejeX == 'Distancia':
                    plt.xlabel('Posición de la plataforma de retardo (mm)')
                else:
                    plt.xlabel('Desfasaje temporal (ps)')
                plt.ylabel('X')
                plt.legend('\u03BB = ' + str(longitudDeOndaFija_nm) + ' nm')
            if ValoresAGraficar[1]==1:
                self.ax2 = self.fig.add_subplot(222)   
                plt.title('Y')
                if ejeX == 'Distancia':
                    plt.xlabel('Posición de la plataforma de retardo (mm)')
                else:
                    plt.xlabel('Desfasaje temporal (ps)')
                plt.ylabel('Y')
                plt.legend('\u03BB = ' + str(longitudDeOndaFija_nm) + ' nm')
            if ValoresAGraficar[2]==1:
                self.ax3 = self.fig.add_subplot(223)   
                plt.title('R')
                if ejeX == 'Distancia':
                    plt.xlabel('Posición de la plataforma de retardo (mm)')
                else:
                    plt.xlabel('Desfasaje temporal (ps)')
                plt.ylabel('R')
                plt.legend('\u03BB = ' + str(longitudDeOndaFija_nm) + ' nm')
            if ValoresAGraficar[3]==1:
                self.ax4 = self.fig.add_subplot(224)   
                plt.title('\u03B8')
                if ejeX == 'Distancia':
                    plt.xlabel('Posición de la plataforma de retardo (mm)')
                else:
                    plt.xlabel('Desfasaje temporal (ps)')
                plt.ylabel('\u03B8')       
                plt.legend('\u03BB = ' + str(longitudDeOndaFija_nm) + ' nm')
        if TipoDeMedicion == 1:
            if ValoresAGraficar[0]==1:
                self.ax1 = self.fig.add_subplot(221)    
                plt.title('X')
                plt.xlabel('Longitud de onda (nm)')
                plt.ylabel('X')
                plt.legend('Posición = ' + str(posicionFijaSMC_mm) + ' mm')
            if ValoresAGraficar[1]==1:
                self.ax2 = self.fig.add_subplot(222)   
                plt.title('Y')
                plt.xlabel('Longitud de onda (nm)')
                plt.ylabel('Y')
                plt.legend('Posición = ' + str(posicionFijaSMC_mm) + ' mm')
            if ValoresAGraficar[2]==1:
                self.ax3 = self.fig.add_subplot(223)   
                plt.title('R')
                plt.xlabel('Longitud de onda (nm)')
                plt.ylabel('R')
                plt.legend('Posición = ' + str(posicionFijaSMC_mm) + ' mm')
            if ValoresAGraficar[3]==1:
                self.ax4 = self.fig.add_subplot(224)   
                plt.title('\u03B8')
                plt.xlabel('Longitud de onda (nm)')
                plt.ylabel('\u03B8')                 
                plt.legend('Posición = ' + str(posicionFijaSMC_mm) + ' mm')
        if TipoDeMedicion == 2:   #Para el gráfico 3D; X es el vector de posiciones del SMC e Y del Monocromador.
            if ValoresAGraficar[0]==1:
                self.ax1 = self.fig.add_subplot(221)    
                plt.title('X')
                if ejeX == 'Distancia':
                    plt.xlabel('Posición de la plataforma de retardo (mm)')
                else:
                    plt.xlabel('Desfasaje temporal (ps)')
                plt.ylabel('Longitud de onda (nm)')
            if ValoresAGraficar[1]==1:
                self.ax2 = self.fig.add_subplot(222)   
                plt.title('Y')
                if ejeX == 'Distancia':
                    plt.xlabel('Posición de la plataforma de retardo (mm)')
                else:
                    plt.xlabel('Desfasaje temporal (ps)')
                plt.ylabel('Longitud de onda (nm)')
            if ValoresAGraficar[2]==1:
                self.ax3 = self.fig.add_subplot(223)   
                plt.title('R')
                if ejeX == 'Distancia':
                    plt.xlabel('Posición de la plataforma de retardo (mm)')
                else:
                    plt.xlabel('Desfasaje temporal (ps)')
                plt.ylabel('Longitud de onda (nm)')
            if ValoresAGraficar[3]==1:
                self.ax4 = self.fig.add_subplot(224)   
                plt.title('\u03B8')
                if ejeX == 'Distancia':
                    plt.xlabel('Posición de la plataforma de retardo (mm)')
                else:
                    plt.xlabel('Desfasaje temporal (ps)')
                plt.ylabel('Longitud de onda (nm)') 
            numeroDePasos = 0
            self.VectorX = np.array(VectorPosicionInicialSMC_mm[0])
            for i in range(0,len(VectorPosicionInicialSMC_mm)):
                if i>0 and VectorPosicionInicialSMC_mm[i] != VectorPosicionFinalSMC_mm[i-1]:
                    self.VectorX = np.append(self.VectorX, VectorPosicionInicialSMC_mm[i])
                numeroDePasos = int((VectorPosicionFinalSMC_mm[i]-VectorPosicionInicialSMC_mm[i])/VectorPasoSMC_mm[i])
                for j in range(0,numeroDePasos):
                    self.VectorX = np.append(self.VectorX, round(VectorPosicionInicialSMC_mm[i]+(j+1)*VectorPasoSMC_mm[i],6))
            numeroDePasos = 0
            self.VectorY = np.array(VectorLongitudDeOndaInicial_nm[0])
            for i in range(0,len(VectorLongitudDeOndaInicial_nm)):
                if i>0 and VectorLongitudDeOndaInicial_nm[i] != VectorLongitudDeOndaFinal_nm[i-1]:
                    self.VectorY = np.append(self.VectorY, VectorLongitudDeOndaInicial_nm[i])
                numeroDePasos = int((VectorLongitudDeOndaFinal_nm[i]-VectorLongitudDeOndaInicial_nm[i])/VectorPasoMono_nm[i])
                for j in range(0,numeroDePasos):
                    self.VectorY = np.append(self.VectorY, round(VectorLongitudDeOndaInicial_nm[i]+(j+1)*VectorPasoMono_nm[i],6))
            if ValoresAGraficar[0] == 1:
                self.M1 = np.zeros((len(self.VectorY),len(self.VectorX)))
            if ValoresAGraficar[1] == 1:
                self.M2 = np.zeros((len(self.VectorY),len(self.VectorX)))
            if ValoresAGraficar[2] == 1:
                self.M3 = np.zeros((len(self.VectorY),len(self.VectorX)))
            if ValoresAGraficar[3] == 1:
                self.M4 = np.zeros((len(self.VectorY),len(self.VectorX)))
    def GraficarALambdaFija(self, VectorAGraficar, posicionSMC, posicionMono):
        if self.ejeX == 'Distancia':
            self.x.append(posicionSMC)
        else:
            self.x.append((posicionSMC)*(2/3)*10) # en picosegundos
#            self.x.append((posicionSMC)*(2/3)*(10**(-11))) # en segundos        
        if self.ValoresAGraficar[0]==1:
            self.y1.append(float(VectorAGraficar[0])) 
            self.ax1.plot(self.x,self.y1,'c*')
        if self.ValoresAGraficar[1]==1:
            self.y2.append(float(VectorAGraficar[1]))
            self.ax2.plot(self.x,self.y2,'m*')
        if self.ValoresAGraficar[2]==1:
            self.y3.append(float(VectorAGraficar[2]))
            self.ax3.plot(self.x,self.y3,'y*')
        if self.ValoresAGraficar[3]==1:
            self.y4.append(float(VectorAGraficar[3]))
            self.ax4.plot(self.x,self.y4,'k*')
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()   
    def GraficarAPosicionFija(self, VectorAGraficar, posicionSMC, posicionMono):
        self.x.append(posicionMono)
        if self.ValoresAGraficar[0]==1:
            self.y1.append(float(VectorAGraficar[0])) 
            self.ax1.plot(self.x,self.y1,'c*')
        if self.ValoresAGraficar[1]==1:
            self.y2.append(float(VectorAGraficar[1]))
            self.ax2.plot(self.x,self.y2,'m*')
        if self.ValoresAGraficar[2]==1:
            self.y3.append(float(VectorAGraficar[2]))
            self.ax3.plot(self.x,self.y3,'y*')
        if self.ValoresAGraficar[3]==1:
            self.y4.append(float(VectorAGraficar[3]))
            self.ax4.plot(self.x,self.y4,'k*')
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
    def GraficarCompletamente(self, VectorAGraficar, posicionSMC, posicionMono):
        posicionX = np.where(self.VectorX == posicionSMC)
        posicionY = np.where(self.VectorY == posicionMono)
#        vectorX = self.VectorX*(2/3)*10 # en picosegundos
        if self.ValoresAGraficar[0]==1:
            self.M1[posicionY[0][0],posicionX[0][0]] = float(VectorAGraficar[0]) 
            self.plot1 = self.ax1.contourf(self.VectorX, self.VectorY, self.M1, 20, cmap='RdGy')
#            self.plot1 = self.ax1.contourf(vectorX, self.VectorY, self.M1, 20, cmap='RdGy')
            divider = make_axes_locatable(self.ax1)
            cax = divider.append_axes("right", size="5%", pad=0.05)
            if hasattr(self,'c1'):
                self.c1.remove()
            self.c1 = self.fig.colorbar(self.plot1,cax=cax)
        if self.ValoresAGraficar[1]==1:
            self.M2[posicionY[0][0],posicionX[0][0]] = float(VectorAGraficar[1]) 
            self.plot2 = self.ax2.contourf(self.VectorX, self.VectorY, self.M2, 20, cmap='RdGy')
#            self.plot2 = self.ax2.contourf(vectorX, self.VectorY, self.M2, 20, cmap='RdGy')
            divider = make_axes_locatable(self.ax2)
            cax = divider.append_axes("right", size="5%", pad=0.05)
            if hasattr(self,'c2'):
                self.c2.remove()
            self.c2 = self.fig.colorbar(self.plot2,cax=cax)
        if self.ValoresAGraficar[2]==1:
            self.M3[posicionY[0][0],posicionX[0][0]] = float(VectorAGraficar[2]) 
            self.plot3 = self.ax3.contourf(self.VectorX, self.VectorY, self.M3, 20, cmap='RdGy')
#            self.plot3 = self.ax3.contourf(vectorX, self.VectorY, self.M3, 20, cmap='RdGy')
            divider = make_axes_locatable(self.ax3)
            cax = divider.append_axes("right", size="5%", pad=0.05)
            if hasattr(self,'c3'):
                self.c3.remove()
            self.c3 = self.fig.colorbar(self.plot3,cax=cax)
        if self.ValoresAGraficar[3]==1:
            self.M4[posicionY[0][0],posicionX[0][0]] = float(VectorAGraficar[3]) 
            self.plot4 = self.ax4.contourf(self.VectorX, self.VectorY, self.M4, 20, cmap='RdGy')
#            self.plot4 = self.ax4.contourf(vectorX, self.VectorY, self.M4, 20, cmap='RdGy')
            divider = make_axes_locatable(self.ax4)
            cax = divider.append_axes("right", size="5%", pad=0.05)
            if hasattr(self,'c4'):
                self.c4.remove()
            self.c4 = self.fig.colorbar(self.plot4,cax=cax)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events() 
    def GuardarGrafico(self, nombreArchivo):
        self.fig.savefig(nombreArchivo, dpi=200)
    def Graficar(self, VectorAGraficar, posicionSMC, posicionMono):
        if self.TipoDeMedicion == 0:
            self.GraficarALambdaFija(VectorAGraficar, posicionSMC, posicionMono)
        if self.TipoDeMedicion == 1:
            self.GraficarAPosicionFija(VectorAGraficar, posicionSMC, posicionMono)
        if self.TipoDeMedicion == 2:
            self.GraficarCompletamente(VectorAGraficar, posicionSMC, posicionMono)

#%%%

class Experimento():
    def __init__(self,VectorDePuertos):
        self.smc = SMC('COM'+str(VectorDePuertos[0]))
        self.mono = Monocromador('COM'+str(VectorDePuertos[1]))
        self.lockin = LockIn(VectorDePuertos[2])    
    def MedicionALambdaFija(self,
                            nombreArchivo,
                            numeroDeConstantesDeTiempo,
                            longitudDeOndaFija_nm,
                            VectorPosicionInicialSMC_mm,
                            VectorPosicionFinalSMC_mm,
                            VectorPasoSMC_mm):
        self.nombreArchivo = nombreArchivo
        self.numeroDeConstantesDeTiempo = numeroDeConstantesDeTiempo
        self.lockin.CalcularTiempoDeIntegracion(numeroDeConstantesDeTiempo)
        self.mono.Mover(longitudDeOndaFija_nm)
        for i in range(0,len(VectorPosicionInicialSMC_mm)):
#            if t.do_run == False:
#                return
            self.smc.Mover(VectorPosicionInicialSMC_mm[i])
            if i==0:
                vectorDeStringsDeDatos = self.Adquirir()
                self.grafico.Graficar(vectorDeStringsDeDatos,self.smc.posicion,self.mono.posicion)
                self.GrabarCSV(vectorDeStringsDeDatos)
            if i>0 and VectorPosicionInicialSMC_mm[i] != VectorPosicionFinalSMC_mm[i-1]:
                vectorDeStringsDeDatos = self.Adquirir()
                self.grafico.Graficar(vectorDeStringsDeDatos,self.smc.posicion,self.mono.posicion)
                self.GrabarCSV(vectorDeStringsDeDatos)
            numeroDePasos = abs(int((VectorPosicionFinalSMC_mm[i]-VectorPosicionInicialSMC_mm[i])/VectorPasoSMC_mm[i]))
            for j in range(0,numeroDePasos):
#                if t.do_run == False:
#                    return
                self.smc.Mover(VectorPasoSMC_mm[i]+self.smc.posicion)
                vectorDeStringsDeDatos = self.Adquirir()
                self.grafico.Graficar(vectorDeStringsDeDatos,self.smc.posicion,self.mono.posicion)
                self.GrabarCSV(vectorDeStringsDeDatos)
    def MedicionAPosicionFijaSMC(self,
                            nombreArchivo,
                            numeroDeConstantesDeTiempo,
                            posicionFijaSMC_mm,
                            VectorLongitudDeOndaInicial_nm,
                            VectorLongitudDeOndaFinal_nm,
                            VectorPasoMono_nm):
        self.nombreArchivo = nombreArchivo
        self.numeroDeConstantesDeTiempo = numeroDeConstantesDeTiempo
        self.lockin.CalcularTiempoDeIntegracion(numeroDeConstantesDeTiempo)
        self.smc.Mover(posicionFijaSMC_mm)
        for i in range(0,len(VectorLongitudDeOndaInicial_nm)):
            self.mono.Mover(VectorLongitudDeOndaInicial_nm[i])
            if i==0:
                vectorDeStringsDeDatos = self.Adquirir()
                self.grafico.Graficar(vectorDeStringsDeDatos,self.smc.posicion,self.mono.posicion)
                self.GrabarCSV(vectorDeStringsDeDatos)
            if i>0 and VectorLongitudDeOndaInicial_nm[i] != VectorLongitudDeOndaFinal_nm[i-1]:
                vectorDeStringsDeDatos = self.Adquirir()
                self.grafico.Graficar(vectorDeStringsDeDatos,self.smc.posicion,self.mono.posicion)
                self.GrabarCSV(vectorDeStringsDeDatos)
            numeroDePasos = abs(int((VectorLongitudDeOndaFinal_nm[i]-VectorLongitudDeOndaInicial_nm[i])/VectorPasoMono_nm[i]))
            for j in range(0,numeroDePasos):
                self.mono.Mover(VectorPasoMono_nm[i]+self.mono.posicion)
                vectorDeStringsDeDatos = self.Adquirir()
                self.grafico.Graficar(vectorDeStringsDeDatos,self.smc.posicion,self.mono.posicion)
                self.GrabarCSV(vectorDeStringsDeDatos)
    def GrabarCSV(self, vectorDeStringsDeDatos):
        with open(self.nombreArchivo, 'a') as csvfile:
            filewriter = csv.writer(csvfile, delimiter=',')
            filewriter.writerow(vectorDeStringsDeDatos)
    def Adquirir(self):
        time.sleep(self.lockin.TiempoDeIntegracionTotal)
        a = self.lockin.address.query("SNAP?1,2{,3,4,5,9}") # X,Y,R,THETA,AUX1,FREC
        a = a.replace('\n','')
        a = a + ',' + str(self.smc.posicion) + ',' + str(self.mono.posicion)
        b = a.split(',')
        return b

    def MedicionCompleta(self, 
                         nombreArchivo,
                         numeroDeConstantesDeTiempo,
                         VectorPosicionInicialSMC_mm,
                         VectorPosicionFinalSMC_mm,
                         VectorPasoSMC_mm,
                         VectorLongitudDeOndaInicial_nm,
                         VectorLongitudDeOndaFinal_nm,
                         VectorPasoMono_nm):
        self.nombreArchivo = nombreArchivo
        self.numeroDeConstantesDeTiempo = numeroDeConstantesDeTiempo
        self.lockin.CalcularTiempoDeIntegracion(numeroDeConstantesDeTiempo)
        for i in range(0,len(VectorLongitudDeOndaInicial_nm)):
            self.mono.Mover(VectorLongitudDeOndaInicial_nm[i])
            numeroDePasosMono = abs(int((VectorLongitudDeOndaFinal_nm[i]-VectorLongitudDeOndaInicial_nm[i])/VectorPasoMono_nm[i]))
            for j in range(0,numeroDePasosMono+1):
                for k in range(0,len(VectorPosicionInicialSMC_mm)):
                    self.smc.Mover(VectorPosicionInicialSMC_mm[k])
                    if k==0:
                        vectorDeStringsDeDatos = self.Adquirir()
                        self.grafico.Graficar(vectorDeStringsDeDatos,self.smc.posicion,self.mono.posicion)
                        self.GrabarCSV(vectorDeStringsDeDatos)
                    if k>0 and VectorPosicionInicialSMC_mm[k] != VectorPosicionFinalSMC_mm[k-1]:
                        vectorDeStringsDeDatos = self.Adquirir()
                        self.grafico.Graficar(vectorDeStringsDeDatos,self.smc.posicion,self.mono.posicion)
                        self.GrabarCSV(vectorDeStringsDeDatos)
                    numeroDePasosSMC = abs(int((VectorPosicionFinalSMC_mm[k]-VectorPosicionInicialSMC_mm[k])/VectorPasoSMC_mm[k]))
                    for l in range(0,numeroDePasosSMC):
                        self.smc.Mover(VectorPasoSMC_mm[k]+self.smc.posicion)
                        vectorDeStringsDeDatos = self.Adquirir()
                        self.grafico.Graficar(vectorDeStringsDeDatos,self.smc.posicion,self.mono.posicion)
                        self.GrabarCSV(vectorDeStringsDeDatos)
                if j<numeroDePasosMono:
                    self.mono.Mover(VectorPasoMono_nm[i] + self.mono.posicion)
        
#%%%
       
class Programa(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.fuenteDelTitulo = tkfont.Font(family='Helvetica', size=18, weight="bold", slant="italic")
        self.title('Pump and Probe Software')
        self.geometry('1400x1000')   
        
        contenedor = tk.Frame(self)
        contenedor.pack(side="top", fill="both", expand=True)
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        
        self.ventanas = {}
        for F in (VentanaDeEspera, MenuPrincipal, MedicionALambdaFija, MedicionAPosicionFijaSMC, MedicionCompleta, MedicionManual, SetearPuertos):
            nombreVentana = F.__name__
            ventana = F(pariente=contenedor, controlador=self)
            self.ventanas[nombreVentana] = ventana
            ventana.grid(row=0, column=0, sticky="nsew")
        self.show_frame("VentanaDeEspera")

    def MostrarVentana(self, nombreVentana):
        ventana = self.ventanas[nombreVentana]
        ventana.tkraise()
        
class MenuPrincipal(tk.Frame):
    def __init__(self, pariente, controlador):
        tk.Frame.__init__(self, pariente)
        self.controlador = controlador
        btn1 = tk.Button(self, text="A Lambda Fija", command=lambda: controlador.MostrarVentana('MedicionALambdaFija'))
        btn1.grid(column=2, row=0)
        btn2 = tk.Button(self, text="A Posicion Fija", command=lambda: controlador.MostrarVentana('MedicionAPosicionFija'))
        btn2.grid(column=3, row=0)
        btn3 = tk.Button(self, text="Completa", command=lambda: controlador.MostrarVentana('MedicionCompleta'))
        btn3.grid(column=4, row=0)
        btn4 = tk.Button(self, text="Manual", command=lambda: controlador.MostrarVentana('MedicionManual'))
        btn4.grid(column=5, row=0)
        btn5 = tk.Button(self, text="Setear Puertos", command=lambda: controlador.MostrarVentana('SetearPuertos'))
        btn5.grid(column=1, row=0)
    
class MedicionManual(tk.Frame):
    def __init__(self, pariente, controlador):
        tk.Frame.__init__(self, pariente)
                
        
        labelNumeroDeConstantesDeTiempo = tk.Label(self, text = 'Numero de constantes de tiempo a esperar del Lock In:')
        labelNumeroDeConstantesDeTiempo.grid(column=0, row=0)
        textoNumeroDeConstantesDeTiempo = tk.Entry(self, width=5)
        textoNumeroDeConstantesDeTiempo.grid(column=1, row=0)
        def SetearNumeroDeConstantesDeTiempo():
            comando = int(textoNumeroDeConstantesDeTiempo.get())
            controlador.experimento.lockin.CalcularTiempoDeIntegracion(comando)
        botonSetearNumeroDeConstantesDeTiempo = tk.Button(self, text="Setear", command=SetearNumeroDeConstantesDeTiempo)
        botonSetearNumeroDeConstantesDeTiempo.grid(column=2, row=0)
        
        labelPosicionSMC = tk.Label(self, text = 'Posicion plataforma de retardo en mm. (ej: 5.24)')
        labelPosicionSMC.grid(column=0, row=1)
        textoPosicionSMC = tk.Entry(self, width=5)
        textoPosicionSMC.grid(column=1, row=1)
        def IrALaPosicionSMC():
            comando = float(textoPosicionSMC.get())
            controlador.experimento.smc.Mover(comando)
        botonIrALaPosicionSMC = tk.Button(self, text="Mover", command=IrALaPosicionSMC)
        botonIrALaPosicionSMC.grid(column=2, row=1)
        
        labelPosicionMonocromador = tk.Label(self, text = 'Posicion red de difracción en nm. (ej: 532.7)')
        labelPosicionMonocromador.grid(column=0, row=2)
        textoPosicionMonocromador = tk.Entry(self, width=5)
        textoPosicionMonocromador.grid(column=1, row=2)
        def IrALaPosicionMonocromador():
            comando = float(textoPosicionMonocromador.get())
            controlador.experimento.mono.Mover(comando)
        botonIrALaPosicionMonocromador = tk.Button(self, text="Mover", command=IrALaPosicionMonocromador)
        botonIrALaPosicionMonocromador.grid(column=2, row=2)

        labelX = tk.Label(self, text = 'X')
        labelX.grid(column=0, row=4)
        textoX = tk.Entry(self, width=5)
        textoX.grid(column=0, row=5)
        labelY = tk.Label(self, text = 'Y')
        labelY.grid(column=1, row=4)
        textoY = tk.Entry(self, width=5)
        textoY.grid(column=1, row=5)
        labelR = tk.Label(self, text = 'R')
        labelR.grid(column=2, row=4)
        textoR = tk.Entry(self, width=5)
        textoR.grid(column=2, row=5)
        labelTheta = tk.Label(self, text = '\u03B8')
        labelTheta.grid(column=3, row=4)
        textoTheta = tk.Entry(self, width=5)
        textoTheta.grid(column=3, row=5)
        labelAuxIn = tk.Label(self, text = 'Aux In 1 (Señal DC)')
        labelAuxIn.grid(column=4, row=4)
        textoAuxIn = tk.Entry(self, width=5)
        textoAuxIn.grid(column=4, row=5)
        labelCocienteXConAuxIn = tk.Label(self, text = 'X/Aux In 1')
        labelCocienteXConAuxIn.grid(column=5, row=4)
        textoCocienteXConAuxIn = tk.Entry(self, width=5)
        textoCocienteXConAuxIn.grid(column=5, row=5)
        
        def IniciarMedicion():
            global t
            t = th.Thread(target=Medicion)
            t.do_run = True
            t.start()
        def Medicion():
            while t.do_run == True:
                vectorDeStringsDeDatos = controlador.experimento.Adquirir()
                textoX.delete(0, tk.END)
                textoX.insert(tk.END, vectorDeStringsDeDatos[0])
                textoY.delete(0, tk.END)
                textoY.insert(tk.END, vectorDeStringsDeDatos[1])
                textoR.delete(0, tk.END)
                textoR.insert(tk.END, vectorDeStringsDeDatos[2])
                textoTheta.delete(0, tk.END)
                textoTheta.insert(tk.END, vectorDeStringsDeDatos[3]) 
                textoAuxIn.delete(0, tk.END)
                textoAuxIn.insert(tk.END, vectorDeStringsDeDatos[4]) 
                cociente = 0
                if float(vectorDeStringsDeDatos[4]) != 0:
                    cociente = float(vectorDeStringsDeDatos[0])/float(vectorDeStringsDeDatos[4])
                else:
                    cociente = float('inf')
                textoCocienteXConAuxIn.delete(0, tk.END)
                textoCocienteXConAuxIn.insert(tk.END, str(cociente)) 
        def FrenarMedicion():
            t.do_run = False
        
        botonIniciarMedicion = tk.Button(self, text="Iniciar Medicion", command=IniciarMedicion)
        botonIniciarMedicion.grid(column=1, row=3)
        botonFrenarMedicion = tk.Button(self, text="Frenar Medicion", command=FrenarMedicion)
        botonFrenarMedicion.grid(column=2, row=3)
        botonMenuPrincipal = tk.Button(self, text="Menu", command=lambda: controlador.MostrarVentana('MenuPrincipal'))
        botonMenuPrincipal.grid(column=0, row=7)

class SetearPuertos(tk.Frame):
    def __init__(self, pariente, controlador):
        tk.Frame.__init__(self, pariente)
        labelSMC = tk.Label(self, text = 'Ingrese el número de puerto COM correspondiente al SMC. Ejemplo : 5')
        labelSMC.grid(column=0, row=0)
        textoSMC = tk.Entry(self, width=5)
        textoSMC.grid(column=1, row=0)
        
        labelMono = tk.Label(self, text = 'Ingrese el número de puerto COM correspondiente al Monocromador. Ejemplo : 4')
        labelMono.grid(column=0, row=1)
        textoMono = tk.Entry(self, width=5)
        textoMono.grid(column=1, row=1)
   
        labelLockIn = tk.Label(self, text = 'Ingrese el número de dirección correspondiente al Lock-In. Puede verse en la pantalla del mismo. Ejemplo : 11')
        labelLockIn.grid(column=0, row=2)
        textoLockIn = tk.Entry(self, width=5)
        textoLockIn.grid(column=1, row=2)
        
        def AdquirirPuertoSMC():
            self.puertoSMC = int(textoSMC.get())
            controlador.experimento.smc = SMC(self.puertoSMC)
#            lecturaCorrecta = controlador.experimento.smc.LeerId()
        def AdquirirPuertoSMS():
            self.puertoSMS = int(textoMono.get())
            controlador.experimento.mono = Monocromador(self.puertoSMS) 
#            lecturaCorrecta = controlador.experimento.mono.LeerId()
        def AdquirirPuertoLockIn():
            self.puertoLockIn = int(textoLockIn.get())
            controlador.experimento.lockin = LockIn(self.puertoLockIn)
#            lecturaCorrecta = controlador.experimento.lockin.LeerId()

        botonSetear1 = tk.Button(self, text = 'Setear', command = AdquirirPuertoSMC)
        botonSetear1.grid(column=2,row=0)
        botonSetear2 = tk.Button(self, text = 'Setear', command = AdquirirPuertoSMS)
        botonSetear2.grid(column=2,row=1)
        botonSetear3 = tk.Button(self, text = 'Setear', command = AdquirirPuertoLockIn)
        botonSetear3.grid(column=2,row=2)
        botonMenuPrincipal = tk.Button(self, text = 'Menu', command = lambda: controlador.MostrarVentana('MenuPrincipal'))
        botonMenuPrincipal.grid(column=0, row=3)        


class MedicionALambdaFija(tk.Frame):
    def __init__(self, pariente, controlador):
        tk.Frame.__init__(self, pariente)
        
        labelNombreArchivo = tk.Label(raiz1, text="Ingrese el nombre del archivo con la extensión\n .csv. Por ejemplo: datos2.csv")
        labelNombreArchivo.grid(column=0, row=0)
        textoNombreArchivo = tk.Entry(raiz1,width=15)
        textoNombreArchivo.grid(column=1, row=0)
        
        labelNumeroDeConstantesDeTiempo = tk.Label(raiz1, text="Ingrese el número de constantes de tiempo de integracion\n del Lock-In. Debe ser un número entero positivo.")
        labelNumeroDeConstantesDeTiempo.grid(column=0, row=1)
        textoNumeroDeConstantesDeTiempo = tk.Entry(raiz1,width=15)
        textoNumeroDeConstantesDeTiempo.grid(column=1, row=1)
    
        labelLongitudDeOndaFija = tk.Label(raiz1, text="Ingrese la longitud de onda fija en nanómetros\n a la que desea realizar la medición.")
        labelLongitudDeOndaFija.grid(column=0, row=2)
        textoLongitudDeOndaFija = tk.Entry(raiz1,width=15)
        textoLongitudDeOndaFija.grid(column=1, row=2)
    
        labelNumeroDeSubintervalos = tk.Label(raiz1, text="Ingrese la cantidad de barridos distintos\n en los que desea seccionar el barrido completo.")
        labelNumeroDeSubintervalos.grid(column=0, row=3)
        textoNumeroDeSubintervalos = tk.Entry(raiz1,width=15)
        textoNumeroDeSubintervalos.grid(column=1, row=3)
    
        def SiguienteDeLambdaFija():
            numeroDeSubintervalos = int(textoNumeroDeSubintervalos.get())
            labelTituloInicial = tk.Label(raiz1, text="Ingresar datos en milímetros: desde 0 a 25")
            labelTituloInicial.grid(column=0, row=5)
            labelTituloInicial = tk.Label(raiz1, text="Posicion Inicial")
            labelTituloInicial.grid(column=0, row=6,sticky=tk.E)
            labelTituloFinal = tk.Label(raiz1, text="Posicion Final")
            labelTituloFinal.grid(column=1, row=6)
            labelTituloPaso = tk.Label(raiz1, text="Paso")
            labelTituloPaso.grid(column=2, row=6)
                    
            
            labelTituloConversor = tk.Label(raiz1, text="Conversor de mm a fs")
            labelTituloConversor.grid(column=3, row=0)
            labelmm = tk.Label(raiz1, text="mm")
            labelmm.grid(column=3, row=1)
            labelfs = tk.Label(raiz1, text="fs")
            labelfs.grid(column=5, row=1)
            textomm = tk.Entry(raiz1,width=15)
            textomm.grid(column=3, row=2)
            textofs = tk.Entry(raiz1,width=15)
            textofs.grid(column=5, row=2)
            def ConvertirAfs():
                mm = textomm.get()
                fs = float(mm)*6666.666
                textofs.delete(0, tk.END)
                textofs.insert(tk.END, fs)
            def ConvertirAmm():
                fs = textofs.get()
                mm = float(fs)/6666.666
                textomm.delete(0, tk.END)
                textomm.insert(tk.END, mm)
            botonConvertirAmm = tk.Button(raiz1, text="<-", command=ConvertirAmm)
            botonConvertirAmm.grid(column=4, row=1)
            botonConvertirAfs = tk.Button(raiz1, text="->", command=ConvertirAfs)
            botonConvertirAfs.grid(column=4, row=2)
        
            if numeroDeSubintervalos>=1:
                textoPosicionInicial1 = tk.Entry(raiz1,width=15)
                textoPosicionInicial1.grid(column=0, row=7,sticky=tk.E)
                textoPosicionFinal1 = tk.Entry(raiz1,width=15)
                textoPosicionFinal1.grid(column=1, row=7)
                textoPaso1 = tk.Entry(raiz1,width=15)
                textoPaso1.grid(column=2, row=7)
            if numeroDeSubintervalos>=2:
                textoPosicionInicial2 = tk.Entry(raiz1,width=15)
                textoPosicionInicial2.grid(column=0, row=8,sticky=tk.E)
                textoPosicionFinal2 = tk.Entry(raiz1,width=15)
                textoPosicionFinal2.grid(column=1, row=8)
                textoPaso2 = tk.Entry(raiz1,width=15)
                textoPaso2.grid(column=2, row=8)
            if numeroDeSubintervalos>=3:
                textoPosicionInicial3 = tk.Entry(raiz1,width=15)
                textoPosicionInicial3.grid(column=0, row=9,sticky=tk.E)
                textoPosicionFinal3 = tk.Entry(raiz1,width=15)
                textoPosicionFinal3.grid(column=1, row=9)
                textoPaso3 = tk.Entry(raiz1,width=15)
                textoPaso3.grid(column=2, row=9)
            if numeroDeSubintervalos>=4:
                textoPosicionInicial4 = tk.Entry(raiz1,width=15)
                textoPosicionInicial4.grid(column=0, row=10,sticky=tk.E)
                textoPosicionFinal4 = tk.Entry(raiz1,width=15)
                textoPosicionFinal4.grid(column=1, row=10)
                textoPaso4 = tk.Entry(raiz1,width=15)
                textoPaso4.grid(column=2, row=10)
            if numeroDeSubintervalos>=5:
                textoPosicionInicial5 = tk.Entry(raiz1,width=15)
                textoPosicionInicial5.grid(column=0, row=11,sticky=tk.E)
                textoPosicionFinal5 = tk.Entry(raiz1,width=15)
                textoPosicionFinal5.grid(column=1, row=11)
                textoPaso5 = tk.Entry(raiz1,width=15)
                textoPaso5.grid(column=2, row=11)
            if numeroDeSubintervalos>=6:
                textoPosicionInicial6 = tk.Entry(raiz1,width=15)
                textoPosicionInicial6.grid(column=0, row=12,sticky=tk.E)
                textoPosicionFinal6 = tk.Entry(raiz1,width=15)
                textoPosicionFinal6.grid(column=1, row=12)
                textoPaso6 = tk.Entry(raiz1,width=15)
                textoPaso6.grid(column=2, row=12)
            if numeroDeSubintervalos>=7:
                textoPosicionInicial7 = tk.Entry(raiz1,width=15)
                textoPosicionInicial7.grid(column=0, row=13,sticky=tk.E)
                textoPosicionFinal7 = tk.Entry(raiz1,width=15)
                textoPosicionFinal7.grid(column=1, row=13)
                textoPaso7 = tk.Entry(raiz1,width=15)
                textoPaso7.grid(column=2, row=13)
            if numeroDeSubintervalos>=8:
                textoPosicionInicial8 = tk.Entry(raiz1,width=15)
                textoPosicionInicial8.grid(column=0, row=14,sticky=tk.E)
                textoPosicionFinal8 = tk.Entry(raiz1,width=15)
                textoPosicionFinal8.grid(column=1, row=14)
                textoPaso8 = tk.Entry(raiz1,width=15)
                textoPaso8.grid(column=2, row=14)
            if numeroDeSubintervalos>=9:
                textoPosicionInicial9 = tk.Entry(raiz1,width=15)
                textoPosicionInicial9.grid(column=0, row=15,sticky=tk.E)
                textoPosicionFinal9 = tk.Entry(raiz1,width=15)
                textoPosicionFinal9.grid(column=1, row=15)
                textoPaso9 = tk.Entry(raiz1,width=15)
                textoPaso9.grid(column=2, row=15)
            if numeroDeSubintervalos>=10:
                textoPosicionInicial10 = tk.Entry(raiz1,width=15)
                textoPosicionInicial10.grid(column=0, row=16,sticky=tk.E)
                textoPosicionFinal10 = tk.Entry(raiz1,width=15)
                textoPosicionFinal10.grid(column=1, row=16)
                textoPaso10 = tk.Entry(raiz1,width=15)
                textoPaso10.grid(column=2, row=16)
                
            
            labelGraficos = tk.Label(raiz1, text="Seleccione los valores que desea graficar\n en función del tiempo de retardo:")
            labelGraficos.grid(column=0, row=17)
            
            
            Var1 = tk.IntVar()
            tk.Checkbutton(raiz1, text='X', variable=Var1).grid(column=0,row=18)
            Var2 = tk.IntVar()
            tk.Checkbutton(raiz1, text='Y', variable=Var2).grid(column=0,row=19)
            Var3 = tk.IntVar()
            tk.Checkbutton(raiz1, text='R', variable=Var3).grid(column=0,row=18, sticky=tk.E)
            Var4 = tk.IntVar()
            tk.Checkbutton(raiz1, text='\u03B8', variable=Var4).grid(column=0,row=19, sticky=tk.E)
            

            labelEjeX = tk.Label(raiz1, text="Seleccione la magnitud que desea graficar en el eje X:")
            labelEjeX.grid(column=0, row=20)

            choices = ['Tiempo', 'Distancia']
            variable = tk.StringVar(raiz1)
            variable.set('Tiempo')
            w = tk.OptionMenu(raiz1, variable, *choices)
            w.grid(column=0,row=21)
            def IniciarMedicion():
                nombreArchivo = textoNombreArchivo.get()
                numeroDeConstantesDeTiempo = int(textoNumeroDeConstantesDeTiempo.get())
                longitudDeOndaFija_nm = float(textoLongitudDeOndaFija.get())
                ejeX = variable.get()
                ValoresAGraficar = (Var1.get(),Var2.get(),Var3.get(),Var4.get())
                self.grafico = Grafico(ValoresAGraficar,0,ejeX,longitudDeOndaFija_nm=longitudDeOndaFija_nm)
                self.experimento.grafico = self.grafico
                VectorPosicionInicialSMC_mm = np.zeros(numeroDeSubintervalos)
                VectorPosicionFinalSMC_mm = np.zeros(numeroDeSubintervalos)
                VectorPasoSMC_mm = np.zeros(numeroDeSubintervalos)
                if numeroDeSubintervalos>=1:
                    VectorPosicionInicialSMC_mm[0] = float(textoPosicionInicial1.get())
                    VectorPosicionFinalSMC_mm[0] = float(textoPosicionFinal1.get())
                    VectorPasoSMC_mm[0] = float(textoPaso1.get())
                if numeroDeSubintervalos>=2:
                    VectorPosicionInicialSMC_mm[1] = float(textoPosicionInicial2.get())
                    VectorPosicionFinalSMC_mm[1] = float(textoPosicionFinal2.get())
                    VectorPasoSMC_mm[1] = float(textoPaso2.get())
                if numeroDeSubintervalos>=3:
                    VectorPosicionInicialSMC_mm[2] = float(textoPosicionInicial3.get())
                    VectorPosicionFinalSMC_mm[2] = float(textoPosicionFinal3.get())
                    VectorPasoSMC_mm[2] = float(textoPaso3.get())
                if numeroDeSubintervalos>=4:
                    VectorPosicionInicialSMC_mm[3] = float(textoPosicionInicial4.get())
                    VectorPosicionFinalSMC_mm[3] = float(textoPosicionFinal4.get())
                    VectorPasoSMC_mm[3] = float(textoPaso4.get())
                if numeroDeSubintervalos>=5:
                    VectorPosicionInicialSMC_mm[4] = float(textoPosicionInicial5.get())
                    VectorPosicionFinalSMC_mm[4] = float(textoPosicionFinal5.get())
                    VectorPasoSMC_mm[4] = float(textoPaso5.get())
                if numeroDeSubintervalos>=6:
                    VectorPosicionInicialSMC_mm[5] = float(textoPosicionInicial6.get())
                    VectorPosicionFinalSMC_mm[5] = float(textoPosicionFinal6.get())
                    VectorPasoSMC_mm[5] = float(textoPaso6.get())
                if numeroDeSubintervalos>=7:
                    VectorPosicionInicialSMC_mm[6] = float(textoPosicionInicial7.get())
                    VectorPosicionFinalSMC_mm[6] = float(textoPosicionFinal7.get())
                    VectorPasoSMC_mm[6] = float(textoPaso7.get())
                if numeroDeSubintervalos>=8:
                    VectorPosicionInicialSMC_mm[7] = float(textoPosicionInicial8.get())
                    VectorPosicionFinalSMC_mm[7] = float(textoPosicionFinal8.get())
                    VectorPasoSMC_mm[7] = float(textoPaso8.get())
                if numeroDeSubintervalos>=9:
                    VectorPosicionInicialSMC_mm[8] = float(textoPosicionInicial9.get())
                    VectorPosicionFinalSMC_mm[8] = float(textoPosicionFinal9.get())
                    VectorPasoSMC_mm[8] = float(textoPaso9.get())
                if numeroDeSubintervalos>=10:
                    VectorPosicionInicialSMC_mm[9] = float(textoPosicionInicial10.get())
                    VectorPosicionFinalSMC_mm[9] = float(textoPosicionFinal10.get())
                    VectorPasoSMC_mm[9] = float(textoPaso10.get())
                    
                    
                tiempoDeMedicion = str(self.CalcularTiempoDeMedicionALambdaFija(numeroDeConstantesDeTiempo,longitudDeOndaFija_nm,VectorPosicionInicialSMC_mm,VectorPosicionFinalSMC_mm,VectorPasoSMC_mm))
#                global t 
#                t = th.Thread(target=CorriendoExperimento)
#                t.do_run = True
#                t.start()
                raizMedicion = tk.Tk()
                raizMedicion.title('Pump and Probe Software - Midiendo a Lambda Fija')
                raizMedicion.geometry('1000x1000')   
                labelEstado = tk.Label(raizMedicion, text="Realizando la medicion. Tiempo estimado: " + tiempoDeMedicion + ' segundos')
                labelEstado.grid(column=0, row=0)
                canvas = FigureCanvasTkAgg(self.grafico.fig, master=raizMedicion)
                canvas.get_tk_widget().grid(row=1,column=0)
                canvas.draw()
                raizMedicion.update()
#                def CorriendoExperimento():
                self.experimento.MedicionALambdaFija(nombreArchivo,numeroDeConstantesDeTiempo,longitudDeOndaFija_nm,VectorPosicionInicialSMC_mm,VectorPosicionFinalSMC_mm,VectorPasoSMC_mm)
                nombreGrafico = nombreArchivo.replace('.csv','')
                self.grafico.GuardarGrafico(nombreGrafico)
                labelEstado = tk.Label(raizMedicion, text="Medicion Finalizada. El archivo ha sido guardado con el nombre: " + nombreArchivo)
                labelEstado.grid(column=0, row=2)               
                def Finalizar():
                    raizMedicion.destroy()    
                botonFinalizar = tk.Button(raizMedicion, text="Finalizar", command=Finalizar)
                botonFinalizar.grid(column=1, row=2)
#                def CancelarMedicion():
#                    t.do_run = False
#                    t.join()
#                    raizMedicion.destroy()
#                botonCancelarMedicion = tk.Button(raizMedicion, text="Cancelar", command=CancelarMedicion)
#                botonCancelarMedicion.grid(column=1, row=0)                
                raizMedicion.mainloop()              
            botonIniciarMedicion = tk.Button(raiz1, text="Iniciar Medicion", command=IniciarMedicion)
            botonIniciarMedicion.grid(column=1, row=22)
       
        botonMenuPrincipal = tk.Button(self, text = 'Menu', command = lambda: controlador.MostrarVentana('MenuPrincipal'))
        botonMenuPrincipal.grid(column=0, row=4)
        botonSiguiente = tk.Button(self, text="Siguiente", command=SiguienteDeLambdaFija)
        botonSiguiente.grid(column=1, row=4)
