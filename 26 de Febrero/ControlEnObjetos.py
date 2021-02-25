# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 14:49:16 2019

@author: LEC
"""

import serial
import pyvisa
import time
import csv
import pandas
import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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
        self.ConfigurarSMC()
        self.posicion = 0
        self.velocidadMmPorSegundo = 0.16 # mm/s
    def ConfigurarSMC(self):    
        self.address.write(b'1RS\r\n')
        time.sleep(5)
        self.address.write(b'1PW1\r\n')
        time.sleep(0.5)
        self.address.write(b'1HT0\r\n')
        time.sleep(0.2)
#        self.address.write(b'1VA???\r\n')
        time.sleep(0.2)
        self.velocidadStepsPorSegundo = 20 # Como mínimo
        self.address.write(b'1PW0\r\n')
        time.sleep(2)
        self.address.write(b'1OR\r\n')   # HAY QUE ESPERAR QUE EL SMC SE PONGA EN VERDE!!!
        time.sleep(5)
    def Mover(self, PosicionSMC_Step): # Configurar Velocidad
        comando = '1PA' + str(PosicionSMC_Step) + '\r\n'
        self.address.write(comando.encode())
        self.posicion = PosicionSMC_Step
        time.sleep(self.CalcularTiempoSleep(PosicionSMC_Step))
    def CalcularTiempoSleep(self, PosicionSMC_Step):
        TiempoSMC = abs(PosicionSMC_Step-self.posicion)/(self.velocidadStepsPorSegundo)
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
        self.posicion = -87
        self.velocidadNmPorSegundo = 9
        self.ConfigurarMonocromador()
    def ConfigurarMonocromador(self): # AGREGAR SETEO DE MULT Y OFFSET PARA CAMBIAR DE RED
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
        
#%%%
    
class LockIn():
    def __init__(self,puerto):
        rm = pyvisa.ResourceManager()  # OJO EL SELF, PUEDE NO FUNCIONAR
        comando = 'GPIB0::' + str(puerto) + '::INSTR'
        self.address = rm.open_resource(comando)
        self.puerto = puerto
        self.ConfigurarLockIn()
    def ConfigurarLockIn(self):
        self.address.write("OUTX1") #Setea en GPIB=1 o RSR232=0
        self.address.write("FMOD0") #Setea el Lock In con fuente externa de modulacion---> interna=1
        self.address.write("RSLP1") #Setea Slope TTL up ---> Sin=0, TTLdown=2
        self.address.write("ISRC0") #Setea la inpunt configuration---->0=A, 1=a-b, 2,3=I en distintas escalas
        self.address.write("IGND1") #Setea ground=1 o float=0
        self.address.write("ICPL0") #Setea Coupling en AC=0 o DC=1
        self.address.write("ILIN3") #Todos los filtros activados
        self.address.write("RMOD0") #Reserva dinamica 0=HR, 1=Normal, 2=LN
        self.address.write("OFSL0") #Setea Low Pass Filter Slope en 0=6, 1=12, 2=18 y 3=24 DB/octava
        self.address.write("SYNC0") #Synchronous Filter off=0 or on below 200hz=1
        self.address.write("OVRM1") #Setea Remote Control Override en on=1, off=0
        self.address.write("LOCL0") #Setea control en Local=0, Remote=1, Remote Lockout=2
    def CalcularTiempoDeIntegracion(self, NumeroDeConstantesDeTiempo):
        TiempoDeIntegracion = 0
        a = self.address.query("OFLT?")
        a = a.replace('\n','')
        a = int(a)
        if (a % 2) == 0:
            TiempoDeIntegracion = 10*(10^(-6))*(10^(a/2))
        else:
            TiempoDeIntegracion = 30*(10^(-6))*(10^((a-1)/2))
        self.TiempoDeIntegracionTotal = TiempoDeIntegracion*NumeroDeConstantesDeTiempo

#%%%        

class Grafico(): 
    def __init__(self, ValoresAGraficar, TipoDeMedicion, ejeX):
        self.TipoDeMedicion = TipoDeMedicion
        self.ValoresAGraficar = ValoresAGraficar
        self.ejeX = ejeX
        self.x = list()
        self.z = list()
        self.yd1 = list(), list()
        self.yd2 = list(), list()
        self.yd3 = list(), list()
        self.yd4 = list(), list()
        self.y1 = list()
        self.y2 = list()
        self.y3 = list()
        self.y4 = list()   
        self.fig = plt.figure(figsize=(13,13))
        self.ax1 = self.fig.add_subplot(221)
        self.ax2 = self.fig.add_subplot(222)
        self.ax3 = self.fig.add_subplot(223)
        self.ax4 = self.fig.add_subplot(224)        
        
    def GraficarALambdaFija(self, VectorAGraficar, posicionSMC, posicionMono):
        if self.ejeX == 'Distancia':
            self.x.append(posicionSMC)
        else:
            self.x.append((posicionSMC)*(2/3)*(10^(-11))) # en segundos
        if self.ValoresAGraficar(0)==1:
            self.y1.append(VectorAGraficar(0)) 
            self.ax1.plot(self.x,self.y1,'c*')
        if self.ValoresAGraficar(1)==1:
            self.y2.append(VectorAGraficar(1))
            self.ax2.plot(self.x,self.y2,'m*')
        if self.ValoresAGraficar(2)==1:
            self.y3.append(VectorAGraficar(2))
            self.ax3.plot(self.x,self.y3,'y*')
        if self.ValoresAGraficar(3)==1:
            self.y4.append(VectorAGraficar(3))
            self.ax4.plot(self.x,self.y4,'k*')
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        #Nombres y escalas de ejes    
    
    def GraficarAPosicionFija(self, VectorAGraficar, posicionSMC, posicionMono):
        self.x.append(posicionMono)
        if self.ValoresAGraficar(0)==1:
            self.y1.append(VectorAGraficar(0)) 
            self.ax1.plot(self.x,self.y1,'c*')
        if self.ValoresAGraficar(1)==1:
            self.y2.append(VectorAGraficar(1))
            self.ax2.plot(self.x,self.y2,'m*')
        if self.ValoresAGraficar(2)==1:
            self.y3.append(VectorAGraficar(2))
            self.ax3.plot(self.x,self.y3,'y*')
        if self.ValoresAGraficar(3)==1:
            self.y4.append(VectorAGraficar(3))
            self.ax4.plot(self.x,self.y4,'k*')
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        #Nombres y escalas de ejes
    
    def GraficarCompletamente(self, VectorAGraficar, posicionSMC, posicionMono):
        if self.ejeX == 'Distancia':
            self.x.append(posicionSMC)
        else:
            self.x.append((posicionSMC)*(2/3)*(10^(-11)))
        self.z.append(posicionMono)
        X, Z = np.meshgrid(self.x,self.z)
        if self.ValoresAGraficar(0)==1:
            self.yd1[0].append(VectorAGraficar(0)) 
            self.yd1[1].append(VectorAGraficar(0)) 
            self.plot1 = self.ax1.contourf(self.x, self.y, Z, 20, cmap='RdGy')
        if self.ValoresAGraficar(1)==1:
            self.yd2[0].append(VectorAGraficar(1)) 
            self.yd2[1].append(VectorAGraficar(1)) 
            self.plot2 = self.ax2.contourf(self.x, self.y, Z, 20, cmap='RdGy')
        if self.ValoresAGraficar(2)==1:
            self.yd3[0].append(VectorAGraficar(2)) 
            self.yd3[1].append(VectorAGraficar(2)) 
            self.plot3 = self.ax3.contourf(self.x, self.y, Z, 20, cmap='RdGy')
        if self.ValoresAGraficar(3)==1:
            self.yd4[0].append(VectorAGraficar(3)) 
            self.yd4[1].append(VectorAGraficar(3)) 
            self.plot4 = self.ax4.contourf(self.x, self.y, Z, 20, cmap='RdGy')
        self.fig.canvas.draw()
        self.fig.canvas.flush_events() 

#FALTAN VALORES INICIALES DE X y Z PARA ARMAR EL GRAFICO 3D

    def PonerColorbars(self):
        if self.ValoresAGraficar(0)==1:
            plt.colorbar(self.plot1)
        if self.ValoresAGraficar(1)==1:
            plt.colorbar(self.plot2)
        if self.ValoresAGraficar(2)==1:
            plt.colorbar(self.plot3)
        if self.ValoresAGraficar(3)==1:
            plt.colorbar(self.plot4)

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
# HAY QUE COMENTAR LA LINEA DE GRAFICAR EN ADQUIRIR PARA CORRER SOLO ESTA CLASE
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
            self.smc.Mover(VectorPosicionInicialSMC_mm[i])
            self.Adquirir()
            numeroDePasos = int((VectorPosicionFinalSMC_mm[i]-VectorPosicionInicialSMC_mm[i])//VectorPasoSMC_mm[i])
            for j in range(0,numeroDePasos):
                self.smc.Mover(VectorPasoSMC_mm[i]+self.smc.posicion)
                self.Adquirir()
        
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
            self.Adquirir()
            numeroDePasos = int((VectorLongitudDeOndaFinal_nm[i]-VectorLongitudDeOndaInicial_nm[i])//VectorPasoMono_nm[i])
            for j in range(0,numeroDePasos):
                self.mono.Mover(VectorPasoMono_nm[i]+self.mono.posicion)
                self.Adquirir()
    
    def Adquirir(self):
        with open(self.nombreArchivo, 'a') as csvfile:
            filewriter = csv.writer(csvfile, delimiter=',')
            time.sleep(self.lockin.TiempoDeIntegracionTotal)
            a = LockIn.query("SNAP?1,2{,3,4,5,9}") # X,Y,R,THETA,AUX1,FREC
            a = a.replace('\n','')
            a = a + ',' + str(self.smc.posicion) + ',' + str(self.mono.posicion)
            b = a.split(',')
            filewriter.writerow(b)
            self.grafico.Graficar(b,self.smc.posicion,self.mono.posicion)
            
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
            numeroDePasosMono = int((VectorLongitudDeOndaFinal_nm[i]-VectorLongitudDeOndaFinal_nm[i])//VectorPasoMono_nm[i])
            for j in range(0,numeroDePasosMono):
                for k in range(0,len(VectorPosicionInicialSMC_mm)):
                    self.smc.Mover(VectorPosicionInicialSMC_mm[k])
                    self.Adquirir()
                    numeroDePasosSMC = int((VectorPosicionFinalSMC_mm[k]-VectorPosicionInicialSMC_mm[k])//VectorPasoSMC_mm[k])
                    for l in range(0,numeroDePasosSMC):
                        self.smc.Mover(VectorPasoSMC_mm[k]+self.smc.posicion)
                        self.Adquirir()
                self.mono.Mover(VectorPasoMono_nm[i] + self.mono.posicion)
        
#%%%
       
class Programa():     
    def Iniciar(self):
        raiz = tk.Tk()
        raiz.title('Pump and Probe Software')
        raiz.geometry('1000x800')   
        def SetearPuertosBoton():
            raiz.destroy()
            self.SetearPuertos()
        btn1 = tk.Button(raiz, text="Setear Puertos", command=SetearPuertosBoton)
        btn1.grid(column=1, row=0)
        raiz.mainloop()
    
    def ProgramaMedicionALambdaFija(self):
        raiz1 = tk.Tk()
        raiz1.title('Pump and Probe Software - Medicion a Lambda Fija')
        raiz1.geometry('1000x800')
        
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
            BotonV1 = tk.Checkbutton(raiz1, text='X', variable=Var1).grid(column=0,row=18)
            
            Var2 = tk.IntVar()
            BotonV2 = tk.Checkbutton(raiz1, text='Y', variable=Var2).grid(column=0,row=19)
            
            Var3 = tk.IntVar()
            BotonV3 = tk.Checkbutton(raiz1, text='R', variable=Var3).grid(column=0,row=18, sticky=tk.E)
            
            Var4 = tk.IntVar()
            BotonV4 = tk.Checkbutton(raiz1, text='\u03B8', variable=Var4).grid(column=0,row=19, sticky=tk.E)
            

            labelEjeX = tk.Label(raiz1, text="Seleccione la magnitud que desea graficar en el eje X:")
            labelEjeX.grid(column=0, row=20)

            choices = ['Tiempo', 'Distancia']
            variable = tk.StringVar(raiz1)
            variable.set('Tiempo')
            w = tk.OptionMenu(raiz1, variable, *choices)
            w.grid(column=0,row=21)
            
            
            nombreArchivo = textoNombreArchivo.get()
            numeroDeConstantesDeTiempo = int(textoNumeroDeConstantesDeTiempo.get())
            longitudDeOndaFija_nm = float(textoLongitudDeOndaFija.get())
        
            def IniciarMedicion():
                ejeX = variable.get()
                ValoresAGraficar = (Var1.get(),Var2.get(),Var3.get(),Var4.get())
                self.grafico = Grafico(ValoresAGraficar,0,ejeX)
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
                raizMedicion = tk.Tk()
                raizMedicion.title('Pump and Probe Software - Midiendo a Lambda Fija')
                raizMedicion.geometry('1000x1000')   
                labelEstado = tk.Label(raizMedicion, text="Realizando la medicion. Tiempo estimado:" + tiempoDeMedicion + 'segundos')
                labelEstado.grid(column=0, row=0)
                
                canvas = FigureCanvasTkAgg(self.grafico.fig, master=raizMedicion)
                canvas.get_tk_widget().grid(row=1,column=0)
                canvas.draw()
                self.experimento.grafico = self.grafico
                self.experimento.MedicionALambdaFija(nombreArchivo,numeroDeConstantesDeTiempo,longitudDeOndaFija_nm,VectorPosicionInicialSMC_mm,VectorPosicionFinalSMC_mm,VectorPasoSMC_mm)
                self.grafico.GuardarGrafico(nombreArchivo)
                labelEstado = tk.Label(raizMedicion, text="Medicion Finalizada. El archivo ha sido guardado con el nombre:" + nombreArchivo)
                labelEstado.grid(column=0, row=0)
                
                def Finalizar():
                    raizMedicion.destroy()    
                botonFinalizar = tk.Button(raizMedicion, text="Finalizar", command=Finalizar)
                botonFinalizar.grid(column=1, row=1)
                raizMedicion.mainloop()
                
            botonIniciarMedicion = tk.Button(raiz1, text="Iniciar Medicion", command=IniciarMedicion)
            botonIniciarMedicion.grid(column=1, row=22)
       
        botonSiguiente = tk.Button(raiz1, text="Siguiente", command=SiguienteDeLambdaFija)
        botonSiguiente.grid(column=1, row=4)
        raiz1.mainloop()
    
    def CalcularTiempoDeMedicionALambdaFija(self, numeroDeConstantesDeTiempo,
                                            longitudDeOndaFija_nm,
                                            VectorPosicionInicialSMC_mm,
                                            VectorPosicionFinalSMC_mm,
                                            VectorPasoSMC_mm):
        TiempoDeMedicion = 0
        CantidadDeMediciones = 0
        TiempoDeDesplazamientoTotal = 0
        TiempoDeDesplazamientoPorPaso = 0
        TiempoMuerto = 0
        TiempoMuerto = abs(VectorPosicionInicialSMC_mm[0]-self.experimento.smc.posicion)/self.experimento.smc.velocidadMmPorSegundo
        TiempoMonocromador = abs(longitudDeOndaFija_nm-self.experimento.mono.posicion)/self.experimento.monocromador.velocidadNmPorSegundo
        for i in range(0, len(VectorPosicionInicialSMC_mm)):
            if i>0:
                TiempoMuerto = TiempoMuerto + abs(VectorPosicionInicialSMC_mm[i]-VectorPosicionFinalSMC_mm[i-1])/self.experimento.smc.velocidadMmPorSegundo
            CantidadDeMediciones = CantidadDeMediciones + abs(VectorPosicionFinalSMC_mm[i]-VectorPosicionInicialSMC_mm[i])/VectorPasoSMC_mm[i]
            TiempoDeDesplazamientoPorPaso = VectorPasoSMC_mm[i]/self.experimento.smc.velocidadMmPorSegundo
            TiempoDeDesplazamientoTotal = TiempoDeDesplazamientoTotal + CantidadDeMediciones*TiempoDeDesplazamientoPorPaso
        TiempoDeMedicion = CantidadDeMediciones*(self.experimento.lockin.CalcularTiempoDeIntegracion(numeroDeConstantesDeTiempo)) + TiempoDeDesplazamientoTotal + TiempoMuerto + TiempoMonocromador
        return TiempoDeMedicion
    
    def CalcularTiempoDeMedicionAPosicionFijaSMC(self, numeroDeConstantesDeTiempo,
                                                 posicionFijaSMC_mm,
                                                 VectorLongitudDeOndaInicial_nm,
                                                 VectorLongitudDeOndaFinal_nm,
                                                 VectorPasoMono_nm):
        TiempoDeMedicion = 0
        CantidadDeMediciones = 0
        TiempoDeDesplazamientoTotal = 0
        TiempoDeDesplazamientoPorPaso = 0
        TiempoMuerto = 0
        TiempoMuerto = abs(VectorLongitudDeOndaInicial_nm[0]-self.experimento.mono.posicion)/self.experimento.mono.velocidadNmPorSegundo
        TiempoSMC = abs(posicionFijaSMC_mm-self.experimento.smc.posicion)/self.experimento.smc.velocidadMmPorSegundo
        for i in range(0, len(VectorLongitudDeOndaInicial_nm)):
            if i>0:
                TiempoMuerto = TiempoMuerto + abs(VectorLongitudDeOndaInicial_nm[i]-VectorLongitudDeOndaFinal_nm[i-1])/self.experimento.mono.velocidadNmPorSegundo
            CantidadDeMediciones = CantidadDeMediciones + abs(VectorLongitudDeOndaFinal_nm[i]-VectorLongitudDeOndaInicial_nm[i])/VectorPasoMono_nm[i]
            TiempoDeDesplazamientoPorPaso = VectorPasoMono_nm[i]/self.experimento.mono.velocidadNmPorSegundo
            TiempoDeDesplazamientoTotal = TiempoDeDesplazamientoTotal + CantidadDeMediciones*TiempoDeDesplazamientoPorPaso
        TiempoDeMedicion = CantidadDeMediciones*(self.experimento.lockin.CalcularTiempoDeIntegracion(numeroDeConstantesDeTiempo)) + TiempoDeDesplazamientoTotal + TiempoMuerto + TiempoSMC
        return TiempoDeMedicion    

#HASTA ACA MODIFIQUE

    def CalcularTiempoDeMedicionCompleta(self, numeroDeConstantesDeTiempo,
                                         VectorPosicionInicialSMC_Stp,
                                         VectorPosicionFinalSMC_Stp,
                                         VectorPasoSMC_Stp,
                                         VectorLongitudDeOndaInicial_Stp,
                                         VectorLongitudDeOndaFinal_Stp,
                                         VectorPasoMono_Stp):
        TiempoDeMedicion = 0
        CantidadDeMediciones = 0
        TiempoDeDesplazamientoSMC = 0
        TiempoDeDesplazamientoPorPaso = 0
        TiempoDeDesplazamientoMono = 0
        TiempoMuertoSMC = 0
        TiempoMuertoMono = 0
        largoVectorSMC = len(VectorPosicionInicialSMC_Stp)
        TiempoSMCInicial = (VectorPosicionInicialSMC_Stp[0]-self.experimento.smc.posicion)/1000
        TiempoDeRetornoSMC = (VectorPosicionFinalSMC_Stp[largoVectorSMC-1]-VectorPosicionInicialSMC_Stp[0])/1000
        TiempoMonocromadorInicial = (VectorLongitudDeOndaInicial_Stp[0]-self.experimento.mono.posicion)/100

        for i in range(0, len(VectorPosicionInicialSMC_Stp)):
            if i>0:
                TiempoMuertoSMC = TiempoMuertoSMC + (VectorPosicionInicialSMC_Stp[i]-VectorPosicionFinalSMC_Stp[i-1])/1000
            CantidadDeMediciones = CantidadDeMediciones + (VectorPosicionFinalSMC_Stp[i]-VectorPosicionInicialSMC_Stp[i])/VectorPasoSMC_Stp[i]
            TiempoDeDesplazamientoPorPaso = VectorPasoSMC_Stp[i]/1000
            TiempoDeDesplazamientoSMC = TiempoDeDesplazamientoSMC + CantidadDeMediciones*TiempoDeDesplazamientoPorPaso
        
        TiempoSMC = TiempoDeDesplazamientoSMC + TiempoSMCInicial + TiempoMuertoSMC + TiempoDeRetornoSMC
        
        for j in range(0, len(VectorLongitudDeOndaInicial_Stp)):
            if j>0:
                TiempoMuertoMono = TiempoMuertoMono + (VectorLongitudDeOndaInicial_Stp[j]-VectorLongitudDeOndaFinal_Stp[j-1])/100
            CantidadDeMovimientos = CantidadDeMovimientos + (VectorLongitudDeOndaFinal_Stp[j]-VectorLongitudDeOndaInicial_Stp[j])/VectorPasoMono_Stp[j]
            TiempoDeDesplazamientoPorPaso = VectorPasoMono_Stp[j]/100
            TiempoDeDesplazamientoMono = TiempoDeDesplazamientoMono + CantidadDeMovimientos*TiempoDeDesplazamientoPorPaso
            
        TiempoMonocromador = TiempoDeDesplazamientoMono + TiempoMonocromadorInicial + TiempoMuertoMono
        TiempoSMCTotal = TiempoSMC*CantidadDeMovimientos
        TiempoLockIn = CantidadDeMediciones*CantidadDeMovimientos*(self.experimento.lockin.CalcularTiempoDeIntegracion(numeroDeConstantesDeTiempo))
        
        TiempoTotal = TiempoMonocromador + TiempoSMCTotal + TiempoLockIn
        
        return TiempoTotal
    
    
    def ProgramaMedicionAPosicionFija(self):
        raiz2 = tk.Tk()
        raiz2.title('Pump and Probe Software - Medicion a Posicion Fija')
        raiz2.geometry('1000x800')
        
        labelNombreArchivo = tk.Label(raiz2, text="Ingrese el nombre del archivo con la extensión\n .csv. Por ejemplo: datos2.csv")
        labelNombreArchivo.grid(column=0, row=0)
        textoNombreArchivo = tk.Entry(raiz2,width=15)
        textoNombreArchivo.grid(column=1, row=0)
        
        labelNumeroDeConstantesDeTiempo = tk.Label(raiz2, text="Ingrese el número de constantes de tiempo de integracion\n del Lock-In. Debe ser un número entero positivo.")
        labelNumeroDeConstantesDeTiempo.grid(column=0, row=1)
        textoNumeroDeConstantesDeTiempo = tk.Entry(raiz2,width=15)
        textoNumeroDeConstantesDeTiempo.grid(column=1, row=1)
    
        labelPosicionFijaSMC = tk.Label(raiz2, text="Ingrese la posición fija de la plataforma de retardo a la que desea\n realizar la medición. Debe ser un valor entre 0 y 25 milímetros.")
        labelPosicionFijaSMC.grid(column=0, row=2)
        textoPosicionFijaSMC = tk.Entry(raiz2,width=15)
        textoPosicionFijaSMC.grid(column=1, row=2)
    
        labelNumeroDeSubintervalos = tk.Label(raiz2, text="Ingrese la cantidad de secciones\n del barrido de longitud de onda.")
        labelNumeroDeSubintervalos.grid(column=0, row=3)
        textoNumeroDeSubintervalos = tk.Entry(raiz2,width=15)
        textoNumeroDeSubintervalos.grid(column=1, row=3)
        
        def SiguienteDePosicionFijaSMC():
            numeroDeSubintervalos = int(textoNumeroDeSubintervalos.get())
            labelTituloInicial = tk.Label(raiz2, text="Ingresar en milímetros:\n desde 0 a 25")
            labelTituloInicial.grid(column=0, row=5)
            labelTituloInicial = tk.Label(raiz2, text="Posicion Inicial")
            labelTituloInicial.grid(column=0, row=5, sticky=tk.E)
            labelTituloFinal = tk.Label(raiz2, text="Posicion Final")
            labelTituloFinal.grid(column=1, row=5)
            labelTituloPaso = tk.Label(raiz2, text="Paso")
            labelTituloPaso.grid(column=2, row=5)
        
            labelTituloConversor = tk.Label(raiz2, text="Conversor de mm a fs")
            labelTituloConversor.grid(column=3, row=0)
            labelmm = tk.Label(raiz2, text="mm")
            labelmm.grid(column=3, row=1)
            labelfs = tk.Label(raiz2, text="fs")
            labelfs.grid(column=5, row=1)
            textomm = tk.Entry(raiz2,width=15)
            textomm.grid(column=3, row=2)
            textofs = tk.Entry(raiz2,width=15)
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


            botonConvertirAmm = tk.Button(raiz2, text="<-", command=ConvertirAmm)
            botonConvertirAmm.grid(column=4, row=1)
            
            botonConvertirAfs = tk.Button(raiz2, text="->", command=ConvertirAfs)
            botonConvertirAfs.grid(column=4, row=2)
        
        
            if numeroDeSubintervalos>=1:
                textoPosicionInicial1 = tk.Entry(raiz2,width=15)
                textoPosicionInicial1.grid(column=0, row=6, sticky=tk.E)
                textoPosicionFinal1 = tk.Entry(raiz2,width=15)
                textoPosicionFinal1.grid(column=1, row=6)
                textoPaso1 = tk.Entry(raiz2,width=15)
                textoPaso1.grid(column=2, row=6)
            if numeroDeSubintervalos>=2:
                textoPosicionInicial2 = tk.Entry(raiz2,width=15)
                textoPosicionInicial2.grid(column=0, row=7, sticky=tk.E)
                textoPosicionFinal2 = tk.Entry(raiz2,width=15)
                textoPosicionFinal2.grid(column=1, row=7)
                textoPaso2 = tk.Entry(raiz2,width=15)
                textoPaso2.grid(column=2, row=7)
            if numeroDeSubintervalos>=3:
                textoPosicionInicial3 = tk.Entry(raiz2,width=15)
                textoPosicionInicial3.grid(column=0, row=8, sticky=tk.E)
                textoPosicionFinal3 = tk.Entry(raiz2,width=15)
                textoPosicionFinal3.grid(column=1, row=8)
                textoPaso3 = tk.Entry(raiz2,width=15)
                textoPaso3.grid(column=2, row=8)
            if numeroDeSubintervalos>=4:
                textoPosicionInicial4 = tk.Entry(raiz2,width=15)
                textoPosicionInicial4.grid(column=0, row=9, sticky=tk.E)
                textoPosicionFinal4 = tk.Entry(raiz2,width=15)
                textoPosicionFinal4.grid(column=1, row=9)
                textoPaso4 = tk.Entry(raiz2,width=15)
                textoPaso4.grid(column=2, row=9)
            if numeroDeSubintervalos>=5:
                textoPosicionInicial5 = tk.Entry(raiz2,width=15)
                textoPosicionInicial5.grid(column=0, row=10, sticky=tk.E)
                textoPosicionFinal5 = tk.Entry(raiz2,width=15)
                textoPosicionFinal5.grid(column=1, row=10)
                textoPaso5 = tk.Entry(raiz2,width=15)
                textoPaso5.grid(column=2, row=10)
            if numeroDeSubintervalos>=6:
                textoPosicionInicial6 = tk.Entry(raiz2,width=15)
                textoPosicionInicial6.grid(column=0, row=12,sticky=tk.E)
                textoPosicionFinal6 = tk.Entry(raiz2,width=15)
                textoPosicionFinal6.grid(column=1, row=12)
                textoPaso6 = tk.Entry(raiz2,width=15)
                textoPaso6.grid(column=2, row=12)
            if numeroDeSubintervalos>=7:
                textoPosicionInicial7 = tk.Entry(raiz2,width=15)
                textoPosicionInicial7.grid(column=0, row=13,sticky=tk.E)
                textoPosicionFinal7 = tk.Entry(raiz2,width=15)
                textoPosicionFinal7.grid(column=1, row=13)
                textoPaso7 = tk.Entry(raiz2,width=15)
                textoPaso7.grid(column=2, row=13)
            if numeroDeSubintervalos>=8:
                textoPosicionInicial8 = tk.Entry(raiz2,width=15)
                textoPosicionInicial8.grid(column=0, row=14,sticky=tk.E)
                textoPosicionFinal8 = tk.Entry(raiz2,width=15)
                textoPosicionFinal8.grid(column=1, row=14)
                textoPaso8 = tk.Entry(raiz2,width=15)
                textoPaso8.grid(column=2, row=14)
            if numeroDeSubintervalos>=9:
                textoPosicionInicial9 = tk.Entry(raiz2,width=15)
                textoPosicionInicial9.grid(column=0, row=15,sticky=tk.E)
                textoPosicionFinal9 = tk.Entry(raiz2,width=15)
                textoPosicionFinal9.grid(column=1, row=15)
                textoPaso9 = tk.Entry(raiz2,width=15)
                textoPaso9.grid(column=2, row=15)
            if numeroDeSubintervalos>=10:
                textoPosicionInicial10 = tk.Entry(raiz2,width=15)
                textoPosicionInicial10.grid(column=0, row=16,sticky=tk.E)
                textoPosicionFinal10 = tk.Entry(raiz2,width=15)
                textoPosicionFinal10.grid(column=1, row=16)
                textoPaso10 = tk.Entry(raiz2,width=15)
                textoPaso10.grid(column=2, row=16)

            labelGraficos = tk.Label(raiz2, text="Seleccione los valores que desea graficar\n en función de la longitud de onda:")
            labelGraficos.grid(column=0, row=17)
            
            
            Var1 = tk.IntVar()
            BotonV1 = tk.Checkbutton(raiz2, text='X', variable=Var1).grid(column=0,row=18)
            
            Var2 = tk.IntVar()
            BotonV2 = tk.Checkbutton(raiz2, text='Y', variable=Var2).grid(column=0,row=19)
            
            Var3 = tk.IntVar()
            BotonV3 = tk.Checkbutton(raiz2, text='R', variable=Var3).grid(column=0,row=18, sticky=tk.E)
            
            Var4 = tk.IntVar()
            BotonV4 = tk.Checkbutton(raiz2, text='\u03B8', variable=Var4).grid(column=0,row=19, sticky=tk.E)
        
        
        
        
            nombreArchivo = textoNombreArchivo.get()
            numeroDeConstantesDeTiempo = int(textoNumeroDeConstantesDeTiempo.get())
            posicionFijaSMC_Stp = int(float(textoPosicionFijaSMC.get())*10000)
        
            def IniciarMedicion():
                ValoresAGraficar = (Var1.get(),Var2.get(),Var3.get(),Var4.get())
                self.experimento.grafico = Grafico(ValoresAGraficar,1,0)
                VectorLongitudDeOndaInicial_Stp = np.zeros(numeroDeSubintervalos)
                VectorLongitudDeOndaFinal_Stp = np.zeros(numeroDeSubintervalos)
                VectorPasoMono_Stp = np.zeros(numeroDeSubintervalos)
                if numeroDeSubintervalos>=1:
                    VectorLongitudDeOndaInicial_Stp[0] = int(float(textoPosicionInicial1.get())/0.03125)
                    VectorLongitudDeOndaFinal_Stp[0] = int(float(textoPosicionFinal1.get())/0.03125)
                    VectorPasoMono_Stp[0] = int(float(textoPaso1.get())/0.03125)
                if numeroDeSubintervalos>=2:
                    VectorLongitudDeOndaInicial_Stp[1] = int(float(textoPosicionInicial2.get())/0.03125)
                    VectorLongitudDeOndaFinal_Stp[1] = int(float(textoPosicionFinal2.get())/0.03125)
                    VectorPasoMono_Stp[1] = int(float(textoPaso2.get())/0.03125)
                if numeroDeSubintervalos>=3:
                    VectorLongitudDeOndaInicial_Stp[2] = int(float(textoPosicionInicial3.get())/0.03125)
                    VectorLongitudDeOndaFinal_Stp[2] = int(float(textoPosicionFinal3.get())/0.03125)
                    VectorPasoMono_Stp[2] = int(float(textoPaso3.get())/0.03125)
                if numeroDeSubintervalos>=4:
                    VectorLongitudDeOndaInicial_Stp[3] = int(float(textoPosicionInicial4.get())/0.03125)
                    VectorLongitudDeOndaFinal_Stp[3] = int(float(textoPosicionFinal4.get())/0.03125)
                    VectorPasoMono_Stp[3] = int(float(textoPaso4.get())/0.03125)
                if numeroDeSubintervalos>=5:
                    VectorLongitudDeOndaInicial_Stp[4] = int(float(textoPosicionInicial5.get())/0.03125)
                    VectorLongitudDeOndaFinal_Stp[4] = int(float(textoPosicionFinal5.get())/0.03125)
                    VectorPasoMono_Stp[4] = int(float(textoPaso5.get())/0.03125)
                if numeroDeSubintervalos>=6:
                    VectorLongitudDeOndaInicial_Stp[5] = int(float(textoPosicionInicial6.get())/0.03125)
                    VectorLongitudDeOndaFinal_Stp[5] = int(float(textoPosicionFinal6.get())/0.03125)
                    VectorPasoMono_Stp[5] = int(float(textoPaso6.get())/0.03125)
                if numeroDeSubintervalos>=7:
                    VectorLongitudDeOndaInicial_Stp[6] = int(float(textoPosicionInicial7.get())/0.03125)
                    VectorLongitudDeOndaFinal_Stp[6] = int(float(textoPosicionFinal7.get())/0.03125)
                    VectorPasoMono_Stp[6] = int(float(textoPaso7.get())/0.03125)
                if numeroDeSubintervalos>=8:
                    VectorLongitudDeOndaInicial_Stp[7] = int(float(textoPosicionInicial8.get())/0.03125)
                    VectorLongitudDeOndaFinal_Stp[7] = int(float(textoPosicionFinal8.get())/0.03125)
                    VectorPasoMono_Stp[7] = int(float(textoPaso8.get())/0.03125)
                if numeroDeSubintervalos>=9:
                    VectorLongitudDeOndaInicial_Stp[8] = int(float(textoPosicionInicial9.get())/0.03125)
                    VectorLongitudDeOndaFinal_Stp[8] = int(float(textoPosicionFinal9.get())/0.03125)
                    VectorPasoMono_Stp[8] = int(float(textoPaso9.get())/0.03125)
                if numeroDeSubintervalos>=10:
                    VectorLongitudDeOndaInicial_Stp[9] = int(float(textoPosicionInicial10.get())/0.03125)
                    VectorLongitudDeOndaFinal_Stp[9] = int(float(textoPosicionFinal10.get())/0.03125)
                    VectorPasoMono_Stp[9] = int(float(textoPaso10.get())/0.03125)
                    

                tiempoDeMedicion = str(self.CalcularTiempoDeMedicionAPosicionFijaSMC(numeroDeConstantesDeTiempo,posicionFijaSMC_Stp,VectorLongitudDeOndaInicial_Stp,VectorLongitudDeOndaFinal_Stp,VectorPasoMono_Stp))
                raizMedicion = tk.Tk()
                raizMedicion.title('Martin y Gonzalo Pump and Probe - Midiendo a Posicion de la plataforma de retardo fija')
                raizMedicion.geometry('1000x1000')   
                labelEstado = tk.Label(raizMedicion, text="Realizando la medicion. Tiempo estimado:" + tiempoDeMedicion + 'segundos')
                labelEstado.grid(column=0, row=0)
                
                canvas = FigureCanvasTkAgg(self.experimento.grafico.fig, master=raizMedicion)
                canvas.get_tk_widget().grid(row=1,column=0)
                canvas.draw()
                
                #BOTON CANCELAR MEDICION
                self.experimento.MedicionAPosicionFijaSMC(nombreArchivo,numeroDeConstantesDeTiempo,posicionFijaSMC_Stp,VectorLongitudDeOndaInicial_Stp,VectorLongitudDeOndaFinal_Stp,VectorPasoMono_Stp)
                self.experimento.grafico.GuardarGrafico(nombreArchivo)
                labelEstado = tk.Label(raizMedicion, text="Medicion Finalizada. El archivo ha sido guardado con el nombre:" + nombreArchivo)
                labelEstado.grid(column=0, row=0)
                
                def Finalizar():
                    raizMedicion.destroy()    
                botonFinalizar = tk.Button(raizMedicion, text="Finalizar", command=Finalizar)
                botonFinalizar.grid(column=1, row=1)
                
                raizMedicion.mainloop()
                
            botonIniciarMedicion = tk.Button(raiz2, text="Iniciar Medicion", command=IniciarMedicion)
            botonIniciarMedicion.grid(column=3, row=20)
        
        
        botonSiguiente = tk.Button(raiz2, text="Siguiente", command=SiguienteDePosicionFijaSMC)
        botonSiguiente.grid(column=1, row=4)
        
        raiz2.mainloop()

    def ProgramaMedicionCompleta(self):
        raiz3 = tk.Tk()
        raiz3.title('Pump and Probe Software - Medicion Completa')    
        raiz3.geometry('1400x800')
        
        labelNombreArchivo = tk.Label(raiz3, text="Ingrese el nombre del archivo con la extensión\n .csv. Por ejemplo: datos2.csv")
        labelNombreArchivo.grid(column=0, row=0)
        textoNombreArchivo = tk.Entry(raiz3,width=15)
        textoNombreArchivo.grid(column=1, row=0)
        
        labelNumeroDeConstantesDeTiempo = tk.Label(raiz3, text="Ingrese el número de constantes de tiempo de integracion\n del Lock-In. Debe ser un número entero positivo.")
        labelNumeroDeConstantesDeTiempo.grid(column=0, row=1)
        textoNumeroDeConstantesDeTiempo = tk.Entry(raiz3,width=15)
        textoNumeroDeConstantesDeTiempo.grid(column=1, row=1)
        
        labelNumeroDeSubintervalosSMC = tk.Label(raiz3, text="Ingrese la cantidad de secciones del barrido\n de la plataforma de retardo.")
        labelNumeroDeSubintervalosSMC.grid(column=0, row=2)
        textoNumeroDeSubintervalosSMC = tk.Entry(raiz3,width=15)
        textoNumeroDeSubintervalosSMC.grid(column=1, row=2)
        
        labelNumeroDeSubintervalosMono = tk.Label(raiz3, text="Ingrese la cantidad de secciones\n del barrido de longitud de onda.")
        labelNumeroDeSubintervalosMono.grid(column=0, row=3)
        textoNumeroDeSubintervalosMono = tk.Entry(raiz3,width=15)
        textoNumeroDeSubintervalosMono.grid(column=1, row=3)
        
        def Siguiente():
            numeroDeSubintervalosSMC = int(textoNumeroDeSubintervalosSMC.get())
            numeroDeSubintervalosMono = int(textoNumeroDeSubintervalosMono.get())
            
            labelTituloInicialMono = tk.Label(raiz3, text="Ingresar datos en nanómetros:\n desde 400 a 1000")
            labelTituloInicialMono.grid(column=0, row=5)
            labelTituloInicialMono = tk.Label(raiz3, text="Longitud de \n Onda Inicial")
            labelTituloInicialMono.grid(column=0, row=6, sticky=tk.E)
            labelTituloFinalMono = tk.Label(raiz3, text="Longitud de \n Onda Final")
            labelTituloFinalMono.grid(column=1, row=6)
            labelTituloPasoMono = tk.Label(raiz3, text="Paso")
            labelTituloPasoMono.grid(column=2, row=6)
        
            labelTituloConversor = tk.Label(raiz3, text="Conversor de mm a fs")
            labelTituloConversor.grid(column=3, row=0)
            labelmm = tk.Label(raiz3, text="mm")
            labelmm.grid(column=3, row=1)
            labelfs = tk.Label(raiz3, text="fs")
            labelfs.grid(column=5, row=1)
            textomm = tk.Entry(raiz3,width=15)
            textomm.grid(column=3, row=2)
            textofs = tk.Entry(raiz3,width=15)
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


            botonConvertirAmm = tk.Button(raiz3, text="<-", command=ConvertirAmm)
            botonConvertirAmm.grid(column=4, row=1)
            
            botonConvertirAfs = tk.Button(raiz3, text="->", command=ConvertirAfs)
            botonConvertirAfs.grid(column=4, row=2)
        
            if numeroDeSubintervalosMono>=1:
                textoPosicionInicial1Mono = tk.Entry(raiz3,width=15)
                textoPosicionInicial1Mono.grid(column=0, row=7, sticky=tk.E)
                textoPosicionFinal1Mono = tk.Entry(raiz3,width=15)
                textoPosicionFinal1Mono.grid(column=1, row=7)
                textoPaso1Mono = tk.Entry(raiz3,width=15)
                textoPaso1Mono.grid(column=2, row=7)
            if numeroDeSubintervalosMono>=2:
                textoPosicionInicial2Mono = tk.Entry(raiz3,width=15)
                textoPosicionInicial2Mono.grid(column=0, row=8, sticky=tk.E)
                textoPosicionFinal2Mono = tk.Entry(raiz3,width=15)
                textoPosicionFinal2Mono.grid(column=1, row=8)
                textoPaso2Mono = tk.Entry(raiz3,width=15)
                textoPaso2Mono.grid(column=2, row=8)
            if numeroDeSubintervalosMono>=3:
                textoPosicionInicial3Mono = tk.Entry(raiz3,width=15)
                textoPosicionInicial3Mono.grid(column=0, row=9, sticky=tk.E)
                textoPosicionFinal3Mono = tk.Entry(raiz3,width=15)
                textoPosicionFinal3Mono.grid(column=1, row=9)
                textoPaso3Mono = tk.Entry(raiz3,width=15)
                textoPaso3Mono.grid(column=2, row=9)
            if numeroDeSubintervalosMono>=4:
                textoPosicionInicial4Mono = tk.Entry(raiz3,width=15)
                textoPosicionInicial4Mono.grid(column=0, row=10, sticky=tk.E)
                textoPosicionFinal4Mono = tk.Entry(raiz3,width=15)
                textoPosicionFinal4Mono.grid(column=1, row=10)
                textoPaso4Mono = tk.Entry(raiz3,width=15)
                textoPaso4Mono.grid(column=2, row=10)
            if numeroDeSubintervalosMono>=5:
                textoPosicionInicial5Mono = tk.Entry(raiz3,width=15)
                textoPosicionInicial5Mono.grid(column=0, row=11, sticky=tk.E)
                textoPosicionFinal5Mono = tk.Entry(raiz3,width=15)
                textoPosicionFinal5Mono.grid(column=1, row=11)
                textoPaso5Mono = tk.Entry(raiz3,width=15)
                textoPaso5Mono.grid(column=2, row=11)
            if numeroDeSubintervalosMono>=6:
                textoPosicionInicial6Mono = tk.Entry(raiz3,width=15)
                textoPosicionInicial6Mono.grid(column=0, row=12,sticky=tk.E)
                textoPosicionFinal6Mono = tk.Entry(raiz3,width=15)
                textoPosicionFinal6Mono.grid(column=1, row=12)
                textoPaso6Mono = tk.Entry(raiz3,width=15)
                textoPaso6Mono.grid(column=2, row=12)
            if numeroDeSubintervalosMono>=7:
                textoPosicionInicial7Mono = tk.Entry(raiz3,width=15)
                textoPosicionInicial7Mono.grid(column=0, row=13,sticky=tk.E)
                textoPosicionFinal7Mono = tk.Entry(raiz3,width=15)
                textoPosicionFinal7Mono.grid(column=1, row=13)
                textoPaso7Mono = tk.Entry(raiz3,width=15)
                textoPaso7Mono.grid(column=2, row=13)
            if numeroDeSubintervalosMono>=8:
                textoPosicionInicial8Mono = tk.Entry(raiz3,width=15)
                textoPosicionInicial8Mono.grid(column=0, row=14,sticky=tk.E)
                textoPosicionFinal8Mono = tk.Entry(raiz3,width=15)
                textoPosicionFinal8Mono.grid(column=1, row=14)
                textoPaso8Mono = tk.Entry(raiz3,width=15)
                textoPaso8Mono.grid(column=2, row=14)
            if numeroDeSubintervalosMono>=9:
                textoPosicionInicial9Mono = tk.Entry(raiz3,width=15)
                textoPosicionInicial9Mono.grid(column=0, row=15,sticky=tk.E)
                textoPosicionFinal9Mono = tk.Entry(raiz3,width=15)
                textoPosicionFinal9Mono.grid(column=1, row=15)
                textoPaso9Mono = tk.Entry(raiz3,width=15)
                textoPaso9Mono.grid(column=2, row=15)
            if numeroDeSubintervalosMono>=10:
                textoPosicionInicial10Mono = tk.Entry(raiz3,width=15)
                textoPosicionInicial10Mono.grid(column=0, row=16,sticky=tk.E)
                textoPosicionFinal10Mono = tk.Entry(raiz3,width=15)
                textoPosicionFinal10Mono.grid(column=1, row=16)
                textoPaso10Mono = tk.Entry(raiz3,width=15)
                textoPaso10Mono.grid(column=2, row=16)


        
            labelTituloInicialSMC = tk.Label(raiz3, text="Ingresar datos en milímetros:\n desde 0 a 25")
            labelTituloInicialSMC.grid(column=4, row=5)
            labelTituloInicialSMC = tk.Label(raiz3, text="Posicion Inicial")
            labelTituloInicialSMC.grid(column=4, row=6, sticky=tk.E)
            labelTituloFinalSMC = tk.Label(raiz3, text="Posicion Final")
            labelTituloFinalSMC.grid(column=5, row=6)
            labelTituloPasoSMC = tk.Label(raiz3, text="Paso")
            labelTituloPasoSMC.grid(column=6, row=6)
        
            if numeroDeSubintervalosSMC>=1:
                textoPosicionInicial1SMC = tk.Entry(raiz3,width=15)
                textoPosicionInicial1SMC.grid(column=4, row=7, sticky=tk.E)
                textoPosicionFinal1SMC = tk.Entry(raiz3,width=15)
                textoPosicionFinal1SMC.grid(column=5, row=7)
                textoPaso1SMC = tk.Entry(raiz3,width=15)
                textoPaso1SMC.grid(column=6, row=7)
            if numeroDeSubintervalosSMC>=2:
                textoPosicionInicial2SMC = tk.Entry(raiz3,width=15)
                textoPosicionInicial2SMC.grid(column=4, row=8, sticky=tk.E)
                textoPosicionFinal2SMC = tk.Entry(raiz3,width=15)
                textoPosicionFinal2SMC.grid(column=5, row=8)
                textoPaso2SMC = tk.Entry(raiz3,width=15)
                textoPaso2SMC.grid(column=6, row=8)
            if numeroDeSubintervalosSMC>=3:
                textoPosicionInicial3SMC = tk.Entry(raiz3,width=15)
                textoPosicionInicial3SMC.grid(column=4, row=9, sticky=tk.E)
                textoPosicionFinal3SMC = tk.Entry(raiz3,width=15)
                textoPosicionFinal3SMC.grid(column=5, row=9)
                textoPaso3SMC = tk.Entry(raiz3,width=15)
                textoPaso3SMC.grid(column=6, row=9)
            if numeroDeSubintervalosSMC>=4:
                textoPosicionInicial4SMC = tk.Entry(raiz3,width=15)
                textoPosicionInicial4SMC.grid(column=4, row=10, sticky=tk.E)
                textoPosicionFinal4SMC = tk.Entry(raiz3,width=15)
                textoPosicionFinal4SMC.grid(column=5, row=10)
                textoPaso4SMC = tk.Entry(raiz3,width=15)
                textoPaso4SMC.grid(column=6, row=10)
            if numeroDeSubintervalosSMC>=5:
                textoPosicionInicial5SMC = tk.Entry(raiz3,width=15)
                textoPosicionInicial5SMC.grid(column=4, row=11, sticky=tk.E)
                textoPosicionFinal5SMC = tk.Entry(raiz3,width=15)
                textoPosicionFinal5SMC.grid(column=5, row=11)
                textoPaso5SMC = tk.Entry(raiz3,width=15)
                textoPaso5SMC.grid(column=6, row=11)
            if numeroDeSubintervalosSMC>=6:
                textoPosicionInicial6SMC = tk.Entry(raiz3,width=15)
                textoPosicionInicial6SMC.grid(column=4, row=12,sticky=tk.E)
                textoPosicionFinal6SMC = tk.Entry(raiz3,width=15)
                textoPosicionFinal6SMC.grid(column=5, row=12)
                textoPaso6SMC = tk.Entry(raiz3,width=15)
                textoPaso6SMC.grid(column=6, row=12)
            if numeroDeSubintervalosSMC>=7:
                textoPosicionInicial7SMC = tk.Entry(raiz3,width=15)
                textoPosicionInicial7SMC.grid(column=4, row=13,sticky=tk.E)
                textoPosicionFinal7SMC = tk.Entry(raiz3,width=15)
                textoPosicionFinal7SMC.grid(column=5, row=13)
                textoPaso7SMC = tk.Entry(raiz3,width=15)
                textoPaso7SMC.grid(column=6, row=13)
            if numeroDeSubintervalosSMC>=8:
                textoPosicionInicial8SMC = tk.Entry(raiz3,width=15)
                textoPosicionInicial8SMC.grid(column=4, row=14,sticky=tk.E)
                textoPosicionFinal8SMC = tk.Entry(raiz3,width=15)
                textoPosicionFinal8SMC.grid(column=5, row=14)
                textoPaso8SMC = tk.Entry(raiz3,width=15)
                textoPaso8SMC.grid(column=6, row=14)
            if numeroDeSubintervalosSMC>=9:
                textoPosicionInicial9SMC = tk.Entry(raiz3,width=15)
                textoPosicionInicial9SMC.grid(column=4, row=15,sticky=tk.E)
                textoPosicionFinal9SMC = tk.Entry(raiz3,width=15)
                textoPosicionFinal9SMC.grid(column=5, row=15)
                textoPaso9SMC = tk.Entry(raiz3,width=15)
                textoPaso9SMC.grid(column=6, row=15)
            if numeroDeSubintervalosSMC>=10:
                textoPosicionInicial10SMC = tk.Entry(raiz3,width=15)
                textoPosicionInicial10SMC.grid(column=4, row=16,sticky=tk.E)
                textoPosicionFinal10SMC = tk.Entry(raiz3,width=15)
                textoPosicionFinal10SMC.grid(column=5, row=16)
                textoPaso10SMC = tk.Entry(raiz3,width=15)
                textoPaso10SMC.grid(column=6, row=16)

            
            labelGrafico = tk.Label(raiz3, text="Seleccione las magnitudes que desea graficar:")
            labelGrafico.grid(column=0, row=17)
            
            
            
            Var1 = tk.IntVar()
            BotonV1 = tk.Checkbutton(raiz3, text='X', variable=Var1).grid(column=0,row=18)
            
            Var2 = tk.IntVar()
            BotonV2 = tk.Checkbutton(raiz3, text='Y', variable=Var2).grid(column=0,row=19)
            
            Var3 = tk.IntVar()
            BotonV3 = tk.Checkbutton(raiz3, text='R', variable=Var3).grid(column=0,row=18, sticky=tk.E)
            
            Var4 = tk.IntVar()
            BotonV4 = tk.Checkbutton(raiz3, text='\u03B8', variable=Var4).grid(column=0,row=19, sticky=tk.E)
            
            labelEjeX = tk.Label(raiz3, text="Seleccione la magnitud que desea graficar en el eje X:")
            labelEjeX.grid(column=0, row=20)
            
            choices = ['Tiempo', 'Distancia']
            variable = tk.StringVar(raiz3)
            variable.set('Tiempo')
            w = tk.OptionMenu(raiz3, variable, *choices)
            w.grid(column=0,row=21)
            
                
            nombreArchivo = textoNombreArchivo.get()
            numeroDeConstantesDeTiempo = int(textoNumeroDeConstantesDeTiempo.get())
        
            def IniciarMedicion():
                ejeX = variable.get()
                ValoresAGraficar = (Var1.get(),Var2.get(),Var3.get(),Var4.get())
                self.experimento.grafico = Grafico(ValoresAGraficar,2,ejeX)
                VectorLongitudDeOndaInicial_Stp = np.zeros(numeroDeSubintervalosMono)
                VectorLongitudDeOndaFinal_Stp = np.zeros(numeroDeSubintervalosMono)
                VectorPasoMono_Stp = np.zeros(numeroDeSubintervalosMono)
                if numeroDeSubintervalosMono>=1:
                    VectorLongitudDeOndaInicial_Stp[0] = int(float(textoPosicionInicial1Mono.get())/0.03125)
                    VectorLongitudDeOndaFinal_Stp[0] = int(float(textoPosicionFinal1Mono.get())/0.03125)
                    VectorPasoMono_Stp[0] = int(float(textoPaso1Mono.get())/0.03125)
                if numeroDeSubintervalosMono>=2:
                    VectorLongitudDeOndaInicial_Stp[1] = int(float(textoPosicionInicial2Mono.get())/0.03125)
                    VectorLongitudDeOndaFinal_Stp[1] = int(float(textoPosicionFinal2Mono.get())/0.03125)
                    VectorPasoMono_Stp[1] = int(float(textoPaso2Mono.get())/0.03125)
                if numeroDeSubintervalosMono>=3:
                    VectorLongitudDeOndaInicial_Stp[2] = int(float(textoPosicionInicial3Mono.get())/0.03125)
                    VectorLongitudDeOndaFinal_Stp[2] = int(float(textoPosicionFinal3Mono.get())/0.03125)
                    VectorPasoMono_Stp[2] = int(float(textoPaso3Mono.get())/0.03125)
                if numeroDeSubintervalosMono>=4:
                    VectorLongitudDeOndaInicial_Stp[3] = int(float(textoPosicionInicial4Mono.get())/0.03125)
                    VectorLongitudDeOndaFinal_Stp[3] = int(float(textoPosicionFinal4Mono.get())/0.03125)
                    VectorPasoMono_Stp[3] = int(float(textoPaso4Mono.get())/0.03125)
                if numeroDeSubintervalosMono>=5:
                    VectorLongitudDeOndaInicial_Stp[4] = int(float(textoPosicionInicial5Mono.get())/0.03125)
                    VectorLongitudDeOndaFinal_Stp[4] = int(float(textoPosicionFinal5Mono.get())/0.03125)
                    VectorPasoMono_Stp[4] = int(float(textoPaso5Mono.get())/0.03125)
                if numeroDeSubintervalosMono>=6:
                    VectorLongitudDeOndaInicial_Stp[5] = int(float(textoPosicionInicial6Mono.get())/0.03125)
                    VectorLongitudDeOndaFinal_Stp[5] = int(float(textoPosicionFinal6Mono.get())/0.03125)
                    VectorPasoMono_Stp[5] = int(float(textoPaso6Mono.get())/0.03125)
                if numeroDeSubintervalosMono>=7:
                    VectorLongitudDeOndaInicial_Stp[6] = int(float(textoPosicionInicial7Mono.get())/0.03125)
                    VectorLongitudDeOndaFinal_Stp[6] = int(float(textoPosicionFinal7Mono.get())/0.03125)
                    VectorPasoMono_Stp[6] = int(float(textoPaso7Mono.get())/0.03125)
                if numeroDeSubintervalosMono>=8:
                    VectorLongitudDeOndaInicial_Stp[7] = int(float(textoPosicionInicial8Mono.get())/0.03125)
                    VectorLongitudDeOndaFinal_Stp[7] = int(float(textoPosicionFinal8Mono.get())/0.03125)
                    VectorPasoMono_Stp[7] = int(float(textoPaso8Mono.get())/0.03125)
                if numeroDeSubintervalosMono>=9:
                    VectorLongitudDeOndaInicial_Stp[8] = int(float(textoPosicionInicial9Mono.get())/0.03125)
                    VectorLongitudDeOndaFinal_Stp[8] = int(float(textoPosicionFinal9Mono.get())/0.03125)
                    VectorPasoMono_Stp[8] = int(float(textoPaso9Mono.get())/0.03125)
                if numeroDeSubintervalosMono>=10:
                    VectorLongitudDeOndaInicial_Stp[9] = int(float(textoPosicionInicial10Mono.get())/0.03125)
                    VectorLongitudDeOndaFinal_Stp[9] = int(float(textoPosicionFinal10Mono.get())/0.03125)
                    VectorPasoMono_Stp[9] = int(float(textoPaso10Mono.get())/0.03125)

                    
                VectorPosicionInicialSMC_Stp = np.zeros(numeroDeSubintervalosSMC)
                VectorPosicionFinalSMC_Stp = np.zeros(numeroDeSubintervalosSMC)
                VectorPasoSMC_Stp = np.zeros(numeroDeSubintervalosSMC)
                if numeroDeSubintervalosSMC>=1:
                    VectorPosicionInicialSMC_Stp[0] = int(float(textoPosicionInicial1SMC.get())*10000)
                    VectorPosicionFinalSMC_Stp[0] = int(float(textoPosicionFinal1SMC.get())*10000)
                    VectorPasoSMC_Stp[0] = int(float(textoPaso1SMC.get())*10000)
                if numeroDeSubintervalosSMC>=2:
                    VectorPosicionInicialSMC_Stp[1] = int(float(textoPosicionInicial2SMC.get())*10000)
                    VectorPosicionFinalSMC_Stp[1] = int(float(textoPosicionFinal2SMC.get())*10000)
                    VectorPasoSMC_Stp[1] = int(float(textoPaso2SMC.get())*10000)
                if numeroDeSubintervalosSMC>=3:
                    VectorPosicionInicialSMC_Stp[2] = int(float(textoPosicionInicial3SMC.get())*10000)
                    VectorPosicionFinalSMC_Stp[2] = int(float(textoPosicionFinal3SMC.get())*10000)
                    VectorPasoSMC_Stp[2] = int(float(textoPaso3SMC.get())*10000)
                if numeroDeSubintervalosSMC>=4:
                    VectorPosicionInicialSMC_Stp[3] = int(float(textoPosicionInicial4SMC.get())*10000)
                    VectorPosicionFinalSMC_Stp[3] = int(float(textoPosicionFinal4SMC.get())*10000)
                    VectorPasoSMC_Stp[3] = int(float(textoPaso4SMC.get())*10000)
                if numeroDeSubintervalosSMC>=5:
                    VectorPosicionInicialSMC_Stp[4] = int(float(textoPosicionInicial5SMC.get())*10000)
                    VectorPosicionFinalSMC_Stp[4] = int(float(textoPosicionFinal5SMC.get())*10000)
                    VectorPasoSMC_Stp[4] = int(float(textoPaso5SMC.get())*10000)
                if numeroDeSubintervalosSMC>=6:
                    VectorPosicionInicialSMC_Stp[5] = int(float(textoPosicionInicial6SMC.get())*10000)
                    VectorPosicionFinalSMC_Stp[5] = int(float(textoPosicionFinal6SMC.get())*10000)
                    VectorPasoSMC_Stp[5] = int(float(textoPaso6SMC.get())*10000)
                if numeroDeSubintervalosSMC>=7:
                    VectorPosicionInicialSMC_Stp[6] = int(float(textoPosicionInicial7SMC.get())*10000)
                    VectorPosicionFinalSMC_Stp[6] = int(float(textoPosicionFinal7SMC.get())*10000)
                    VectorPasoSMC_Stp[6] = int(float(textoPaso7SMC.get())*10000)
                if numeroDeSubintervalosSMC>=8:
                    VectorPosicionInicialSMC_Stp[7] = int(float(textoPosicionInicial8SMC.get())*10000)
                    VectorPosicionFinalSMC_Stp[7] = int(float(textoPosicionFinal8SMC.get())*10000)
                    VectorPasoSMC_Stp[7] = int(float(textoPaso8SMC.get())*10000)
                if numeroDeSubintervalosSMC>=9:
                    VectorPosicionInicialSMC_Stp[8] = int(float(textoPosicionInicial9SMC.get())*10000)
                    VectorPosicionFinalSMC_Stp[8] = int(float(textoPosicionFinal9SMC.get())*10000)
                    VectorPasoSMC_Stp[8] = int(float(textoPaso9SMC.get())*10000)
                if numeroDeSubintervalosSMC>=10:
                    VectorPosicionInicialSMC_Stp[9] = int(float(textoPosicionInicial10SMC.get())*10000)
                    VectorPosicionFinalSMC_Stp[9] = int(float(textoPosicionFinal10SMC.get())*10000)
                    VectorPasoSMC_Stp[9] = int(float(textoPaso10SMC.get())*10000)
                    
                
                raiz3.destroy()
                tiempoDeMedicion = str(self.CalcularTiempoDeMedicionCompleta(numeroDeConstantesDeTiempo,VectorPosicionInicialSMC_Stp,VectorPosicionFinalSMC_Stp,VectorPasoSMC_Stp,VectorLongitudDeOndaInicial_Stp,VectorLongitudDeOndaFinal_Stp,VectorPasoMono_Stp))
                raizMedicion = tk.Tk()
                raizMedicion.title('Martin y Gonzalo Pump and Probe - Medición Completa')
                raizMedicion.geometry('1000x1000')   
                labelEstado = tk.Label(raizMedicion, text="Realizando la medicion. Tiempo estimado:" + tiempoDeMedicion + 'segundos')
                labelEstado.grid(column=0, row=0)
                
                canvas = FigureCanvasTkAgg(self.experimento.grafico.fig, master=raizMedicion)
                canvas.get_tk_widget().grid(row=1,column=0)
                canvas.draw()
                
                #BOTON CANCELAR MEDICION
                
                self.experimento.MedicionCompleta(nombreArchivo,numeroDeConstantesDeTiempo,VectorPosicionInicialSMC_Stp,VectorPosicionFinalSMC_Stp,VectorPasoSMC_Stp,VectorLongitudDeOndaInicial_Stp,VectorLongitudDeOndaFinal_Stp,VectorPasoMono_Stp)
                self.experimento.grafico.PonerColorbars()
                self.experimento.grafico.GuardarGrafico(nombreArchivo)
                labelEstado = tk.Label(raizMedicion, text="Medicion Finalizada. El archivo ha sido guardado con el nombre:" + nombreArchivo)
                labelEstado.grid(column=0, row=0)
                
                def Finalizar():
                    raizMedicion.destroy()    
                botonFinalizar = tk.Button(raizMedicion, text="Finalizar", command=Finalizar)
                botonFinalizar.grid(column=1, row=1)    
                raizMedicion.mainloop()
                    
            botonIniciarMedicion = tk.Button(raiz3, text="Iniciar Medicion", command=IniciarMedicion)
            botonIniciarMedicion.grid(column=3, row=22)
        
        botonSiguiente = tk.Button(raiz3, text="Siguiente", command=Siguiente)
        botonSiguiente.grid(column=1, row=4)
        raiz3.mainloop()
    
    def SetearPuertos(self):
        raiz4 = tk.Tk()
        raiz4.title('Pump and Probe Software - Seteo de puertos')
        raiz4.geometry('1000x800')
        
        labelSMC = tk.Label(raiz4, text = 'Ingrese el número de puerto COM correspondiente al SMC. Ejemplo : 5')
        labelSMC.grid(column=0, row=0)
        textoSMC = tk.Entry(raiz4, width=5)
        textoSMC.grid(column=1, row=0)
        
        labelMono = tk.Label(raiz4, text = 'Ingrese el número de puerto COM correspondiente al Monocromador. Ejemplo : 4')
        labelMono.grid(column=0, row=1)
        textoMono = tk.Entry(raiz4, width=5)
        textoMono.grid(column=1, row=1)
   
        labelLockIn = tk.Label(raiz4, text = 'Ingrese el número de dirección correspondiente al Lock-In. Puede verse en la pantalla del mismo. Ejemplo : 11')
        labelLockIn.grid(column=0, row=2)
        textoLockIn = tk.Entry(raiz4, width=5)
        textoLockIn.grid(column=1, row=2)
        
        def AdquirirPuertos():
            self.VectorDePuertos = (int(textoSMC.get()), int(textoMono.get()), int(textoLockIn.get()))
            if hasattr(self, 'experimento'):
                if (self.experimento.smc.puerto) != ('COM' + str(self.VectorDePuertos[0])):
                    self.experimento.smc = SMC('COM' + str(self.VectorDePuertos[0]))
                if (self.experimento.mono.puerto) != ('COM' + str(self.VectorDePuertos[1])):
                    self.experimento.mono = Monocromador('COM' + str(self.VectorDePuertos[1]))
                if (self.experimento.lockin.puerto) != (self.VectorDePuertos[2]):
                    self.experimento.lockin = LockIn(self.VectorDePuertos[2])
            else:
                self.experimento = Experimento(self.VectorDePuertos) 
            raiz4.destroy()
            self.Continuar()

        botonOk = tk.Button(raiz4, text = 'Setear', command = AdquirirPuertos)
        botonOk.grid(column=1,row=3)
        
        raiz4.mainloop()
        
    def Continuar(self):
        raiz = tk.Tk()
        raiz.title('Pump and Probe Software')
        raiz.geometry('1000x800')   
        def SetearPuertosBis():
            raiz.destroy()
            self.SetearPuertos()
        def ProgramaMedicionALambdaFijaBis():
            raiz.destroy()
            self.ProgramaMedicionALambdaFija()
        def ProgramaMedicionAPosicionFijaBis():
            raiz.destroy()
            self.ProgramaMedicionAPosicionFija()
        def ProgramaMedicionCompletaBis():
            raiz.destroy()
            self.ProgramaMedicionCompleta()
            
        btn1 = tk.Button(raiz, text="Setear Puertos", command=SetearPuertosBis)
        btn1.grid(column=1, row=0)
        btn2 = tk.Button(raiz, text="A Lambda Fija", command=ProgramaMedicionALambdaFijaBis)
        btn2.grid(column=2, row=0)
        btn3 = tk.Button(raiz, text="A Posicion Fija", command=ProgramaMedicionAPosicionFijaBis)
        btn3.grid(column=3, row=0)
        btn4 = tk.Button(raiz, text="Completa", command=ProgramaMedicionCompletaBis)
        btn4.grid(column=4, row=0)
        raiz.mainloop()

