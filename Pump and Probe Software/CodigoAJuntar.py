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
from datetime import date
import os

global do_run
do_run = True
global t
global thread
global tiempoAgregadoMonocromador #Tiempo de espera por paso agregado para el monocromador.
global tiempoAgregadoPlataforma # Tiempo de espera por paso agregado para la plataforma.
tiempoAgregadoMonocromador = 1
tiempoAgregadoPlataforma = 1

#%%%%%%
class SMC():
    def __init__(self):
        self.address = serial.Serial(
                port = None,
                baudrate = 57600,
                bytesize = 8,
                stopbits = 1,
                parity = 'N',
                timeout = 1,
                xonxoff = True,
                rtscts = False,
                dsrdtr = False)
        self.resolucion = 0.0001
        self.posicion = 0 # Solo para inicializar la variable. Al configurar se lee la posición.
        self.velocidadMmPorSegundo = 0.16
    def AsignarPuerto(self, puerto):
        self.address.port = puerto
        self.puerto = puerto
        self.address.open()
    def CerrarPuerto(self):
        self.address.close()
    def Configurar(self):    
        valor = -1
        estadosReady = ['32','33','34']
        while valor == -1:
            self.address.write(b'1TS\r\n')
            time.sleep(0.3)
            lectura = self.LeerBuffer()
            if 'TS' in lectura:
                valor = 1
                if any(x in lectura for x in estadosReady):
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
            self.address.write(b'1TS\r\n')
            time.sleep(0.3)
            lectura = self.LeerBuffer()
            if 'TS' in lectura:
                valor = lectura.find('32')
        self.posicion = 0
    def LeerPosicion(self):
        valor = -1
        while valor == -1:
            self.address.write(b'1TH\r\n')
            time.sleep(0.3)
            lectura = self.LeerBuffer()
            if 'TH' in lectura:
                a = lectura.split('\r')[0]
                b = a.split('TH')[len(a.split('TH'))-1]
                return float(b)
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
            TiempoSMC = abs(PosicionSMC_mm-self.posicion)/self.velocidadMmPorSegundo + tiempoAgregadoPlataforma
        return TiempoSMC
    def LeerBuffer(self):
        lectura = 'a'
        lecturaTotal = ''
        while lectura != '\n' and lectura != '': 
            time.sleep(0.1)
            lectura = self.address.read()
            print(lectura)
            lectura = lectura.decode('windows-1252')
            lecturaTotal = lecturaTotal + lectura
        return lecturaTotal      
    def Identificar(self):
        valor = -1
        b = False
        i=0
        while valor == -1 and i < 5:
            i += 1
            self.address.write(b'1ID?\r\n')
            time.sleep(0.3)
            lectura = self.LeerBuffer()
            if 'ID' in lectura:
                valor = 1
                if 'TRA25PPD' in lectura:
                    b = True
        return b
    def Calibrar(self):
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
        return
    
#%%%
        
class SMS():
    def __init__(self):
        self.address = serial.Serial(
                port = None,
                baudrate = 9600,
                bytesize = 8,
                stopbits = 1,
                parity = 'N',
                timeout = 3,
                xonxoff = False,
                rtscts = False,
                dsrdtr = True)
        self.posicion = 0
        self.resolucion = 0.3125 # Resolucion = 1/multiplicador
        self.velocidadNmPorSegundo = 9 
    def AsignarPuerto(self, puerto):
        self.address.port = puerto
        self.puerto = puerto     
        self.address.open()
    def CerrarPuerto(self):
        self.address.close()
    def LeerPosicion(self):
        valor = -1
        while valor == -1:
            self.address.write(b'#CL?\r3\r')
            time.sleep(1)
            lectura = self.LeerBuffer()
            valor = lectura.find('CL?')        
        a = lectura.split('\r')[0]
        b = a.split(' ')[len(a.split(' '))-1]
        c = b.split('!!')[0]
        posicionEnNm = float(c)
        return posicionEnNm
    def Configurar(self): # AGREGAR SETEO DE MULT Y OFFSET PARA CAMBIAR DE RED
        comando = '#SLM\r3\r'
        self.address.write(comando.encode())
        time.sleep(1)
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
            TiempoMonocromador = abs(LongitudDeOnda_nm-self.posicion)/(self.velocidadNmPorSegundo) + tiempoAgregadoMonocromador
        return TiempoMonocromador
    def LeerBuffer(self):
        lectura = 'a'
        lecturaTotal = ''
        while lectura != '\n' and lectura != '':
            lectura = self.address.read()
            print(lectura)
            lectura = lectura.decode('windows-1252')
            lecturaTotal = lecturaTotal + lectura
            time.sleep(0.1)
        return lecturaTotal
    def Identificar(self):
        b = False
        valor = -1
        i = 1
        while valor == -1 and i < 5:
            i += 1
            self.address.write(b'#VR?\r')
            time.sleep(0.5)
            self.address.flush()
            lectura = self.LeerBuffer()
            if 'VR' in lectura:
                valor = 1
                if 'Version 3.03' in lectura:
                    b =True
        return b
    def Calibrar(self):
        self.address.write(b'#CAL\r3\r')
        time.sleep(self.CalcularTiempoSleep(-87))
        self.posicion = self.LeerPosicion()
        return
    
#%%%
    
class LockIn():
    def AsignarPuerto(self, puerto):
        rm = pyvisa.ResourceManager()
        comando = 'GPIB0::' + puerto + '::INSTR'
        self.address = rm.open_resource(comando)
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
        self.CalcularTiempoDeIntegracion(1)
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
        lectura = self.address.query("*IDN?")
        if 'SR830' in lectura:
            b = True
        return b

#%%%        

class Grafico(): 
    def __init__(self):
        self.fig = plt.figure(figsize=(13,10))
    def Configurar(self, valoresAGraficar, TipoDeMedicion, ejeX, VectorPosicionInicialSMC_mm = 0, VectorPosicionFinalSMC_mm = 0, VectorPasoSMC_mm = 0, VectorLongitudDeOndaInicial_nm = 0, VectorLongitudDeOndaFinal_nm = 0, VectorPasoMono_nm = 0, longitudDeOndaFija_nm = 0, posicionFijaSMC_mm = 0):
        self.fig.clear()
        self.TipoDeMedicion = TipoDeMedicion
        self.ValoresAGraficar = valoresAGraficar
        self.cantidadDeValoresAGraficar = valoresAGraficar.count(1)
        self.posicionFijaSMC_mm = posicionFijaSMC_mm
        self.longitudDeOndaFija_nm = longitudDeOndaFija_nm
        self.ejeX = ejeX
        self.x = list()
        self.z = list()
        self.VectorX = 0
        self.VectorY = 0
        self.M1 = 0
        self.M2 = 0
        self.M3 = 0
        self.M4 = 0
        self.listaDeMatrices = list()
        self.listaDePlots = list()
        self.listaDeColorbars = list()
        self.y1 = list()
        self.y2 = list()
        self.y3 = list()
        self.y4 = list()   
        self.listaDeValoresAGraficar = list()
        if TipoDeMedicion == 2:
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
            if valoresAGraficar[0] == 1:
                self.M1 = np.zeros((len(self.VectorY),len(self.VectorX)))
            if valoresAGraficar[1] == 1:
                self.M2 = np.zeros((len(self.VectorY),len(self.VectorX)))
            if valoresAGraficar[2] == 1:
                self.M3 = np.zeros((len(self.VectorY),len(self.VectorX)))
            if valoresAGraficar[3] == 1:
                self.M4 = np.zeros((len(self.VectorY),len(self.VectorX)))
                
        if valoresAGraficar[0] == 1:
            self.listaDeMatrices.append(self.M1)
            self.listaDeValoresAGraficar.append('X')
        if valoresAGraficar[1] == 1:
            self.listaDeMatrices.append(self.M2)
            self.listaDeValoresAGraficar.append('Y')
        if valoresAGraficar[2] == 1:
            self.listaDeMatrices.append(self.M3)
            self.listaDeValoresAGraficar.append('R')
        if valoresAGraficar[3] == 1:
            self.listaDeMatrices.append(self.M4)
            self.listaDeValoresAGraficar.append('\u03B8')
        self.listaDeGraficos = list()
        if self.cantidadDeValoresAGraficar == 1:
            self.listaDeGraficos.append(self.fig.add_subplot(111))
        if self.cantidadDeValoresAGraficar == 2:
            self.listaDeGraficos.append(self.fig.add_subplot(211))
            self.listaDeGraficos.append(self.fig.add_subplot(212))
        if self.cantidadDeValoresAGraficar == 3:
            self.listaDeGraficos.append(self.fig.add_subplot(221))
            self.listaDeGraficos.append(self.fig.add_subplot(222))
            self.listaDeGraficos.append(self.fig.add_subplot(223))
        if self.cantidadDeValoresAGraficar == 4:
            self.listaDeGraficos.append(self.fig.add_subplot(221))
            self.listaDeGraficos.append(self.fig.add_subplot(222))
            self.listaDeGraficos.append(self.fig.add_subplot(223))
            self.listaDeGraficos.append(self.fig.add_subplot(224))
        self.CrearGrafico(TipoDeMedicion)
        

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
    def CrearGrafico(self, TipoDeMedicion):
        if TipoDeMedicion == 0:
            for i in range(0,self.cantidadDeValoresAGraficar):
                self.listaDeGraficos[i].set_title('\u03BB = ' + str(self.longitudDeOndaFija_nm) + ' nm')
                if self.ejeX == 'Distancia':
                    self.listaDeGraficos[i].set_xlabel('Retardo (mm)')
                else:
                    self.listaDeGraficos[i].set_xlabel('Retardo (ps)')
                self.listaDeGraficos[i].set_ylabel(self.listaDeValoresAGraficar[i])
        if TipoDeMedicion == 1:
            for i in range (0,self.cantidadDeValoresAGraficar):
                self.listaDeGraficos[i].set_title('Posición = ' + str(self.posicionFijaSMC_mm) + ' mm')
                self.listaDeGraficos[i].set_xlabel('Longitud de onda (nm)')
                self.listaDeGraficos[i].set_ylabel(self.listaDeValoresAGraficar[i])
        if TipoDeMedicion == 2:
            for i in range(0,self.cantidadDeValoresAGraficar):
                self.listaDeGraficos[i].set_title(self.listaDeValoresAGraficar[i])
                if self.ejeX == 'Distancia':
                    self.listaDeGraficos[i].set_xlabel('Retardo (mm)')
                else:
                    self.listaDeGraficos[i].set_xlabel('Retardo (ps)')
                self.listaDeGraficos[i].set_ylabel('Longitud de onda (nm)') 
                self.listaDePlots.append(self.listaDeGraficos[i].contourf(self.VectorX, self.VectorY, self.listaDeMatrices[i], 20, cmap='RdGy'))
                print('entro')
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
    def GraficarALambdaFija(self, VectorAGraficar, posicionSMC, posicionMono):
        if self.ejeX == 'Distancia':
            self.x.append(posicionSMC)
        else:
            self.x.append((posicionSMC)*(2/3)*10) # en picosegundos
#            self.x.append((posicionSMC)*(2/3)*(10**(-11))) # en segundos   
        self.listaDeArrays = list()
        if self.ValoresAGraficar[0] == 1:
            self.y1.append(float(VectorAGraficar[0]))
            self.listaDeArrays.append(self.y1)
        if self.ValoresAGraficar[1] == 1:
            self.y2.append(float(VectorAGraficar[1]))
            self.listaDeArrays.append(self.y2)
        if self.ValoresAGraficar[2] == 1:
            self.y3.append(float(VectorAGraficar[2]))
            self.listaDeArrays.append(self.y3)
        if self.ValoresAGraficar[3] == 1:
            self.y4.append(float(VectorAGraficar[3]))
            self.listaDeArrays.append(self.y4)
        for i in range(0, self.cantidadDeValoresAGraficar):
            self.listaDeGraficos[i].plot(self.x, self.listaDeArrays[i], 'c*')
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()   
    def GraficarAPosicionFija(self, VectorAGraficar, posicionSMC, posicionMono):
        self.x.append(posicionMono)
        self.listaDeArrays = list()
        if self.ValoresAGraficar[0] == 1:
            self.y1.append(float(VectorAGraficar[0]))
            self.listaDeArrays.append(self.y1)
        if self.ValoresAGraficar[1] == 1:
            self.y2.append(float(VectorAGraficar[1]))
            self.listaDeArrays.append(self.y2)
        if self.ValoresAGraficar[2] == 1:
            self.y3.append(float(VectorAGraficar[2]))
            self.listaDeArrays.append(self.y3)
        if self.ValoresAGraficar[3] == 1:
            self.y4.append(float(VectorAGraficar[3]))
            self.listaDeArrays.append(self.y4)
        for i in range(0, self.cantidadDeValoresAGraficar):
            self.listaDeGraficos[i].plot(self.x, self.listaDeArrays[i], 'c*')
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
    def GraficarCompletamente(self, VectorAGraficar, posicionSMC, posicionMono):
        posicionX = np.where(self.VectorX == posicionSMC)
        posicionY = np.where(self.VectorY == posicionMono)
#        vectorX = self.VectorX*(2/3)*10 # en picosegundos

        if hasattr(self, 'listaDeColorbars'):
            print(len(self.listaDeColorbars))
            for i in range(0,len(self.listaDeColorbars)):
                self.listaDeColorbars[i].remove()
        self.listaDeColorbars = list()
        if self.ValoresAGraficar[0]==1:
            self.M1[posicionY[0][0],posicionX[0][0]] = float(VectorAGraficar[0]) 
        if self.ValoresAGraficar[1]==1:
            self.M2[posicionY[0][0],posicionX[0][0]] = float(VectorAGraficar[1]) 
        if self.ValoresAGraficar[2]==1:
            self.M3[posicionY[0][0],posicionX[0][0]] = float(VectorAGraficar[2]) 
        if self.ValoresAGraficar[3]==1:
            self.M4[posicionY[0][0],posicionX[0][0]] = float(VectorAGraficar[3]) 
        
        for i in range(0, self.cantidadDeValoresAGraficar):
            self.listaDeGraficos[i].contourf(self.VectorX, self.VectorY, self.listaDeMatrices[i], 20, cmap='RdGy')
            divider = make_axes_locatable(self.listaDeGraficos[i])
            cax = divider.append_axes("right", size="5%", pad=0.05)
            self.listaDeColorbars.append(self.fig.colorbar(self.listaDePlots[i],cax=cax))
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
                            VectorPosicionInicialSMC_mm,
                            VectorPosicionFinalSMC_mm,
                            VectorPasoSMC_mm):
        self.nombreArchivo = nombreArchivo
        global do_run
        for i in range(0,len(VectorPosicionInicialSMC_mm)):
            if do_run == False:
                return
            self.smc.Mover(VectorPosicionInicialSMC_mm[i])
            if i==0:
                self.AdquirirGraficarYGrabarCSV()
            if i>0 and VectorPosicionInicialSMC_mm[i] != VectorPosicionFinalSMC_mm[i-1]:
                self.AdquirirGraficarYGrabarCSV()
            numeroDePasos = abs(int((VectorPosicionFinalSMC_mm[i]-VectorPosicionInicialSMC_mm[i])/VectorPasoSMC_mm[i]))
            for j in range(0,numeroDePasos):
                if do_run == False:
                    return
                self.smc.Mover(VectorPasoSMC_mm[i]+self.smc.posicion)
                self.AdquirirGraficarYGrabarCSV()
    def MedicionAPosicionFijaSMC(self,
                            nombreArchivo,
                            VectorLongitudDeOndaInicial_nm,
                            VectorLongitudDeOndaFinal_nm,
                            VectorPasoMono_nm):
        global do_run
        self.nombreArchivo = nombreArchivo
        for i in range(0,len(VectorLongitudDeOndaInicial_nm)):
            if do_run == False:
                return
            self.mono.Mover(VectorLongitudDeOndaInicial_nm[i])
            if i==0:
                self.AdquirirGraficarYGrabarCSV()
            if i>0 and VectorLongitudDeOndaInicial_nm[i] != VectorLongitudDeOndaFinal_nm[i-1]:
                self.AdquirirGraficarYGrabarCSV()
            numeroDePasos = abs(int((VectorLongitudDeOndaFinal_nm[i]-VectorLongitudDeOndaInicial_nm[i])/VectorPasoMono_nm[i]))
            for j in range(0,numeroDePasos):
                if do_run == False:
                    return
                self.mono.Mover(round(VectorPasoMono_nm[i]+self.mono.posicion,4))
                self.AdquirirGraficarYGrabarCSV()

    def MedicionCompleta(self, 
                         nombreArchivo,
                         VectorPosicionInicialSMC_mm,
                         VectorPosicionFinalSMC_mm,
                         VectorPasoSMC_mm,
                         VectorLongitudDeOndaInicial_nm,
                         VectorLongitudDeOndaFinal_nm,
                         VectorPasoMono_nm):
        self.nombreArchivo = nombreArchivo
        for i in range(0,len(VectorLongitudDeOndaInicial_nm)):
            if do_run == False:
                return
            self.mono.Mover(VectorLongitudDeOndaInicial_nm[i])
            numeroDePasosMono = abs(int((VectorLongitudDeOndaFinal_nm[i]-VectorLongitudDeOndaInicial_nm[i])/VectorPasoMono_nm[i]))
            for j in range(0,numeroDePasosMono+1):
                if do_run == False:
                    return
                for k in range(0,len(VectorPosicionInicialSMC_mm)):
                    if do_run == False:
                        return
                    self.smc.Mover(VectorPosicionInicialSMC_mm[k])
                    if k==0:
                        self.AdquirirGraficarYGrabarCSV()
                    if k>0 and VectorPosicionInicialSMC_mm[k] != VectorPosicionFinalSMC_mm[k-1]:
                        self.AdquirirGraficarYGrabarCSV()
                    numeroDePasosSMC = abs(int((VectorPosicionFinalSMC_mm[k]-VectorPosicionInicialSMC_mm[k])/VectorPasoSMC_mm[k]))
                    for l in range(0,numeroDePasosSMC):
                        if do_run == False:
                            return
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

class Advertencia():
    def __init__(self, texto):
        advertencia = tk.Tk()
        advertencia.title('Atención')
        advertencia.geometry('300x100')
        labelExplicacion = tk.Label(advertencia, text = texto)
        labelExplicacion.place(x=0, y=0)
        def Cerrar():
            advertencia.destroy()
        botonCerrar = tk.Button(advertencia, text = 'Ok', command = Cerrar)
        botonCerrar.place(x=200, y = 40)
        advertencia.mainloop()
class Medicion():
    def IniciarVentana(self, tiempoDeMedicion, tipoDeMedicion, experimento, nombreArchivo, VectorPosicionInicialSMC_mm=0, VectorPosicionFinalSMC_mm=0, VectorPasoSMC_mm=0, VectorLongitudDeOndaInicial_nm=0, VectorLongitudDeOndaFinal_nm=0, VectorPasoMono_nm=0):
        global do_run
        do_run = True
        self.midiendo = tk.Tk()
        self.midiendo.title('Midiendo')
        self.midiendo.geometry('300x100')
        segundos = tiempoDeMedicion%60
        totalMinutos = int(tiempoDeMedicion/60)
        minutos = totalMinutos%60
        horas = int(totalMinutos/60)
        self.labelEstado = tk.Label(self.midiendo, text="Realizando la medicion. Tiempo estimado: " + str(horas) + ' h ' + str(minutos) + ' m ' + str(segundos) + ' s.')
        self.labelEstado.place(x=0, y=0)
        def Cancelar():
            global do_run
            do_run = False
            print('Cancelar')
            self.midiendo.destroy()
        botonCancelar = tk.Button(self.midiendo, text = 'Cancelar', command = Cancelar)
        botonCancelar.place(x=70, y = 40)
        def Finalizar():
            self.midiendo.destroy()
        self.botonFinalizar = tk.Button(self.midiendo, text = 'Finalizar', command = Finalizar)
        self.botonFinalizar.place(x=200, y = 40)
        self.botonFinalizar["state"]="disabled"
        def Medir():
            if tipoDeMedicion == 0:
                experimento.MedicionALambdaFija(nombreArchivo,VectorPosicionInicialSMC_mm,VectorPosicionFinalSMC_mm,VectorPasoSMC_mm)
            if tipoDeMedicion == 1:
                experimento.MedicionAPosicionFijaSMC(nombreArchivo,VectorLongitudDeOndaInicial_nm, VectorLongitudDeOndaFinal_nm, VectorPasoMono_nm)
            if tipoDeMedicion == 2:
                experimento.MedicionCompleta(nombreArchivo, VectorPosicionInicialSMC_mm,VectorPosicionFinalSMC_mm,VectorPasoSMC_mm, VectorLongitudDeOndaInicial_nm, VectorLongitudDeOndaFinal_nm, VectorPasoMono_nm)
            nombreGrafico = nombreArchivo.replace('.csv','')
            experimento.grafico.GuardarGrafico(nombreGrafico)         
            self.CambiarEstadoAFinalizado(nombreArchivo)  
        Medir()
        self.midiendo.mainloop()
    def CambiarEstadoAFinalizado(self, nombreArchivo):
        self.botonFinalizar["state"]="normal"
        print('CambiarEstadoAFinalizado')
        self.labelEstado = tk.Label(self.midiendo, text="Medicion Finalizada. El archivo ha sido guardado con el\n nombre: " + nombreArchivo)
        self.labelEstado.place(x=0, y=0)                       
class Configuracion():
    def __init__(self, experimento, programa):
        self.primeraVez = True
        self.experimento = experimento
        self.programa = programa
        self.b1 = False
        self.b2 = False
        self.b3 = False    
    def AbrirVentana(self):
        raizConfiguracion = tk.Tk()
        raizConfiguracion.title('Pump and Probe Software - Configuración')
        raizConfiguracion.geometry('550x200')
        def SetearPuertoSMC():
            try:
                puertoSMC = int(textoSMC.get())
            except ValueError:
                Advertencia('El valor ingresado debe ser un número entero.')
                return
            try:
                self.experimento.smc.AsignarPuerto('COM' + str(puertoSMC))
            except:
                Advertencia('No se ha podido abrir el puerto serie.')
                return
            self.b1 = self.experimento.smc.Identificar() # Booleano
            if self.b1:
                labelSMCReconocido.config(text = 'Reconocido')
                botonInicializarSMC["state"]="normal"
                botonCalibrarSMC["state"] = "normal"
            else:
                labelSMCReconocido.config(text = 'No reconocido')
                self.experimento.smc.CerrarPuerto()
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
        if self.b1:
            labelSMCReconocido = tk.Label(raizConfiguracion, text = 'Reconocido')
            botonInicializarSMC["state"] = "normal"
            botonCalibrarSMC["state"] = "normal"    
        else:
            labelSMCReconocido = tk.Label(raizConfiguracion)
            botonInicializarSMC["state"] = "disabled"
            botonCalibrarSMC["state"] = "disabled"                
        labelSMCReconocido.place(x=305, y=5)
        def SetearPuertoSMS():
            try:
                puertoSMS = int(textoMono.get())
            except ValueError:
                Advertencia('El valor ingresado debe ser un número entero.')
                return
            try:
                self.experimento.mono.AsignarPuerto('COM' + str(puertoSMS))
            except:
                Advertencia('No se ha podido abrir el puerto serie.')
                return
            b = self.experimento.mono.Identificar() # Booleano
            if b:
                labelSMSReconocido.config(text = 'Reconocido')
                botonInicializarSMS["state"]="normal"
                botonCalibrarSMS["state"] = "normal"
            else:
                labelSMSReconocido.config(text = 'No reconocido')
                self.experimento.mono.CerrarPuerto()
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
        
        if self.b2:
            labelSMSReconocido = tk.Label(raizConfiguracion, text = 'Reconocido')
            botonInicializarSMS["state"] = "normal"
            botonCalibrarSMS["state"] = "normal"                
        else:
            labelSMSReconocido = tk.Label(raizConfiguracion)
            botonInicializarSMS["state"] = "disabled"
            botonCalibrarSMS["state"] = "disabled"                
        labelSMSReconocido.place(x=305, y=30)
        
        def SetearPuertoLockIn():
            try:
                puertoLockIn = int(textoLockIn.get())
            except ValueError:
                Advertencia('El valor ingresado debe ser un número entero.')
                return
            try:
                self.experimento.lockin.AsignarPuerto(str(puertoLockIn))
            except:
                Advertencia('No se ha podido abrir el puerto GPIB.')
                return
            b = self.experimento.lockin.Identificar() # Booleano
            if b:
                labelLockInReconocido.config(text = 'Reconocido')
                botonInicializarLockIn["state"] = "normal"
            else:
                labelLockInReconocido.config(text = 'No reconocido')                
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
        if self.b3:
            labelLockInReconocido = tk.Label(raizConfiguracion, text='Reconocido')
            botonInicializarLockIn["state"] = "normal"
        else:
            labelLockInReconocido = tk.Label(raizConfiguracion)
            botonInicializarLockIn["state"] = "disabled"
        labelLockInReconocido.place(x=305, y=55)
        def MenuPrincipal():
            raizConfiguracion.destroy()
            self.programa.PantallaPrincipal()
        def Salir():
            raizConfiguracion.destroy()                    
        if self.primeraVez:
            botonMenuPrincipal = tk.Button(raizConfiguracion, text = 'Continuar', command = MenuPrincipal)
            botonMenuPrincipal.place(x=200, y=100)
            botonSalir = tk.Button(raizConfiguracion, text = 'Salir', command = Salir)
            botonSalir.place(x=100, y=100)
            self.primeraVez = False
        else:
            botonSalir = tk.Button(raizConfiguracion, text = 'Menu', command = Salir)
            botonSalir.place(x=100, y=100)            
        raizConfiguracion.mainloop()
        
class Programa():    
    def __init__(self):
        self.experimento = Experimento()
        self.configuracion = Configuracion(self.experimento, self)
        self.configuracion.AbrirVentana()
    class PanelValoresAGraficar():
        def __init__(self, raiz, posicion):
            X = posicion[0]
            Y = posicion[1]
            labelGraficos = tk.Label(raiz, text="Valores a graficar: ")
            labelGraficos.place(x=X, y=Y)
            self.Var1 = tk.IntVar()
            tk.Checkbutton(raiz, text='X', variable=self.Var1).place(x=X,y=Y+20)
            self.Var1.set(1)
            self.Var2 = tk.IntVar()
            tk.Checkbutton(raiz, text='Y', variable=self.Var2).place(x=X+40,y=Y+20)
            self.Var3 = tk.IntVar()
            tk.Checkbutton(raiz, text='R', variable=self.Var3).place(x=X,y=Y+40)
            self.Var4 = tk.IntVar()
            tk.Checkbutton(raiz, text='\u03B8', variable=self.Var4).place(x=X+40,y=Y+40)
            self.Var5 = tk.IntVar()
            tk.Checkbutton(raiz, text='X/AUX', variable=self.Var5).place(x=X+80,y=Y+20)
            self.Var6 = tk.IntVar()
            tk.Checkbutton(raiz, text='R/AUX', variable=self.Var6).place(x=X+80,y=Y+40)
        def ObtenerValores(self):
            return (self.Var1.get(), self.Var2.get(), self.Var3.get(), self.Var4.get(), self.Var5.get(), self.Var6.get())
    class PanelEjeX():
        def __init__(self, raiz, posicion):
            X = posicion[0]
            Y = posicion[1]
            labelEjeX = tk.Label(raiz, text="Eje X del gráfico: ")
            labelEjeX.place(x=X, y=Y) 
            choices = ['Tiempo', 'Distancia']
            self.variable = tk.StringVar(raiz)
            self.variable.set('Tiempo')
            w = tk.OptionMenu(raiz, self.variable, *choices)
            w.place(x=X+200,y=Y-7)
        def ObtenerValor(self):
            return(self.variable.get())
    class PanelNombreArchivo():
        def __init__(self, raiz, posicion):
            self.numeroDeMedicion = 1
            X = posicion[0]
            Y = posicion[1]
            labelNombreArchivo = tk.Label(raiz, text="Nombre del archivo :")
            labelNombreArchivo.place(x=X, y=Y)
            self.textoNombreArchivo = tk.Entry(raiz,width=15)
            self.textoNombreArchivo.place(x=X+200, y=Y)
            self.textoNombreArchivo.delete(0, tk.END)
            fecha = date.today()
            fechaEnFormatoString = fecha.strftime("%Y-%m-%d")
            nombre = fechaEnFormatoString + '_' +str(self.numeroDeMedicion) + '.csv'
            self.textoNombreArchivo.insert(0, nombre)        
        def ActualizarNombreArchivo(self):
            self.numeroDeMedicion += 1
            self.textoNombreArchivo.delete(0, tk.END)
            fecha = date.today()
            fechaEnFormatoString = fecha.strftime("%Y-%m-%d")
            nombre = fechaEnFormatoString + '_'+ str(self.numeroDeMedicion) + '.csv'
            self.textoNombreArchivo.insert(0, nombre)        
    class PanelConversor():
        def __init__(self, raiz, posicion):
            X = posicion[0] 
            Y = posicion[1] 
            labelTituloConversor = tk.Label(raiz, text="Conversor de\n mm a fs")
            labelTituloConversor.place(x=X, y=Y)
            labelmm = tk.Label(raiz, text="mm")
            labelmm.place(x=X+115, y=Y-8)
            labelfs = tk.Label(raiz, text="fs")
            labelfs.place(x=X+260, y=Y-8)
            textomm = tk.Entry(raiz,width=15)
            textomm.place(x=X+85, y=Y+17)
            textofs = tk.Entry(raiz,width=15)
            textofs.place(x=X+230, y=Y+17)
            def ConvertirAfs():
                mm = textomm.get()
                fs = round(float(mm)*6666.666,2)
                textofs.delete(0, tk.END)
                textofs.insert(tk.END, fs)
            def ConvertirAmm():
                fs = textofs.get()
                mm = round(float(fs)/6666.666,5)
                textomm.delete(0, tk.END)
                textomm.insert(tk.END, mm)
            botonConvertirAmm = tk.Button(raiz, text="<-", command=ConvertirAmm)
            botonConvertirAmm.place(x=X+180, y=Y+12)
            botonConvertirAfs = tk.Button(raiz, text="->", command=ConvertirAfs)
            botonConvertirAfs.place(x=X+205, y=Y+12)
    class PanelMedicionManual():
        def __init__(self, raiz, posicion, experimento):
            self.experimento = experimento
            X = posicion[0]
            Y = posicion[1]
            labelX = tk.Label(raiz, text = 'X')
            labelX.place(x=X+50, y=Y)
            labelX.config(font=("Courier", 30))
            textoX = tk.Entry(raiz, font=("Courier",20))
            textoX.place(x=X, y=Y+35, height=45, width=130)
            labelY = tk.Label(raiz, text = 'Y')
            labelY.place(x=X+50, y=Y+85)
            labelY.config(font=("Courier", 30))
            textoY = tk.Entry(raiz, font=("Courier",20))
            textoY.place(x=X, y=Y+120, height=45, width=130)
            labelR = tk.Label(raiz, text = 'R')
            labelR.place(x=X+50, y=Y+170)
            labelR.config(font=("Courier", 30))
            textoR = tk.Entry(raiz, font=("Courier",20))
            textoR.place(x=X, y=Y+205, height=45, width=130)
            labelTheta = tk.Label(raiz, text = '\u03B8')
            labelTheta.place(x=X+50, y=Y+255)
            labelTheta.config(font=("Courier", 30))
            textoTheta = tk.Entry(raiz, font=("Courier",20))
            textoTheta.place(x=X, y=Y+290, height=45, width=130)
            labelAuxIn = tk.Label(raiz, text = 'Aux')
            labelAuxIn.place(x=X+25, y=Y+340)
            labelAuxIn.config(font=("Courier", 30))
            textoAuxIn = tk.Entry(raiz, font=("Courier",20))
            textoAuxIn.place(x=X, y=Y+375, height=45, width=130)
            labelCocienteXConAuxIn = tk.Label(raiz, text = 'X/Aux')
            labelCocienteXConAuxIn.place(x=X+5, y=Y+425)
            labelCocienteXConAuxIn.config(font=("Courier", 30))
            textoCocienteXConAuxIn = tk.Entry(raiz, font=("Courier",20))
            textoCocienteXConAuxIn.place(x=X, y=Y+460, height=45, width=130)
            labelCocienteRConAuxIn = tk.Label(raiz, text = 'R/Aux')
            labelCocienteRConAuxIn.place(x=X+5, y=Y+510)
            labelCocienteRConAuxIn.config(font=("Courier", 30))
            textoCocienteRConAuxIn = tk.Entry(raiz, font=("Courier",20))
            textoCocienteRConAuxIn.place(x=X, y=Y+545, height=45, width=130)
            labelFrecuencia = tk.Label(raiz, text = 'f')
            labelFrecuencia.place(x=X+50, y=Y+595)
            labelFrecuencia.config(font=("Courier", 30))
            textoFrecuencia = tk.Entry(raiz, font=("Courier",20))
            textoFrecuencia.place(x=X, y=Y+630, height=45, width=130)
            def IniciarMedicion():
                global t
                t = th.Thread(target=MedicionManual)
                t.do_run = True
                t.start()
            def MedicionManual():
                while t.do_run == True:
                    vectorDeStringsDeDatos = self.experimento.Adquirir()
                    textoX.delete(0, tk.END)
                    textoX.insert(tk.END, str(round(float(vectorDeStringsDeDatos[0]), 6)))
                    textoY.delete(0, tk.END)
                    textoY.insert(tk.END, str(round(float(vectorDeStringsDeDatos[1]), 6)))
                    textoR.delete(0, tk.END)
                    textoR.insert(tk.END, str(round(float(vectorDeStringsDeDatos[2]), 6)))
                    textoTheta.delete(0, tk.END)
                    textoTheta.insert(tk.END, str(round(float(vectorDeStringsDeDatos[3]), 6)))
                    textoAuxIn.delete(0, tk.END)
                    textoAuxIn.insert(tk.END, str(round(float(vectorDeStringsDeDatos[4]), 6)))
                    textoFrecuencia.delete(0, tk.END)
                    textoFrecuencia.insert(tk.END, str(round(float(vectorDeStringsDeDatos[5]), 6))) 
                    cocienteXConAux = 0
                    cocienteRConAux = 0
                    if float(vectorDeStringsDeDatos[4]) != 0:
                        cocienteXConAux = round(float(vectorDeStringsDeDatos[0])/float(vectorDeStringsDeDatos[4]), 6)
                        cocienteRConAux = round(float(vectorDeStringsDeDatos[2])/float(vectorDeStringsDeDatos[4]), 6)
                    else:
                        cocienteXConAux = float('inf')
                        cocienteRConAux = float('inf')
                    textoCocienteXConAuxIn.delete(0, tk.END)
                    textoCocienteXConAuxIn.insert(tk.END, str(cocienteXConAux))
                    textoCocienteRConAuxIn.delete(0, tk.END)
                    textoCocienteRConAuxIn.insert(tk.END, str(cocienteRConAux)) 
            def FrenarMedicion():
                t.do_run = False
            botonIniciarMedicion = tk.Button(raiz, text="Iniciar", command=IniciarMedicion,font=("Courier", 20))
            botonIniciarMedicion.place(x=X, y=Y+600, height=40, width=130)
            botonFrenarMedicion = tk.Button(raiz, text="Frenar", command=FrenarMedicion,font=("Courier", 20))
            botonFrenarMedicion.place(x=X, y=Y+640, height=40, width=130)
    class PanelSeteoNumeroDeConstantesDeTiempo():
        def __init__(self, raiz, posicion, experimento):
            self.experimento = experimento
            X = posicion[0]
            Y = posicion[1]
            labelNumeroDeConstantesDeTiempo = tk.Label(raiz, text = '# de ctes de tiempo (Lock In):')
            labelNumeroDeConstantesDeTiempo.place(x=X, y=Y+5)
            textoNumeroDeConstantesDeTiempo = tk.Entry(raiz, width=5)
            textoNumeroDeConstantesDeTiempo.place(x=X+160, y=Y+7)
            textoNumeroDeConstantesDeTiempo.delete(0, tk.END)
            textoNumeroDeConstantesDeTiempo.insert(0, '1')
            def SetearNumeroDeConstantesDeTiempo():
                try:
                    numeroDeConstantesDeTiempo = int(textoNumeroDeConstantesDeTiempo.get())
                except ValueError:
                    Advertencia('El valor ingresado debe ser un número entero.')
                self.experimento.lockin.CalcularTiempoDeIntegracion(numeroDeConstantesDeTiempo)
            botonSetearNumeroDeConstantesDeTiempo = tk.Button(raiz, text="Setear", command=SetearNumeroDeConstantesDeTiempo)
            botonSetearNumeroDeConstantesDeTiempo.place(x=X+200, y=Y+5)
    class PanelJoggingPlataforma():
        def __init__(self, raiz, posicion, experimento):
            self.experimento = experimento
            X = posicion[0]
            Y = posicion[1]
            labelPosicionSMC = tk.Label(raiz, text = 'Retardo de 0 a 25 (mm) :')
            labelPosicionSMC.place(x=X, y=Y+5)
            labelPasoSMC = tk.Label(raiz, text = 'Paso (mm) (res: 0.0001) :')
            labelPasoSMC.place(x=X, y=Y+50)
            self.textoPosicionSMC = tk.Entry(raiz, font=("Courier",20))
            self.textoPosicionSMC.place(x=X+150, y=Y+7, height=30, width=100)
            textoPasoSMC = tk.Entry(raiz, width=5, font=("Courier",20))
            textoPasoSMC.place(x=X+150, y=Y+50, height=30, width=100)
            self.textoPosicionSMC.delete(0, tk.END)
            self.textoPosicionSMC.insert(0, str(self.experimento.smc.posicion))
            textoPasoSMC.delete(0, tk.END)
            textoPasoSMC.insert(0, '1')
            def IrALaPosicionSMC():
                comando = float(self.textoPosicionSMC.get())
                self.experimento.smc.Mover(comando)
            def MoverHaciaAdelante():
                comando = float(textoPasoSMC.get())
                comandoMultiploDeLaResolucion = self.experimento.smc.resolucion*int(comando/self.experimento.smc.resolucion)
                textoPasoSMC.delete(0, tk.END)
                textoPasoSMC.insert(0, str(comandoMultiploDeLaResolucion)) 
                self.experimento.smc.Mover(comandoMultiploDeLaResolucion+self.experimento.smc.posicion)
                self.Actualizar()
            def MoverHaciaAtras():
                comando = (-1)*float(textoPasoSMC.get())
                comandoMultiploDeLaResolucion = self.experimento.smc.resolucion*int(comando/self.experimento.smc.resolucion)
                textoPasoSMC.delete(0, tk.END)
                textoPasoSMC.insert(0, str(comandoMultiploDeLaResolucion)) 
                self.experimento.smc.Mover(comandoMultiploDeLaResolucion+self.experimento.smc.posicion)
                self.Actualizar()
            botonIrALaPosicionSMC = tk.Button(raiz, text="Mover", command=IrALaPosicionSMC, font=("Courier",15))
            botonIrALaPosicionSMC.place(x=X+255, y=Y+5, height=30, width=80)
            botonMoverHaciaDelante = tk.Button(raiz, text="+", command=MoverHaciaAdelante, font=("Courier",15))
            botonMoverHaciaDelante.place(x=X+255, y=Y+50, height=30, width=30)
            botonMoverHaciaAtras = tk.Button(raiz, text="-", command=MoverHaciaAtras, font=("Courier",15))
            botonMoverHaciaAtras.place(x=X+295, y=Y+50, height=30, width=30)
        def Actualizar(self):
            self.textoPosicionSMC.delete(0, tk.END)
            self.textoPosicionSMC.insert(0, str(self.experimento.smc.posicion))
    class PanelJoggingRedDeDifraccion():
        def __init__(self, raiz, posicion, experimento):
            self.experimento = experimento
            X = posicion[0]
            Y = posicion[1]
            labelPosicionMonocromador = tk.Label(raiz, text = '\u03BB de 200 a 1200 (nm) :')
            labelPosicionMonocromador.place(x=X, y=Y)
            labelPasoMonocromador = tk.Label(raiz, text = 'Paso (mm) (res: 0.3125) :')
            labelPasoMonocromador.place(x=X, y=Y+50)
            self.textoPosicionMonocromador = tk.Entry(raiz, width=5, font=("Courier",20))
            self.textoPosicionMonocromador.place(x=X+150, y=Y+7, height=30, width=100)
            textoPasoMonocromador = tk.Entry(raiz, width=5, font=("Courier",20))
            textoPasoMonocromador.place(x=X+150, y=Y+50, height=30, width=100)
            self.textoPosicionMonocromador.delete(0, tk.END)
            self.textoPosicionMonocromador.insert(0, str(self.experimento.mono.posicion))
            textoPasoMonocromador.delete(0, tk.END)
            textoPasoMonocromador.insert(0, '0.9375')
            def IrALaPosicionMonocromador():
                comando = float(self.textoPosicionMonocromador.get())
                self.experimento.mono.Mover(comando)
            def MoverHaciaAdelante():
                comando = float(textoPasoMonocromador.get())
                comandoMultiploDeLaResolucion = self.experimento.mono.resolucion*int(comando/self.experimento.mono.resolucion)
                textoPasoMonocromador.delete(0, tk.END)
                textoPasoMonocromador.insert(0, str(comandoMultiploDeLaResolucion)) 
                self.experimento.mono.Mover(comandoMultiploDeLaResolucion+self.experimento.mono.posicion)
                self.Actualizar()
            def MoverHaciaAtras():
                comando = (-1)*float(textoPasoMonocromador.get())
                comandoMultiploDeLaResolucion = self.experimento.mono.resolucion*int(comando/self.experimento.mono.resolucion)
                textoPasoMonocromador.delete(0, tk.END)
                textoPasoMonocromador.insert(0, str(comandoMultiploDeLaResolucion)) 
                self.experimento.mono.Mover(comandoMultiploDeLaResolucion+self.experimento.mono.posicion)
                self.Actualizar()
            botonIrALaPosicionMonocromador = tk.Button(raiz, text="Mover", command=IrALaPosicionMonocromador, font=("Courier",15))
            botonIrALaPosicionMonocromador.place(x=X+255, y=Y+5, height=30, width=80)
            botonMoverHaciaDelante = tk.Button(raiz, text="+", command=MoverHaciaAdelante, font=("Courier",15))
            botonMoverHaciaDelante.place(x=X+255, y=Y+50, height=30, width=30)
            botonMoverHaciaAtras = tk.Button(raiz, text="-", command=MoverHaciaAtras, font=("Courier",15))
            botonMoverHaciaAtras.place(x=X+295, y=Y+50, height=30, width=30)   
        def Actualizar(self):
            self.textoPosicionMonocromador.delete(0, tk.END)
            self.textoPosicionMonocromador.insert(0, str(self.experimento.mono.posicion))
    class PanelBarridoEnDistancia():
        def __init__(self, raiz, posicion):
            X = posicion[0] #950
            Y = posicion[1]#140
            labelTituloInicial = tk.Label(raiz, text="Barrido en distancia")
            labelTituloInicial.place(x=X, y=Y)        
        
            labelNumeroDeSubintervalos = tk.Label(raiz, text="Secciones: ")
            labelNumeroDeSubintervalos.place(x=X, y=Y+20)
            textoNumeroDeSubintervalos = tk.Entry(raiz,width=5)
            textoNumeroDeSubintervalos.place(x=X+100, y=Y+25)
            textoNumeroDeSubintervalos.delete(0, tk.END)
            textoNumeroDeSubintervalos.insert(0, '1')        
        
            labelTituloInicial = tk.Label(raiz, text="Posicion Inicial")
            labelTituloInicial.place(x=X, y=Y+45)
            labelTituloFinal = tk.Label(raiz, text="Posicion Final")
            labelTituloFinal.place(x=X+100, y=Y+45)
            labelTituloPaso = tk.Label(raiz, text="Paso")
            labelTituloPaso.place(x=X+200, y=Y+45)
    
            self.textosPosicionInicial = list()
            self.textosPosicionFinal = list()
            self.textosPaso = list()
                    
            def ObtenerSecciones():
                for i in range(0,len(self.textosPosicionInicial)):
                    self.textosPosicionInicial[i].destroy()
                    self.textosPosicionFinal[i].destroy()
                    self.textosPaso[i].destroy()
                self.textosPosicionInicial.clear()
                self.textosPosicionFinal.clear()
                self.textosPaso.clear()
                self.numeroDeSubintervalos = int(textoNumeroDeSubintervalos.get())
                for i in range(0,self.numeroDeSubintervalos):
                    self.textosPosicionInicial.append(tk.Entry(raiz,width=15))
                    self.textosPosicionFinal.append(tk.Entry(raiz,width=15))
                    self.textosPaso.append(tk.Entry(raiz,width=15))
                    self.textosPosicionInicial[i].place(x=X, y=Y+65+i*20)
                    self.textosPosicionFinal[i].place(x=X+100, y=Y+65+i*20)
                    self.textosPaso[i].place(x=X+200, y=Y+65+i*20)
            ObtenerSecciones()    
            botonSiguiente = tk.Button(raiz, text="Ok", command=ObtenerSecciones)
            botonSiguiente.place(x=X+150, y=Y+20)
        def ObtenerValores(self):
            VectorPosicionInicialSMC_mm = np.zeros(self.numeroDeSubintervalos)
            VectorPosicionFinalSMC_mm = np.zeros(self.numeroDeSubintervalos)
            VectorPasoSMC_mm = np.zeros(self.numeroDeSubintervalos)
            for i in range(0,self.numeroDeSubintervalos):
                VectorPosicionInicialSMC_mm[i] = float(self.textosPosicionInicial[i].get())
                VectorPosicionFinalSMC_mm[i] = float(self.textosPosicionFinal[i].get())
                VectorPasoSMC_mm[i] = float(self.textosPaso[i].get())            
            return (VectorPosicionInicialSMC_mm, VectorPosicionFinalSMC_mm, VectorPasoSMC_mm)
    class PanelBarridoEnLongitudesDeOnda():
        def __init__(self, raiz, posicion):
            X = posicion[0]
            Y = posicion[1]
            
            labelTituloBarridoLongitudDeOnda = tk.Label(raiz, text="Barrido en longitud de onda")
            labelTituloBarridoLongitudDeOnda.place(x=X, y=Y)
            labelNumeroDeSubintervalosLongitudDeOnda = tk.Label(raiz, text="Secciones: ")
            labelNumeroDeSubintervalosLongitudDeOnda.place(x=X, y=Y+20)
            textoNumeroDeSubintervalosLongitudDeOnda = tk.Entry(raiz,width=5)
            textoNumeroDeSubintervalosLongitudDeOnda.place(x=X+100, y=Y+25)
            textoNumeroDeSubintervalosLongitudDeOnda.delete(0, tk.END)
            textoNumeroDeSubintervalosLongitudDeOnda.insert(0, '1')        

            labelTituloLongitudDeOndaInicial = tk.Label(raiz, text="\u03BB Inicial")
            labelTituloLongitudDeOndaInicial.place(x=X, y=Y+45)
            labelTituloLongitudDeOndaFinal = tk.Label(raiz, text="\u03BB Final")
            labelTituloLongitudDeOndaFinal.place(x=X+100, y=Y+45)
            labelTituloPasoLongitudDeOnda = tk.Label(raiz, text="Paso")
            labelTituloPasoLongitudDeOnda.place(x=X+200, y=Y+45)
   
            self.textosLongitudDeOndaInicial = list()
            self.textosLongitudDeOndaFinal = list()
            self.textosPasoLongitudDeOnda = list()
        
            def ObtenerSeccionesBarridoEnLongitudDeOnda():
                for i in range(0,len(self.textosLongitudDeOndaInicial)):
                    self.textosLongitudDeOndaInicial[i].destroy()
                    self.textosLongitudDeOndaFinal[i].destroy()
                    self.textosPasoLongitudDeOnda[i].destroy()
                self.textosLongitudDeOndaInicial.clear()
                self.textosLongitudDeOndaFinal.clear()
                self.textosPasoLongitudDeOnda.clear()
                self.numeroDeSubintervalosLongitudDeOnda = int(textoNumeroDeSubintervalosLongitudDeOnda.get())
                for i in range(0,self.numeroDeSubintervalosLongitudDeOnda):
                    self.textosLongitudDeOndaInicial.append(tk.Entry(raiz,width=15))
                    self.textosLongitudDeOndaFinal.append(tk.Entry(raiz,width=15))
                    self.textosPasoLongitudDeOnda.append(tk.Entry(raiz,width=15))
                    self.textosLongitudDeOndaInicial[i].place(x=950, y=425+i*20)
                    self.textosLongitudDeOndaFinal[i].place(x=1050, y=425+i*20)
                    self.textosPasoLongitudDeOnda[i].place(x=1150, y=425+i*20)
            botonSeccionesLongitudDeOnda = tk.Button(raiz, text="Ok", command=ObtenerSeccionesBarridoEnLongitudDeOnda)
            botonSeccionesLongitudDeOnda.place(x=1100, y=380)
            ObtenerSeccionesBarridoEnLongitudDeOnda()
        def ObtenerValores(self):
            VectorLongitudDeOndaInicial_nm = np.zeros(self.numeroDeSubintervalosLongitudDeOnda)
            VectorLongitudDeOndaFinal_nm = np.zeros(self.numeroDeSubintervalosLongitudDeOnda)
            VectorPasoMono_nm = np.zeros(self.numeroDeSubintervalosLongitudDeOnda)
            for i in range(0,self.numeroDeSubintervalosLongitudDeOnda):
                VectorLongitudDeOndaInicial_nm[i] = float(self.textosLongitudDeOndaInicial[i].get())
                VectorLongitudDeOndaFinal_nm[i] = float(self.textosLongitudDeOndaFinal[i].get())
                VectorPasoMono_nm[i] = float(self.textosPasoLongitudDeOnda[i].get())
            return (VectorLongitudDeOndaInicial_nm, VectorLongitudDeOndaFinal_nm, VectorPasoMono_nm)
    def PantallaPrincipal(self):
        raiz = tk.Tk()
        raiz.title('Pump and Probe Software')
        raiz.geometry('1450x825')   
        
        # GRAFICO #
        self.grafico = Grafico()
        canvas = FigureCanvasTkAgg(self.grafico.fig, master=raiz)
        canvas.get_tk_widget().place(x=10,y=90)
        canvas.draw()
        
        # PANEL SETEO DE NUMERO DE CONSTANTES DE TIEMPO DEL LOCK IN#        
        self.panelSeteoNumeroDeConstantesDeTiempo = self.PanelSeteoNumeroDeConstantesDeTiempo(raiz, (700, 10), self.experimento)
        
        # PANEL JOGGING DE LA PLATAFORMA #
        self.panelJoggingPlataforma = self.PanelJoggingPlataforma(raiz, (5, 5), self.experimento)
        
        # PANEL JOGGING DE LA RED DE DIFRACCION #
        self.panelJoggingRedDeDifraccion = self.PanelJoggingRedDeDifraccion(raiz, (350, 5), self.experimento)
        
        # PANEL MEDICION MANUAL #
        self.panelMedicionManual = self.PanelMedicionManual(raiz, (1275, 100), self.experimento)
        
        # PANEL CONVERSOR #
        self.panelConversor = self.PanelConversor(raiz, (700,43))
        
        # BOTON CONFIGURACION #
        fuente = font.Font(size=10)
        botonConfiguracion = tk.Button(raiz, text="Configuración", font=fuente, command=self.configuracion.AbrirVentana, width=20, heigh=2)
        botonConfiguracion.place(x=1050, y=5)
        
        # BARRIDOS #
        labelMediciones = tk.Label(raiz, text = 'Barridos', font=("Arial", 25))
        labelMediciones.place(x=950, y=100)

        # BARRIDO EN POSICIONES DEL SMC #
        self.panelBarridoEnDistancia = self.PanelBarridoEnDistancia(raiz, (950,140))

        def MedirALambdaFija():
            nombreArchivo = self.panelNombreArchivo.textoNombreArchivo.get()
            self.panelNombreArchivo.ActualizarNombreArchivo()
            ejeX = self.panelEjeX.ObtenerValor()
            valoresAGraficar = self.panelValoresAGraficar.ObtenerValores() 
            VectorPosicionInicialSMC_mm = self.panelBarridoEnDistancia.ObtenerValores()[0]
            VectorPosicionFinalSMC_mm = self.panelBarridoEnDistancia.ObtenerValores()[1]
            VectorPasoSMC_mm = self.panelBarridoEnDistancia.ObtenerValores()[2]    
            self.grafico.Configurar(valoresAGraficar,0,ejeX,longitudDeOndaFija_nm=self.experimento.mono.posicion)
            self.experimento.grafico = self.grafico
            raiz.update()
            medicion = Medicion()
            tiempoDeMedicion = int(self.CalcularTiempoDeMedicionALambdaFija(VectorPosicionInicialSMC_mm,VectorPosicionFinalSMC_mm,VectorPasoSMC_mm))                
            medicion.IniciarVentana(tiempoDeMedicion, 0, self.experimento, nombreArchivo, VectorPosicionInicialSMC_mm, VectorPosicionFinalSMC_mm, VectorPasoSMC_mm)
        botonMedirALambdaFija = tk.Button(raiz, text="Barrer", command=MedirALambdaFija)
        botonMedirALambdaFija.place(x=1075, y=300)
    
        
        #BARRIDO EN LONGITUDES DE ONDA#
        self.panelBarridoEnLongitudesDeOnda = self.PanelBarridoEnLongitudesDeOnda(raiz, (950,360))
        
        def MedirAPosicionFija():
            nombreArchivo = self.panelNombreArchivo.textoNombreArchivo.get()
            self.panelNombreArchivo.ActualizarNombreArchivo()
            valoresAGraficar = self.panelValoresAGraficar.ObtenerValores()
            VectorLongitudDeOndaInicial_nm = self.panelBarridoEnLongitudesDeOnda.ObtenerValores()[0]
            VectorLongitudDeOndaFinal_nm = self.panelBarridoEnLongitudesDeOnda.ObtenerValores()[1]
            VectorPasoMono_nm = self.panelBarridoEnLongitudesDeOnda.ObtenerValores()[2]
            self.grafico.Configurar(valoresAGraficar,1,0,posicionFijaSMC_mm = self.experimento.smc.posicion)
            self.experimento.grafico = self.grafico
            raiz.update()            
            medicion = Medicion()
            tiempoDeMedicion = int(self.CalcularTiempoDeMedicionAPosicionFijaSMC(VectorLongitudDeOndaInicial_nm, VectorLongitudDeOndaFinal_nm, VectorPasoMono_nm))
            medicion.IniciarVentana(tiempoDeMedicion, 1, self.experimento, nombreArchivo, VectorLongitudDeOndaInicial_nm=VectorLongitudDeOndaInicial_nm, VectorLongitudDeOndaFinal_nm=VectorLongitudDeOndaFinal_nm, VectorPasoMono_nm=VectorPasoMono_nm)
        botonMedirAPosicionFija = tk.Button(raiz, text="Barrer", command=MedirAPosicionFija)
        botonMedirAPosicionFija.place(x=1075, y=525)
                
        # PANEL EJE X: TIEMPO O DISTANCIA#
        self.panelEjeX = self.PanelEjeX(raiz, (950,720))
        
        # PANEL VALORES A GRAFICAR #
        self.panelValoresAGraficar = self.PanelValoresAGraficar(raiz, (950,650))

        # PANEL NOMBRE ARCHIVO #
        self.panelNombreArchivo = self.PanelNombreArchivo(raiz, (950, 760))
        
        # DOBLE BARRIDO #
        def MedirCompletamente():
            VectorPosicionInicialSMC_mm = self.panelBarridoEnDistancia.ObtenerValores()[0]
            VectorPosicionFinalSMC_mm = self.panelBarridoEnDistancia.ObtenerValores()[1]
            VectorPasoSMC_mm = self.panelBarridoEnDistancia.ObtenerValores()[2]
            VectorLongitudDeOndaInicial_nm = self.panelBarridoEnLongitudesDeOnda.ObtenerValores()[0]
            VectorLongitudDeOndaFinal_nm = self.panelBarridoEnLongitudesDeOnda.ObtenerValores()[1]
            VectorPasoMono_nm = self.panelBarridoEnLongitudesDeOnda.ObtenerValores()[2]
            ejeX = self.panelEjeX.ObtenerValor()
            valoresAGraficar = self.panelValoresAGraficar.ObtenerValores()
            nombreArchivo = self.panelNombreArchivo.textoNombreArchivo.get()
            self.panelNombreArchivo.ActualizarNombreArchivo()
            self.grafico.Configurar(valoresAGraficar, 2, ejeX, VectorPosicionInicialSMC_mm, VectorPosicionFinalSMC_mm, VectorPasoSMC_mm, VectorLongitudDeOndaInicial_nm, VectorLongitudDeOndaFinal_nm, VectorPasoMono_nm)
            self.experimento.grafico = self.grafico            
            raiz.update()
            medicion = Medicion()
            tiempoDeMedicion = int(self.CalcularTiempoDeMedicionCompleta(VectorPosicionInicialSMC_mm, VectorPosicionFinalSMC_mm, VectorPasoSMC_mm, VectorLongitudDeOndaInicial_nm, VectorLongitudDeOndaFinal_nm, VectorPasoMono_nm))
            medicion.IniciarVentana(tiempoDeMedicion, 2, self.experimento, nombreArchivo,  VectorPosicionInicialSMC_mm, VectorPosicionFinalSMC_mm, VectorPasoSMC_mm, VectorLongitudDeOndaInicial_nm, VectorLongitudDeOndaFinal_nm, VectorPasoMono_nm)
        botonMedirCompletamente = tk.Button(raiz, text="Barrido doble", command=MedirCompletamente)
        botonMedirCompletamente.place(x=1075, y=605)

        # PROTOCOLO AL CERRAR PROGRAMA #        

        def AlCerrar():
            self.experimento.smc.address.close()
            self.experimento.mono.address.close()
            os._exit(00)
            raiz.destroy()
        raiz.protocol("WM_DELETE_WINDOW", AlCerrar)

        raiz.mainloop()
    def CalcularTiempoDeMedicionALambdaFija(self,
                                            VectorPosicionInicialSMC_mm,
                                            VectorPosicionFinalSMC_mm,
                                            VectorPasoSMC_mm):
        TiempoDeMedicion = 0
        CantidadDeMedicionesTotal = 0
        TiempoDeDesplazamientoTotal = 0
        TiempoDeDesplazamientoPorPaso = 0
        TiempoMuerto = 0
        TiempoMuerto = abs(VectorPosicionInicialSMC_mm[0]-self.experimento.smc.posicion)/self.experimento.smc.velocidadMmPorSegundo + tiempoAgregadoPlataforma
        for i in range(0, len(VectorPosicionInicialSMC_mm)):
            if i>0 and VectorPosicionInicialSMC_mm[i] != VectorPosicionFinalSMC_mm[i-1]:
                TiempoMuerto = TiempoMuerto + abs(VectorPosicionInicialSMC_mm[i]-VectorPosicionFinalSMC_mm[i-1])/self.experimento.smc.velocidadMmPorSegundo + tiempoAgregadoPlataforma
            CantidadDeMediciones = 0
            CantidadDeMediciones = abs(VectorPosicionFinalSMC_mm[i]-VectorPosicionInicialSMC_mm[i])/VectorPasoSMC_mm[i]
            TiempoDeDesplazamientoPorPaso = VectorPasoSMC_mm[i]/self.experimento.smc.velocidadMmPorSegundo + tiempoAgregadoPlataforma
            TiempoDeDesplazamientoTotal = TiempoDeDesplazamientoTotal + CantidadDeMediciones*TiempoDeDesplazamientoPorPaso
            CantidadDeMedicionesTotal = CantidadDeMedicionesTotal + CantidadDeMediciones
        TiempoDeMedicion = CantidadDeMedicionesTotal*(self.experimento.lockin.TiempoDeIntegracionTotal) + TiempoDeDesplazamientoTotal + TiempoMuerto
        return TiempoDeMedicion    
    def CalcularTiempoDeMedicionAPosicionFijaSMC(self, 
                                                 VectorLongitudDeOndaInicial_nm,
                                                 VectorLongitudDeOndaFinal_nm,
                                                 VectorPasoMono_nm):
        TiempoDeMedicion = 0
        CantidadDeMedicionesTotal = 0
        TiempoDeDesplazamientoTotal = 0
        TiempoDeDesplazamientoPorPaso = 0
        TiempoMuerto = 0
        TiempoMuerto = abs(VectorLongitudDeOndaInicial_nm[0]-self.experimento.mono.posicion)/self.experimento.mono.velocidadNmPorSegundo + tiempoAgregadoMonocromador
        for i in range(0, len(VectorLongitudDeOndaInicial_nm)):
            if i>0 and VectorLongitudDeOndaInicial_nm[i] != VectorLongitudDeOndaFinal_nm[i-1]:
                TiempoMuerto = TiempoMuerto + abs(VectorLongitudDeOndaInicial_nm[i]-VectorLongitudDeOndaFinal_nm[i-1])/self.experimento.mono.velocidadNmPorSegundo + tiempoAgregadoMonocromador
            CantidadDeMediciones = 0
            CantidadDeMediciones = abs(VectorLongitudDeOndaFinal_nm[i]-VectorLongitudDeOndaInicial_nm[i])/VectorPasoMono_nm[i]
            TiempoDeDesplazamientoPorPaso = VectorPasoMono_nm[i]/self.experimento.mono.velocidadNmPorSegundo + tiempoAgregadoMonocromador
            TiempoDeDesplazamientoTotal = TiempoDeDesplazamientoTotal + CantidadDeMediciones*TiempoDeDesplazamientoPorPaso
        TiempoDeMedicion = CantidadDeMedicionesTotal*(self.experimento.lockin.TiempoDeIntegracionTotal) + TiempoDeDesplazamientoTotal + TiempoMuerto
        return TiempoDeMedicion    
    def CalcularTiempoDeMedicionCompleta(self, 
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
        TiempoSMCInicial = abs(VectorPosicionInicialSMC_mm[0]-self.experimento.smc.posicion)/self.experimento.smc.velocidadMmPorSegundo + tiempoAgregadoPlataforma
        TiempoDeRetornoSMC = abs(VectorPosicionFinalSMC_mm[largoVectorSMC-1]-VectorPosicionInicialSMC_mm[0])/self.experimento.smc.velocidadMmPorSegundo + tiempoAgregadoPlataforma
        TiempoMonocromadorInicial = abs(VectorLongitudDeOndaInicial_nm[0]-self.experimento.mono.posicion)/self.experimento.mono.velocidadNmPorSegundo + tiempoAgregadoMonocromador
        for i in range(0, len(VectorPosicionInicialSMC_mm)):
            if i>0 and VectorPosicionInicialSMC_mm[i] != VectorPosicionFinalSMC_mm[i-1]:
                TiempoMuertoSMC = TiempoMuertoSMC + (VectorPosicionInicialSMC_mm[i]-VectorPosicionFinalSMC_mm[i-1])/self.experimento.smc.velocidadMmPorSegundo + tiempoAgregadoPlataforma
            CantidadDeMovimientosSMC = 0
            CantidadDeMovimientosSMC = abs(VectorPosicionFinalSMC_mm[i]-VectorPosicionInicialSMC_mm[i])/VectorPasoSMC_mm[i]
            TiempoDeDesplazamientoPorPaso = VectorPasoSMC_mm[i]/self.experimento.smc.velocidadMmPorSegundo + tiempoAgregadoPlataforma
            TiempoDeDesplazamientoSMC = TiempoDeDesplazamientoSMC + CantidadDeMovimientosSMC*TiempoDeDesplazamientoPorPaso        
        TiempoSMC = TiempoDeDesplazamientoSMC + TiempoSMCInicial + TiempoMuertoSMC + TiempoDeRetornoSMC        
        for j in range(0, len(VectorLongitudDeOndaInicial_nm)):
            if j>0 and VectorLongitudDeOndaInicial_nm[i] != VectorLongitudDeOndaFinal_nm[i-1]:
                TiempoMuertoMono = TiempoMuertoMono + abs(VectorLongitudDeOndaInicial_nm[j]-VectorLongitudDeOndaFinal_nm[j-1])/self.experimento.mono.velocidadNmPorSegundo + tiempoAgregadoMonocromador
            CantidadDeMovimientosMono = 0
            CantidadDeMovimientosMono = abs(VectorLongitudDeOndaFinal_nm[j]-VectorLongitudDeOndaInicial_nm[j])/VectorPasoMono_nm[j]
            CantidadDeMovimientosMonoTotal = CantidadDeMovimientosMonoTotal + CantidadDeMovimientosMono
            TiempoDeDesplazamientoPorPaso = VectorPasoMono_nm[j]/self.experimento.mono.velocidadNmPorSegundo + tiempoAgregadoMonocromador
            TiempoDeDesplazamientoMono = TiempoDeDesplazamientoMono + CantidadDeMovimientosMono*TiempoDeDesplazamientoPorPaso
        TiempoMonocromador = TiempoDeDesplazamientoMono + TiempoMonocromadorInicial + TiempoMuertoMono
        TiempoSMCTotal = TiempoSMC*CantidadDeMovimientosMonoTotal
        TiempoLockIn = CantidadDeMovimientosSMCTotal*CantidadDeMovimientosMonoTotal*(self.experimento.lockin.TiempoDeIntegracionTotal)       
        TiempoTotal = TiempoMonocromador + TiempoSMCTotal + TiempoLockIn        
        return TiempoTotal
    
programa = Programa()