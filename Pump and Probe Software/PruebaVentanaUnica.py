# -*- coding: utf-8 -*-
"""
Created on Wed Mar 17 17:38:20 2021

@author: Usuario
"""

import serial
import pyvisa
import time
import csv
import tkinter as tk
import tkinter.font as font
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.axes_grid1 import make_axes_locatable
import threading as th

global t

#%%%%%%

class SMC():
    def __init__(self):
        self.posicion = 0 # Solo para inicializar la variable. Al configurar se lee la posición.
        self.velocidadMmPorSegundo = 0.16
    def AsignarPuerto(self, puerto):
#        self.address = serial.Serial(
#                port = puerto,
#                baudrate = 57600,
#                bytesize = 8,
#                stopbits = 1,
#                parity = 'N',
#                timeout = 1,
#                xonxoff = False,
#                rtscts = False,
#                dsrdtr = False)
        self.puerto = puerto
    def Configurar(self):    
        valor = -1
        estadosReady = ['32','33','34']
        while valor == -1:
            time.sleep(1)
            self.address.write(b'1TS\r\n')
            time.sleep(2)
            lectura = 'a'
            lecturaTotal = ''
            while lectura != '\n' and lectura != '': 
                time.sleep(1)
                lectura = self.address.read()
                print(lectura)
                lectura = lectura.decode('windows-1252')
                print(lectura)
                lecturaTotal = lecturaTotal + lectura
            if 'TS' in lecturaTotal:
                valor = 1
                if any(x in lecturaTotal for x in estadosReady):
                    self.posicion = abs(round(self.LeerPosicion(),5))
                    return
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
        valor = -1
        while valor == -1:
            time.sleep(1)
            self.address.write(b'1TS\r\n')
            time.sleep(2)
            lectura = 'a'
            lecturaTotal = ''
            while lectura != '\n' and lectura != '': 
                time.sleep(1)
                lectura = self.address.read()
                print(lectura)
                lectura = lectura.decode('windows-1252')
                print(lectura)
                lecturaTotal = lecturaTotal + lectura
            valor = lecturaTotal.find('32')
        self.posicion = 0
    def LeerPosicion(self):
        self.address.write(b'1TH\r\n')
        time.sleep(1)
        valor = -1
        while valor == -1:
            time.sleep(2)
            lectura = self.LeerBuffer()
            if 'TH' in lectura:
                a = lectura.split('\r')
                b = a[0]
                c = b.split('TH')
                d = c[len(c)-1]
                return float(d)
            self.address.write(b'1TH\r\n')
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
    def LeerBuffer(self):
        lectura = 'a'
        lecturaTotal = ''
        while lectura != '\n' and lectura != '': 
            time.sleep(0.3)
            lectura = self.address.read()
            print(lectura)
            lectura = lectura.decode('windows-1252')
            lecturaTotal = lecturaTotal + lectura
        return lecturaTotal        
    def Identificar(self):
        b = False
        return b
    def Calibrar(self):
        return
#%%%
        
class SMS():
    def __init__(self):
        self.velocidadNmPorSegundo = 9
    def AsignarPuerto(self, puerto):
#        self.address = serial.Serial(
#                port = puerto,
#                baudrate = 9600,
#                bytesize = 8,
#                stopbits = 1,
#                parity = 'N',
#                timeout = 1,
#                xonxoff = False,
#                rtscts = False,
#                dsrdtr = False)
        self.puerto = puerto        
    def LeerPosicion(self):
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
                lectura = lectura.decode('utf-8')
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
    def Configurar(self): # AGREGAR SETEO DE MULT Y OFFSET PARA CAMBIAR DE RED
        comando = '#SLM\r3\r'
        self.address.write(comando.encode())
        time.sleep(3)
        self.posicion = self.LeerPosicion()
        if self.posicion < 400:
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
            TiempoMonocromador = abs(LongitudDeOnda_nm-self.posicion)/(self.velocidadNmPorSegundo) + 5
        return TiempoMonocromador
    def Identificar(self):
        b = False
        return b
    def Calibrar(self):
        return
#%%%
    
class LockIn():
    def AsignarPuerto(self, puerto):
        rm = pyvisa.ResourceManager()
        comando = 'GPIB0::' + puerto + '::INSTR'
#        self.address = rm.open_resource(comando)
        self.puerto = puerto
        
    def Configurar(self):
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
    def Identificar(self):
        b = False
        return b

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
        self.fig = plt.figure(figsize=(12,10))
        if TipoDeMedicion == 0:
            if ValoresAGraficar[0]==1:
                self.ax1 = self.fig.add_subplot(221)    
                plt.title('\u03BB = ' + str(longitudDeOndaFija_nm) + ' nm')
                if ejeX == 'Distancia':
                    plt.xlabel('Posición de la plataforma de retardo (mm)')
                else:
                    plt.xlabel('Desfasaje temporal (ps)')
                plt.ylabel('X')
            if ValoresAGraficar[1]==1:
                self.ax2 = self.fig.add_subplot(222)   
                plt.title('\u03BB = ' + str(longitudDeOndaFija_nm) + ' nm')
                if ejeX == 'Distancia':
                    plt.xlabel('Posición de la plataforma de retardo (mm)')
                else:
                    plt.xlabel('Desfasaje temporal (ps)')
                plt.ylabel('Y')
                plt.legend('\u03BB = ' + str(longitudDeOndaFija_nm) + ' nm')
            if ValoresAGraficar[2]==1:
                self.ax3 = self.fig.add_subplot(223)   
                plt.title('\u03BB = ' + str(longitudDeOndaFija_nm) + ' nm')
                if ejeX == 'Distancia':
                    plt.xlabel('Posición de la plataforma de retardo (mm)')
                else:
                    plt.xlabel('Desfasaje temporal (ps)')
                plt.ylabel('R')
                plt.legend('\u03BB = ' + str(longitudDeOndaFija_nm) + ' nm')
            if ValoresAGraficar[3]==1:
                self.ax4 = self.fig.add_subplot(224)   
                plt.title('\u03BB = ' + str(longitudDeOndaFija_nm) + ' nm')
                if ejeX == 'Distancia':
                    plt.xlabel('Posición de la plataforma de retardo (mm)')
                else:
                    plt.xlabel('Desfasaje temporal (ps)')
                plt.ylabel('\u03B8')       
                plt.legend('\u03BB = ' + str(longitudDeOndaFija_nm) + ' nm')
        if TipoDeMedicion == 1:
            if ValoresAGraficar[0]==1:
                self.ax1 = self.fig.add_subplot(221)    
                plt.title('Posición = ' + str(posicionFijaSMC_mm) + ' mm')
                plt.xlabel('Longitud de onda (nm)')
                plt.ylabel('X')
            if ValoresAGraficar[1]==1:
                self.ax2 = self.fig.add_subplot(222)   
                plt.title('Posición = ' + str(posicionFijaSMC_mm) + ' mm')
                plt.xlabel('Longitud de onda (nm)')
                plt.ylabel('Y')
            if ValoresAGraficar[2]==1:
                self.ax3 = self.fig.add_subplot(223)   
                plt.title('Posición = ' + str(posicionFijaSMC_mm) + ' mm')
                plt.xlabel('Longitud de onda (nm)')
                plt.ylabel('R')
            if ValoresAGraficar[3]==1:
                self.ax4 = self.fig.add_subplot(224)   
                plt.title('Posición = ' + str(posicionFijaSMC_mm) + ' mm')
                plt.xlabel('Longitud de onda (nm)')
                plt.ylabel('\u03B8')                 
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
    def __init__(self):
        self.smc = SMC()
        self.mono = SMS()
        self.lockin = LockIn()
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
        for i in range(0,len(VectorPosicionInicialSMC_mm)):
#            if t.do_run == False:
#                return
            self.smc.Mover(VectorPosicionInicialSMC_mm[i])
            if i==0:
                self.AdquirirGraficarYGrabarCSV()
            if i>0 and VectorPosicionInicialSMC_mm[i] != VectorPosicionFinalSMC_mm[i-1]:
                self.AdquirirGraficarYGrabarCSV()
            numeroDePasos = abs(int((VectorPosicionFinalSMC_mm[i]-VectorPosicionInicialSMC_mm[i])/VectorPasoSMC_mm[i]))
            for j in range(0,numeroDePasos):
#                if t.do_run == False:
#                    return
                self.smc.Mover(VectorPasoSMC_mm[i]+self.smc.posicion)
                self.AdquirirGraficarYGrabarCSV()
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
        for i in range(0,len(VectorLongitudDeOndaInicial_nm)):
            self.mono.Mover(VectorLongitudDeOndaInicial_nm[i])
            if i==0:
                self.AdquirirGraficarYGrabarCSV()
            if i>0 and VectorLongitudDeOndaInicial_nm[i] != VectorLongitudDeOndaFinal_nm[i-1]:
                self.AdquirirGraficarYGrabarCSV()
            numeroDePasos = abs(int((VectorLongitudDeOndaFinal_nm[i]-VectorLongitudDeOndaInicial_nm[i])/VectorPasoMono_nm[i]))
            for j in range(0,numeroDePasos):
                self.mono.Mover(round(VectorPasoMono_nm[i]+self.mono.posicion,4))
                self.AdquirirGraficarYGrabarCSV()
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
                        self.AdquirirGraficarYGrabarCSV()
                    if k>0 and VectorPosicionInicialSMC_mm[k] != VectorPosicionFinalSMC_mm[k-1]:
                        self.AdquirirGraficarYGrabarCSV()
                    numeroDePasosSMC = abs(int((VectorPosicionFinalSMC_mm[k]-VectorPosicionInicialSMC_mm[k])/VectorPasoSMC_mm[k]))
                    for l in range(0,numeroDePasosSMC):
                        self.smc.Mover(VectorPasoSMC_mm[k]+self.smc.posicion)
                        self.AdquirirGraficarYGrabarCSV()
                if j<numeroDePasosMono:
                    self.mono.Mover(VectorPasoMono_nm[i] + self.mono.posicion)
    def AdquirirGraficarYGrabarCSV(self):
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

#%%%

class Programa():
    
    def __init__(self):
        self.experimento = Experimento()
        self.Configuracion()
        self.PantallaPrincipal()
        self.numeroDeConstantesDeTiempo = 50
#            self.experimento.lockin.CalcularTiempoDeIntegracion(self.numeroDeConstantesDeTiempo)
    def Configuracion(self):        
        raizConfiguracion = tk.Tk()
        raizConfiguracion.title('Pump and Probe Software')
        raizConfiguracion.geometry('550x200')

        def SetearPuertoSMC():
            puertoSMC = int(textoSMC.get())
            self.experimento.smc.AsignarPuerto('COM' + str(puertoSMC))
            b = self.experimento.smc.Identificar() # Booleano
            if b:
                labelSMCReconocido = tk.Label(raizConfiguracion, text = 'Reconocido')
                labelSMCReconocido.place(x=305, y=5)
            else:
                labelSMCReconocido = tk.Label(raizConfiguracion, text = 'No reconocido')
                labelSMCReconocido.place(x=305, y=5)
        def InicializarSMC():
            self.experimento.smc.Configurar()
        labelSMC = tk.Label(raizConfiguracion, text = 'Puerto COM correspondiente al SMC: ')
        labelSMC.place(x=0, y=5)
        textoSMC = tk.Entry(raizConfiguracion, width=5)
        textoSMC.place(x=225, y=5)
        textoSMC.delete(0, tk.END)
        textoSMC.insert(0, '4')
        botonSetearPuertoSMC = tk.Button(raizConfiguracion, text = 'Setear', command = SetearPuertoSMC)
        botonSetearPuertoSMC.place(x=260,y=5)
        botonInicializarSMC = tk.Button(raizConfiguracion, text = 'Inicializar', command = InicializarSMC)
        botonInicializarSMC.place(x=395,y=5)
        botonCalibrarSMC = tk.Button(raizConfiguracion, text = 'Calibrar', command = self.experimento.smc.Calibrar)
        botonCalibrarSMC.place(x=455, y=5)
                
        def SetearPuertoSMS():
            puertoSMS = int(textoMono.get())
            self.experimento.mono.AsignarPuerto('COM' + str(puertoSMS))
            b = self.experimento.mono.Identificar() # Booleano
            if b:
                labelSMSReconocido = tk.Label(raizConfiguracion, text = 'Reconocido')
                labelSMSReconocido.place(x=305, y=30)
            else:
                labelSMSReconocido = tk.Label(raizConfiguracion, text = 'No reconocido')
                labelSMSReconocido.place(x=305, y=30)
        def InicializarSMS():
            self.experimento.mono.Configurar()                
        labelMono = tk.Label(raizConfiguracion, text = 'Puerto COM correspondiente al SMS: ')
        labelMono.place(x=0, y=30)
        textoMono = tk.Entry(raizConfiguracion, width=5)
        textoMono.place(x=225, y=30)
        textoMono.delete(0, tk.END)
        textoMono.insert(0, '3')
        botonSetearPuertoSMS = tk.Button(raizConfiguracion, text = 'Setear', command = SetearPuertoSMS)
        botonSetearPuertoSMS.place(x=260,y=30)
        botonInicializarSMS = tk.Button(raizConfiguracion, text = 'Inicializar', command = InicializarSMS)
        botonInicializarSMS.place(x=395,y=30)
        botonCalibrarSMS = tk.Button(raizConfiguracion, text = 'Calibrar', command = self.experimento.mono.Calibrar)
        botonCalibrarSMS.place(x=455, y=30)
                
        def SetearPuertoLockIn():
            puertoLockIn = int(textoLockIn.get())
            self.experimento.lockin.AsignarPuerto(str(puertoLockIn))
            b = self.experimento.lockin.Identificar() # Booleano
            if b:
                labelLockInReconocido = tk.Label(raizConfiguracion, text = 'Reconocido')
                labelLockInReconocido.place(x=305, y=55)
            else:
                labelLockInReconocido = tk.Label(raizConfiguracion, text = 'No reconocido')
                labelLockInReconocido.place(x=305, y=55)
        def InicializarLockIn():
            self.experimento.lockin.Configurar()                        
        labelLockIn = tk.Label(raizConfiguracion, text = 'Puerto correspondiente al Lock-In: ')
        labelLockIn.place(x=0, y=55)
        textoLockIn = tk.Entry(raizConfiguracion, width=5)
        textoLockIn.place(x=225, y=55)
        textoLockIn.delete(0, tk.END)
        textoLockIn.insert(0, '8')
        botonSetearPuertoLockIn = tk.Button(raizConfiguracion, text = 'Setear', command = SetearPuertoLockIn)
        botonSetearPuertoLockIn.place(x=260,y=55)
        botonInicializarLockIn = tk.Button(raizConfiguracion, text = 'Inicializar', command = InicializarLockIn)
        botonInicializarLockIn.place(x=395,y=55)
                
        def MenuPrincipal():
            raizConfiguracion.destroy()

        botonMenuPrincipal = tk.Button(raizConfiguracion, text = 'Cerrar', command = MenuPrincipal)
        botonMenuPrincipal.place(x=100, y=100)
        
        raizConfiguracion.mainloop()
        
    def MedirALambdaFija(self):
        print('midiendoALambdaFija')
    def MedirAPosicionFija(self):
        print('midiendoAPosicionFija')
    def MedirCompletamente(self):
        print('midiendoCompletamente')
    def CalcularTiempoDeMedicionALambdaFija(self, numeroDeConstantesDeTiempo,
                                            VectorPosicionInicialSMC_mm,
                                            VectorPosicionFinalSMC_mm,
                                            VectorPasoSMC_mm):
        TiempoDeMedicion = 0
        CantidadDeMedicionesTotal = 0
        TiempoDeDesplazamientoTotal = 0
        TiempoDeDesplazamientoPorPaso = 0
        TiempoMuerto = 0
        TiempoMuerto = abs(VectorPosicionInicialSMC_mm[0]-self.experimento.smc.posicion)/self.experimento.smc.velocidadMmPorSegundo + 1
        for i in range(0, len(VectorPosicionInicialSMC_mm)):
            if i>0 and VectorPosicionInicialSMC_mm[i] != VectorPosicionFinalSMC_mm[i-1]:
                TiempoMuerto = TiempoMuerto + abs(VectorPosicionInicialSMC_mm[i]-VectorPosicionFinalSMC_mm[i-1])/self.experimento.smc.velocidadMmPorSegundo + 1
            CantidadDeMediciones = 0
            CantidadDeMediciones = abs(VectorPosicionFinalSMC_mm[i]-VectorPosicionInicialSMC_mm[i])/VectorPasoSMC_mm[i]
            TiempoDeDesplazamientoPorPaso = VectorPasoSMC_mm[i]/self.experimento.smc.velocidadMmPorSegundo + 1
            TiempoDeDesplazamientoTotal = TiempoDeDesplazamientoTotal + CantidadDeMediciones*TiempoDeDesplazamientoPorPaso
            CantidadDeMedicionesTotal = CantidadDeMedicionesTotal + CantidadDeMediciones
        TiempoDeMedicion = CantidadDeMedicionesTotal*(self.experimento.lockin.CalcularTiempoDeIntegracion(numeroDeConstantesDeTiempo)) + TiempoDeDesplazamientoTotal + TiempoMuerto
        return TiempoDeMedicion
    
    def CalcularTiempoDeMedicionAPosicionFijaSMC(self, numeroDeConstantesDeTiempo,
                                                 VectorLongitudDeOndaInicial_nm,
                                                 VectorLongitudDeOndaFinal_nm,
                                                 VectorPasoMono_nm):
        TiempoDeMedicion = 0
        CantidadDeMedicionesTotal = 0
        TiempoDeDesplazamientoTotal = 0
        TiempoDeDesplazamientoPorPaso = 0
        TiempoMuerto = 0
        TiempoMuerto = abs(VectorLongitudDeOndaInicial_nm[0]-self.experimento.mono.posicion)/self.experimento.mono.velocidadNmPorSegundo + 5
        for i in range(0, len(VectorLongitudDeOndaInicial_nm)):
            if i>0 and VectorLongitudDeOndaInicial_nm[i] != VectorLongitudDeOndaFinal_nm[i-1]:
                TiempoMuerto = TiempoMuerto + abs(VectorLongitudDeOndaInicial_nm[i]-VectorLongitudDeOndaFinal_nm[i-1])/self.experimento.mono.velocidadNmPorSegundo + 5
            CantidadDeMediciones = 0
            CantidadDeMediciones = abs(VectorLongitudDeOndaFinal_nm[i]-VectorLongitudDeOndaInicial_nm[i])/VectorPasoMono_nm[i]
            TiempoDeDesplazamientoPorPaso = VectorPasoMono_nm[i]/self.experimento.mono.velocidadNmPorSegundo + 5
            TiempoDeDesplazamientoTotal = TiempoDeDesplazamientoTotal + CantidadDeMediciones*TiempoDeDesplazamientoPorPaso
        TiempoDeMedicion = CantidadDeMedicionesTotal*(self.experimento.lockin.CalcularTiempoDeIntegracion(numeroDeConstantesDeTiempo)) + TiempoDeDesplazamientoTotal + TiempoMuerto
        return TiempoDeMedicion    

    def CalcularTiempoDeMedicionCompleta(self, numeroDeConstantesDeTiempo,
                                         VectorPosicionInicialSMC_mm,
                                         VectorPosicionFinalSMC_mm,
                                         VectorPasoSMC_mm,
                                         VectorLongitudDeOndaInicial_nm,
                                         VectorLongitudDeOndaFinal_nm,
                                         VectorPasoMono_nm):
        CantidadDeMovimientosSMCTotal = 0
        TiempoDeDesplazamientoSMC = 0
        TiempoDeDesplazamientoPorPaso = 0
        TiempoDeDesplazamientoMono = 0
        TiempoMuertoSMC = 0
        TiempoMuertoMono = 0
        CantidadDeMovimientosMonoTotal = 0
        largoVectorSMC = len(VectorPosicionInicialSMC_mm)
        TiempoSMCInicial = abs(VectorPosicionInicialSMC_mm[0]-self.experimento.smc.posicion)/self.experimento.smc.velocidadMmPorSegundo + 1
        TiempoDeRetornoSMC = abs(VectorPosicionFinalSMC_mm[largoVectorSMC-1]-VectorPosicionInicialSMC_mm[0])/self.experimento.smc.velocidadMmPorSegundo + 1
        TiempoMonocromadorInicial = abs(VectorLongitudDeOndaInicial_nm[0]-self.experimento.mono.posicion)/self.experimento.mono.velocidadNmPorSegundo + 5
        for i in range(0, len(VectorPosicionInicialSMC_mm)):
            if i>0 and VectorPosicionInicialSMC_mm[i] != VectorPosicionFinalSMC_mm[i-1]:
                TiempoMuertoSMC = TiempoMuertoSMC + (VectorPosicionInicialSMC_mm[i]-VectorPosicionFinalSMC_mm[i-1])/self.experimento.smc.velocidadMmPorSegundo + 1
            CantidadDeMovimientosSMC = 0
            CantidadDeMovimientosSMC = abs(VectorPosicionFinalSMC_mm[i]-VectorPosicionInicialSMC_mm[i])/VectorPasoSMC_mm[i]
            TiempoDeDesplazamientoPorPaso = VectorPasoSMC_mm[i]/self.experimento.smc.velocidadMmPorSegundo + 1
            TiempoDeDesplazamientoSMC = TiempoDeDesplazamientoSMC + CantidadDeMovimientosSMC*TiempoDeDesplazamientoPorPaso
        
        TiempoSMC = TiempoDeDesplazamientoSMC + TiempoSMCInicial + TiempoMuertoSMC + TiempoDeRetornoSMC
        
        for j in range(0, len(VectorLongitudDeOndaInicial_nm)):
            if j>0 and VectorLongitudDeOndaInicial_nm[i] != VectorLongitudDeOndaFinal_nm[i-1]:
                TiempoMuertoMono = TiempoMuertoMono + abs(VectorLongitudDeOndaInicial_nm[j]-VectorLongitudDeOndaFinal_nm[j-1])/self.experimento.mono.velocidadNmPorSegundo + 5
            CantidadDeMovimientosMono = 0
            CantidadDeMovimientosMono = abs(VectorLongitudDeOndaFinal_nm[j]-VectorLongitudDeOndaInicial_nm[j])/VectorPasoMono_nm[j]
            CantidadDeMovimientosMonoTotal = CantidadDeMovimientosMonoTotal + CantidadDeMovimientosMono
            TiempoDeDesplazamientoPorPaso = VectorPasoMono_nm[j]/self.experimento.mono.velocidadNmPorSegundo + 5
            TiempoDeDesplazamientoMono = TiempoDeDesplazamientoMono + CantidadDeMovimientosMono*TiempoDeDesplazamientoPorPaso
        TiempoMonocromador = TiempoDeDesplazamientoMono + TiempoMonocromadorInicial + TiempoMuertoMono
        TiempoSMCTotal = TiempoSMC*CantidadDeMovimientosMonoTotal
        TiempoLockIn = CantidadDeMovimientosSMCTotal*CantidadDeMovimientosMonoTotal*(self.experimento.lockin.CalcularTiempoDeIntegracion(numeroDeConstantesDeTiempo))
        
        TiempoTotal = TiempoMonocromador + TiempoSMCTotal + TiempoLockIn
        
        return TiempoTotal

    def PantallaPrincipal(self):
        raiz = tk.Tk()
        raiz.title('Pump and Probe Software')
        raiz.geometry('1400x1000')   
        
        #MEDICION MANUAL#        
        
        labelNumeroDeConstantesDeTiempo = tk.Label(raiz, text = '# de ctes de tiempo (Lock In):')
        labelNumeroDeConstantesDeTiempo.place(x=0, y=5)
        textoNumeroDeConstantesDeTiempo = tk.Entry(raiz, width=5)
        textoNumeroDeConstantesDeTiempo.place(x=160, y=7)
        textoNumeroDeConstantesDeTiempo.delete(0, tk.END)
        textoNumeroDeConstantesDeTiempo.insert(0, '100')
        
        def SetearNumeroDeConstantesDeTiempo():
            self.numeroDeConstantesDeTiempo = int(textoNumeroDeConstantesDeTiempo.get())
#            self.experimento.lockin.CalcularTiempoDeIntegracion(self.numeroDeConstantesDeTiempo)
        botonSetearNumeroDeConstantesDeTiempo = tk.Button(raiz, text="Setear", command=SetearNumeroDeConstantesDeTiempo)
        botonSetearNumeroDeConstantesDeTiempo.place(x=200, y=5)
        
        labelPosicionSMC = tk.Label(raiz, text = 'Posición desde 0 hasta 25 (mm) (res: 0.0001) :')
        labelPosicionSMC.place(x=250, y=5)
        textoPosicionSMC = tk.Entry(raiz, width=5)
        textoPosicionSMC.place(x=493, y=7)
        textoPosicionSMC.delete(0, tk.END)
#        textoPosicionSMC.insert(0, str(self.experimento.smc.posicion))
        def IrALaPosicionSMC():
            comando = float(textoPosicionSMC.get())
#            self.experimento.smc.Mover(comando)
        botonIrALaPosicionSMC = tk.Button(raiz, text="Mover", command=IrALaPosicionSMC)
        botonIrALaPosicionSMC.place(x=532, y=5)
        
        labelPosicionMonocromador = tk.Label(raiz, text = '\u03BB desde 200 hasta 1200 (nm) (res: 0.3) :')
        labelPosicionMonocromador.place(x=582, y=5)
        textoPosicionMonocromador = tk.Entry(raiz, width=5)
        textoPosicionMonocromador.place(x=790, y=7)
        textoPosicionMonocromador.delete(0, tk.END)
#        textoPosicionMonocromador.insert(0, str(self.experimento.mono.posicion))
        def IrALaPosicionMonocromador():
            comando = float(textoPosicionMonocromador.get())
#            self.experimento.mono.Mover(comando)
        botonIrALaPosicionMonocromador = tk.Button(raiz, text="Mover", command=IrALaPosicionMonocromador)
        botonIrALaPosicionMonocromador.place(x=830, y=5)

        labelX = tk.Label(raiz, text = 'X')
        labelX.place(x=15, y=35)
        textoX = tk.Entry(raiz, width=5)
        textoX.place(x=0, y=60)
        labelY = tk.Label(raiz, text = 'Y')
        labelY.place(x=65, y=35)
        textoY = tk.Entry(raiz, width=5)
        textoY.place(x=50, y=60)
        labelR = tk.Label(raiz, text = 'R')
        labelR.place(x=115, y=35)
        textoR = tk.Entry(raiz, width=5)
        textoR.place(x=100, y=60)
        labelTheta = tk.Label(raiz, text = '\u03B8')
        labelTheta.place(x=165, y=35)
        textoTheta = tk.Entry(raiz, width=5)
        textoTheta.place(x=150, y=60)
        labelAuxIn = tk.Label(raiz, text = 'Aux')
        labelAuxIn.place(x=200, y=35)
        textoAuxIn = tk.Entry(raiz, width=5)
        textoAuxIn.place(x=200, y=60)
        labelCocienteXConAuxIn = tk.Label(raiz, text = 'X/Aux')
        labelCocienteXConAuxIn.place(x=250, y=35)
        textoCocienteXConAuxIn = tk.Entry(raiz, width=5)
        textoCocienteXConAuxIn.place(x=250, y=60)
        
        def IniciarMedicion():
            global t
            t = th.Thread(target=Medicion)
            t.do_run = True
            t.start()
        def Medicion():
            while t.do_run == True:
                vectorDeStringsDeDatos = np.random.rand(5)
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
        
        botonIniciarMedicion = tk.Button(raiz, text="Iniciar Medicion", command=IniciarMedicion)
        botonIniciarMedicion.place(x=300, y=35)
        botonFrenarMedicion = tk.Button(raiz, text="Frenar Medicion", command=FrenarMedicion)
        botonFrenarMedicion.place(x=300, y=60)
        
        #CONVERSOR#
        
        labelTituloConversor = tk.Label(raiz, text="Conversor de\n mm a fs")
        labelTituloConversor.place(x=405, y=43)
        labelmm = tk.Label(raiz, text="mm")
        labelmm.place(x=520, y=35)
        labelfs = tk.Label(raiz, text="fs")
        labelfs.place(x=665, y=35)
        textomm = tk.Entry(raiz,width=15)
        textomm.place(x=490, y=60)
        textofs = tk.Entry(raiz,width=15)
        textofs.place(x=635, y=60)
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
        botonConvertirAmm = tk.Button(raiz, text="<-", command=ConvertirAmm)
        botonConvertirAmm.place(x=585, y=55)
        botonConvertirAfs = tk.Button(raiz, text="->", command=ConvertirAfs)
        botonConvertirAfs.place(x=610, y=55)
        
        
        #BOTON CONFIGURACION#
        fuente = font.Font(size=10)
        botonConfiguracion = tk.Button(raiz, text="Configuración", font=fuente, command=self.Configuracion, width=20, heigh=2)
        botonConfiguracion.place(x=950, y=5)
        
        
        #BARRIDOS#
        
        labelMediciones = tk.Label(raiz, text = 'Barridos', font=("Arial", 25))
        labelMediciones.place(x=950, y=100)

        #BARRIDO EN POSICIONES DEL SMC#
        
        labelTituloInicial = tk.Label(raiz, text="Barrido en distancia")
        labelTituloInicial.place(x=950, y=140)        
        
        labelNumeroDeSubintervalos = tk.Label(raiz, text="Secciones: ")
        labelNumeroDeSubintervalos.place(x=950, y=160)
        textoNumeroDeSubintervalos = tk.Entry(raiz,width=5)
        textoNumeroDeSubintervalos.place(x=1050, y=165)
        textoNumeroDeSubintervalos.delete(0, tk.END)
        textoNumeroDeSubintervalos.insert(0, '1')        
        
        labelTituloInicial = tk.Label(raiz, text="Posicion Inicial")
        labelTituloInicial.place(x=950, y=185)
        labelTituloFinal = tk.Label(raiz, text="Posicion Final")
        labelTituloFinal.place(x=1050, y=185)
        labelTituloPaso = tk.Label(raiz, text="Paso")
        labelTituloPaso.place(x=1150, y=185)
    
        textosPosicionInicial = list()
        textosPosicionFinal = list()
        textosPaso = list()
                    
        def ObtenerSecciones():
            for i in range(0,len(textosPosicionInicial)):
                textosPosicionInicial[i].destroy()
                textosPosicionFinal[i].destroy()
                textosPaso[i].destroy()
            textosPosicionInicial.clear()
            textosPosicionFinal.clear()
            textosPaso.clear()
            self.numeroDeSubintervalos = int(textoNumeroDeSubintervalos.get())
            for i in range(0,self.numeroDeSubintervalos):
                textosPosicionInicial.append(tk.Entry(raiz,width=15))
                textosPosicionFinal.append(tk.Entry(raiz,width=15))
                textosPaso.append(tk.Entry(raiz,width=15))
                textosPosicionInicial[i].place(x=950, y=205+i*20)
                textosPosicionFinal[i].place(x=1050, y=205+i*20)
                textosPaso[i].place(x=1150, y=205+i*20)
        ObtenerSecciones()    
        botonSiguiente = tk.Button(raiz, text="Ok", command=ObtenerSecciones)
        botonSiguiente.place(x=1100, y=160)

        def MedirALambdaFija():
            VectorPosicionInicialSMC_mm = np.zeros(self.numeroDeSubintervalos)
            VectorPosicionFinalSMC_mm = np.zeros(self.numeroDeSubintervalos)
            VectorPasoSMC_mm = np.zeros(self.numeroDeSubintervalos)
            for i in range(0,self.numeroDeSubintervalos):
                VectorPosicionInicialSMC_mm[i] = float(textosPosicionInicial[i].get())
                VectorPosicionFinalSMC_mm[i] = float(textosPosicionFinal[i].get())
                VectorPasoSMC_mm[i] = float(textosPaso[i].get())
            nombreArchivo = textoNombreArchivo.get()
            ejeX = variable.get()
            ValoresAGraficar = ([1,1,1,1])
            self.grafico = Grafico(ValoresAGraficar,0,ejeX,longitudDeOndaFija_nm=0)
#            self.experimento.grafico = self.grafico
            tiempoDeMedicion = '0'
#            tiempoDeMedicion = str(self.CalcularTiempoDeMedicionALambdaFija(self.numeroDeConstantesDeTiempo,VectorPosicionInicialSMC_mm,VectorPosicionFinalSMC_mm,VectorPasoSMC_mm))
            labelEstado = tk.Label(raiz, text="Realizando la medicion. Tiempo estimado: " + tiempoDeMedicion + ' segundos')
            labelEstado.place(x=950, y=650)
            canvas = FigureCanvasTkAgg(self.grafico.fig, master=raiz)
            canvas.get_tk_widget().place(x=0,y=90)
            canvas.draw()
            raiz.update()
#            self.experimento.MedicionALambdaFija(nombreArchivo,VectorPosicionInicialSMC_mm,VectorPosicionFinalSMC_mm,VectorPasoSMC_mm)
            nombreGrafico = nombreArchivo.replace('.csv','')
            self.grafico.GuardarGrafico(nombreGrafico)
            labelEstado = tk.Label(raiz, text="Medicion Finalizada. El archivo ha sido guardado con el nombre: " + nombreArchivo)
            labelEstado.place(x=950, y=675)                       
        botonMedirALambdaFija = tk.Button(raiz, text="Barrer", command=MedirALambdaFija)
        botonMedirALambdaFija.place(x=1075, y=305)
        
        #BARRIDO EN LONGITUDES DE ONDA#
        
        labelTituloBarridoLongitudDeOnda = tk.Label(raiz, text="Barrido en longitud de onda")
        labelTituloBarridoLongitudDeOnda.place(x=950, y=360)        

        labelNumeroDeSubintervalosLongitudDeOnda = tk.Label(raiz, text="Secciones: ")
        labelNumeroDeSubintervalosLongitudDeOnda.place(x=950, y=380)
        textoNumeroDeSubintervalosLongitudDeOnda = tk.Entry(raiz,width=5)
        textoNumeroDeSubintervalosLongitudDeOnda.place(x=1050, y=385)
        textoNumeroDeSubintervalosLongitudDeOnda.delete(0, tk.END)
        textoNumeroDeSubintervalosLongitudDeOnda.insert(0, '1')        

        labelTituloLongitudDeOndaInicial = tk.Label(raiz, text="\u03BB Inicial")
        labelTituloLongitudDeOndaInicial.place(x=950, y=405)
        labelTituloLongitudDeOndaFinal = tk.Label(raiz, text="\u03BB Final")
        labelTituloLongitudDeOndaFinal.place(x=1050, y=405)
        labelTituloPasoLongitudDeOnda = tk.Label(raiz, text="Paso")
        labelTituloPasoLongitudDeOnda.place(x=1150, y=405)
   
        textosLongitudDeOndaInicial = list()
        textosLongitudDeOndaFinal = list()
        textosPasoLongitudDeOnda = list()
        
        def ObtenerSeccionesBarridoEnLongitudDeOnda():
            for i in range(0,len(textosLongitudDeOndaInicial)):
                textosLongitudDeOndaInicial[i].destroy()
                textosLongitudDeOndaFinal[i].destroy()
                textosPasoLongitudDeOnda[i].destroy()
            textosLongitudDeOndaInicial.clear()
            textosLongitudDeOndaFinal.clear()
            textosPasoLongitudDeOnda.clear()
            self.numeroDeSubintervalosLongitudDeOnda = int(textoNumeroDeSubintervalosLongitudDeOnda.get())
            for i in range(0,self.numeroDeSubintervalosLongitudDeOnda):
                textosLongitudDeOndaInicial.append(tk.Entry(raiz,width=15))
                textosLongitudDeOndaFinal.append(tk.Entry(raiz,width=15))
                textosPasoLongitudDeOnda.append(tk.Entry(raiz,width=15))
                textosLongitudDeOndaInicial[i].place(x=950, y=425+i*20)
                textosLongitudDeOndaFinal[i].place(x=1050, y=425+i*20)
                textosPasoLongitudDeOnda[i].place(x=1150, y=425+i*20)
        botonSeccionesLongitudDeOnda = tk.Button(raiz, text="Ok", command=ObtenerSeccionesBarridoEnLongitudDeOnda)
        botonSeccionesLongitudDeOnda.place(x=1100, y=380)
        ObtenerSeccionesBarridoEnLongitudDeOnda()
        
        def MedirAPosicionFija():
            VectorLongitudDeOndaInicial_nm = np.zeros(self.numeroDeSubintervalosLongitudDeOnda)
            VectorLongitudDeOndaFinal_nm = np.zeros(self.numeroDeSubintervalosLongitudDeOnda)
            VectorPasoMono_nm = np.zeros(self.numeroDeSubintervalosLongitudDeOnda)
            for i in range(0,self.numeroDeSubintervalosLongitudDeOnda):
                VectorLongitudDeOndaInicial_nm[i] = float(textosLongitudDeOndaInicial[i].get())
                VectorLongitudDeOndaFinal_nm[i] = float(textosLongitudDeOndaFinal[i].get())
                VectorPasoMono_nm[i] = float(textosPasoLongitudDeOnda[i].get())
            nombreArchivo = textoNombreArchivo.get()
            tiempoDeMedicion = '0'
            ValoresAGraficar = ([1,1,1,1])
            self.grafico = Grafico(ValoresAGraficar,1,0,posicionFijaSMC_mm = 0)
#            self.experimento.grafico = self.grafico
#            tiempoDeMedicion = str(self.CalcularTiempoDeMedicionAPosicionFijaSMC(self.numeroDeConstantesDeTiempo,VectorPosicionInicialSMC_mm,VectorPosicionFinalSMC_mm,VectorPasoSMC_mm))
            labelEstado = tk.Label(raiz, text="Realizando la medicion. Tiempo estimado: " + tiempoDeMedicion + ' segundos')
            labelEstado.place(x=950, y=650)
            canvas = FigureCanvasTkAgg(self.grafico.fig, master=raiz)
            canvas.get_tk_widget().place(x=0,y=90)
            canvas.draw()
#            raizMedicion.update()
#            self.experimento.MedicionAPosicionFijaSMC(nombreArchivo,VectorPosicionInicialSMC_mm,VectorPosicionFinalSMC_mm,VectorPasoSMC_mm)
            nombreGrafico = nombreArchivo.replace('.csv','')
#            self.grafico.GuardarGrafico(nombreGrafico)
            labelEstado = tk.Label(raiz, text="Medicion Finalizada. El archivo ha sido guardado con el nombre: " + nombreArchivo)
            labelEstado.place(x=950, y=675)    
        botonMedirAPosicionFija = tk.Button(raiz, text="Barrer", command=MedirAPosicionFija)
        botonMedirAPosicionFija.place(x=1075, y=525)
                
        # EJE X: TIEMPO O DISTANCIA#
        labelEjeX = tk.Label(raiz, text="Eje X del gráfico: ")
        labelEjeX.place(x=950, y=330)
        choices = ['Tiempo', 'Distancia']
        variable = tk.StringVar(raiz)
        variable.set('Tiempo')
        w = tk.OptionMenu(raiz, variable, *choices)
        w.place(x=1150,y=323)
            
        labelNombreArchivo = tk.Label(raiz, text="Nombre del archivo (Ej: datos2.csv) :")
        labelNombreArchivo.place(x=950, y=575)
        textoNombreArchivo = tk.Entry(raiz,width=15)
        textoNombreArchivo.place(x=1150, y=575)
        textoNombreArchivo.delete(0, tk.END)
        textoNombreArchivo.insert(0, 'datos.csv')        
        
        #DOBLE BARRIDO#
        def MedirCompletamente():
            VectorPosicionInicialSMC_mm = np.zeros(self.numeroDeSubintervalos)
            VectorPosicionFinalSMC_mm = np.zeros(self.numeroDeSubintervalos)
            VectorPasoSMC_mm = np.zeros(self.numeroDeSubintervalos)
            for i in range(0,self.numeroDeSubintervalos):
                VectorPosicionInicialSMC_mm[i] = float(textosPosicionInicial[i].get())
                VectorPosicionFinalSMC_mm[i] = float(textosPosicionFinal[i].get())
                VectorPasoSMC_mm[i] = float(textosPaso[i].get())
            VectorLongitudDeOndaInicial_nm = np.zeros(self.numeroDeSubintervalosLongitudDeOnda)
            VectorLongitudDeOndaFinal_nm = np.zeros(self.numeroDeSubintervalosLongitudDeOnda)
            VectorPasoMono_nm = np.zeros(self.numeroDeSubintervalosLongitudDeOnda)
            for i in range(0,self.numeroDeSubintervalosLongitudDeOnda):
                VectorLongitudDeOndaInicial_nm[i] = float(textosLongitudDeOndaInicial[i].get())
                VectorLongitudDeOndaFinal_nm[i] = float(textosLongitudDeOndaFinal[i].get())
                VectorPasoMono_nm[i] = float(textosPasoLongitudDeOnda[i].get())
            ejeX = variable.get()
            ValoresAGraficar = ([1,1,1,1])
            nombreArchivo = textoNombreArchivo.get()
            tiempoDeMedicion = '0'
            self.grafico = Grafico(ValoresAGraficar, 2, ejeX, VectorPosicionInicialSMC_mm, VectorPosicionFinalSMC_mm, VectorPasoSMC_mm, VectorLongitudDeOndaInicial_nm, VectorLongitudDeOndaFinal_nm, VectorPasoMono_nm)
#            self.experimento.grafico = self.grafico
#            tiempoDeMedicion = str(self.CalcularTiempoDeMedicionCompleta(self.numeroDeConstantesDeTiempo,VectorPosicionInicialSMC_mm, VectorPosicionFinalSMC_mm, VectorPasoSMC_mm, VectorLongitudDeOndaInicial_nm, VectorLongitudDeOndaFinal_nm, VectorPasoMono_nm))
            labelEstado = tk.Label(raiz, text="Realizando la medicion. Tiempo estimado: " + tiempoDeMedicion + ' segundos')
            labelEstado.place(x=950, y=650)
            canvas = FigureCanvasTkAgg(self.grafico.fig, master=raiz)
            canvas.get_tk_widget().place(x=0,y=90)
            canvas.draw()
#            raizMedicion.update()
#            self.experimento.MedicionCompleta(nombreArchivo, VectorPosicionInicialSMC_mm, VectorPosicionFinalSMC_mm, VectorPasoSMC_mm, VectorLongitudDeOndaInicial_nm, VectorLongitudDeOndaFinal_nm, VectorPasoMono_nm)
            nombreGrafico = nombreArchivo.replace('.csv','')
#            self.grafico.GuardarGrafico(nombreGrafico)
            labelEstado = tk.Label(raiz, text="Medicion Finalizada. El archivo ha sido guardado con el nombre: " + nombreArchivo)
            labelEstado.place(x=950, y=675)    
        
        botonMedirCompletamente = tk.Button(raiz, text="Barrido doble", command=MedirCompletamente)
        botonMedirCompletamente.place(x=1075, y=605)
        
        raiz.mainloop()

programa = Programa()