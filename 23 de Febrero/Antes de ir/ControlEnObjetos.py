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
from tkinter import *
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg



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
        self.velocidadStepsPorSegundo = 400
        
    #def ConfigurarMonocromador(self):
    
    def Mover(self, LongitudDeOnda_Step): 
        comando = '#MRL\r1\r' + str(LongitudDeOnda_Step) + '\r'
        self.address.write(comando.encode())
        self.posicion = LongitudDeOnda_Step
        time.sleep(self.CalcularTiempoSleep(LongitudDeOnda_Step))
        
    def CalcularTiempoSleep(self, LongitudDeOnda_Step):
        TiempoMonocromador = abs(LongitudDeOnda_Step-self.posicion)/(self.velocidadStepsPorSegundo) # Hay que medirlo
        return TiempoMonocromador
        
class LockIn():
    def __init__(self,puerto):
        rm = pyvisa.ResourceManager()  # OJO EL SELF, PUEDE NO FUNCIONAR
        comando = 'GPIB0::' + str(puerto) + '::INSTR'
        self.address = rm.open_resource(comando)
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
        
#class Osciloscopio():
#    def __init__(self,puerto):
#        self.ConfigurarOsciloscopio()
#    def ConfigurarOsciloscopio():



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
            self.x.append(posicionSMC/10000)
        else:
            self.x.append((posicionSMC/10000)*(2/3)*(10^(-11)))
        if self.ValoresAGraficar(0)==1:
            self.y1.append(VectorAGraficar(0)) 
            ax1.plot(self.x,self.y1,'c*')
        if self.ValoresAGraficar(1)==1:
            self.y2.append(VectorAGraficar(1))
            ax2.plot(self.x,self.y2,'m*')
        if self.ValoresAGraficar(2)==1:
            self.y3.append(VectorAGraficar(2))
            ax3.plot(self.x,self.y3,'y*')
        if self.ValoresAGraficar(3)==1:
            self.y4.append(VectorAGraficar(3))
            ax4.plot(self.x,self.y4,'k*')
        fig.canvas.draw()
        fig.canvas.flush_events()
        #Nombres y escalas de ejes    
    
    def GraficarAPosicionFija(self, VectorAGraficar, posicionSMC, posicionMono):
        self.x.append(posicionMono*0.03125)
        if self.ValoresAGraficar(0)==1:
            self.y1.append(VectorAGraficar(0)) 
            ax1.plot(self.x,self.y1,'c*')
        if self.ValoresAGraficar(1)==1:
            self.y2.append(VectorAGraficar(1))
            ax2.plot(self.x,self.y2,'m*')
        if self.ValoresAGraficar(2)==1:
            self.y3.append(VectorAGraficar(2))
            ax3.plot(self.x,self.y3,'y*')
        if self.ValoresAGraficar(3)==1:
            self.y4.append(VectorAGraficar(3))
            ax4.plot(self.x,self.y4,'k*')
        fig.canvas.draw()
        fig.canvas.flush_events()
        #Nombres y escalas de ejes
    
    def GraficarCompletamente(self, VectorAGraficar, posicionSMC, posicionMono):
        if self.ejeX == 'Distancia':
            self.x.append(posicionSMC/10000)
        else:
            self.x.append((posicionSMC/10000)*(2/3)*(10^(-11)))
        self.z.append(posicionMono*0.03125)
        X, Z = np.meshgrid(x,z)
        if self.ValoresAGraficar(0)==1:
            self.yd1[0].append(VectorAGraficar(0)) 
            self.yd1[1].append(VectorAGraficar(0)) 
            self.plot1 = ax1.contourf(x, y, Z, 20, cmap='RdGy')
        if self.ValoresAGraficar(1)==1:
            self.yd2[0].append(VectorAGraficar(1)) 
            self.yd2[1].append(VectorAGraficar(1)) 
            self.plot2 = ax2.contourf(x, y, Z, 20, cmap='RdGy')
        if self.ValoresAGraficar(2)==1:
            self.yd3[0].append(VectorAGraficar(2)) 
            self.yd3[1].append(VectorAGraficar(2)) 
            self.plot3 = ax3.contourf(x, y, Z, 20, cmap='RdGy')
        if self.ValoresAGraficar(3)==1:
            self.yd4[0].append(VectorAGraficar(3)) 
            self.yd4[1].append(VectorAGraficar(3)) 
            self.plot4 = ax4.contourf(x, y, Z, 20, cmap='RdGy')
        fig.canvas.draw()
        fig.canvas.flush_events() 

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

class Experimento():
    def __init__(self,VectorDePuertos):
        self.smc = SMC('COM'+str(VectorDePuertos[0]))
        self.mono = Monocromador('COM'+str(VectorDePuertos[1]))
        self.lockin = LockIn(VectorDePuertos[2])
        #self.osciloscopio = Osciloscopio(VectorDePuertos[3])
        
        
    def MedicionALambdaFija(self,
                            nombreArchivo,
                            numeroDeConstantesDeTiempo,
                            longitudDeOndaFija_Stp,
                            VectorPosicionInicialSMC_Stp,
                            VectorPosicionFinalSMC_Stp,
                            VectorPasoSMC_Stp):
        self.nombreArchivo = nombreArchivo
        self.numeroDeConstantesDeTiempo = numeroDeConstantesDeTiempo
        self.lockin.CalcularTiempoDeIntegracion(numeroDeConstantesDeTiempo)
        self.TipoDeMedicion = 0
        
        
        self.mono.Mover(longitudDeOndaFija_Stp)
        for i in range(0,len(VectorPosicionInicialSMC_Stp)):
            self.smc.Mover(VectorPosicionInicialSMC_Stp[i])
            self.Adquirir()
            for j in range(VectorPosicionInicialSMC_Stp[i],VectorPosicionFinalSMC_Stp[i],VectorPasoSMC_Stp[i]):
                self.smc.Mover(VectorPasoSMC_Stp[i]+self.smc.posicion)
                self.Adquirir()
        
    def MedicionAPosicionFijaSMC(self,
                            nombreArchivo,
                            numeroDeConstantesDeTiempo,
                            posicionFijaSMC_Stp,
                            VectorLongitudDeOndaInicial_Stp,
                            VectorLongitudDeOndaFinal_Stp,
                            VectorPasoMono_Stp):
        self.nombreArchivo = nombreArchivo
        self.numeroDeConstantesDeTiempo = numeroDeConstantesDeTiempo
        self.lockin.CalcularTiempoDeIntegracion(numeroDeConstantesDeTiempo)
        self.TipoDeMedicion = 1
        
        self.smc.Mover(posicionFijaSMC_Stp)
        for i in range(0,len(VectorLongitudDeOndaInicial_Stp)):
            self.mono.Mover(VectorLongitudDeOndaInicial_Stp[i])
            self.Adquirir()
            for j in range(VectorLongitudDeOndaInicial_Stp[i],VectorLongitudDeOndaFinal_Stp[i],VectorPasoMono_Stp[i]):
                self.mono.Mover(VectorPasoMono_Stp[i]+self.mono.posicion)
                self.Adquirir()
    
    def Adquirir(self):
        with open(self.nombreArchivo, 'a') as csvfile:
            filewriter = csv.writer(csvfile, delimiter=',')
            time.sleep(self.lockin.TiempoDeIntegracionTotal)
            a = LockIn.query("SNAP?1,2{,3,4,9}")
            a = a.replace('\n','')
            #VoltajeDC = Osciloscopio.query()
            a = a + ',' + str(self.smc.posicion) + ',' + str(self.mono.posicion)# + ',' + VoltajeDC
            b = a.split(',')
            filewriter.writerow(b)
            self.grafico.Graficar(b,self.smc.posicion,self.mono.posicion)
            
                            
    
    def MedicionCompleta(self, 
                         nombreArchivo,
                         numeroDeConstantesDeTiempo,
                         VectorPosicionInicialSMC_Stp,
                         VectorPosicionFinalSMC_Stp,
                         VectorPasoSMC_Stp,
                         VectorLongitudDeOndaInicial_Stp,
                         VectorLongitudDeOndaFinal_Stp,
                         VectorPasoMono_Stp):
         
        self.nombreArchivo = nombreArchivo
        self.numeroDeConstantesDeTiempo = numeroDeConstantesDeTiempo
        self.lockin.CalcularTiempoDeIntegracion(numeroDeConstantesDeTiempo)
        self.TipoDeMedicion = 2
        
        
        for i in range(0,len(VectorLongitudDeOndaInicial_Stp)):
            self.mono.Mover(VectorLongitudDeOndaInicial_Stp[i])
            for j in range(VectorLongitudDeOndaInicial_Stp[i], VectorLongitudDeOndaFinal_Stp[i], VectorPasoMono_Stp[i]):
                for k in range(0,len(VectorPosicionInicialSMC_Stp)):
                    self.smc.Mover(VectorPosicionInicialSMC_Stp[k])
                    self.Adquirir()
                    for l in range(VectorPosicionInicialSMC_Stp[k],VectorPosicionFinalSMC_Stp[k],VectorPasoSMC_Stp[k]):
                        self.smc.Mover(VectorPasoSMC_Stp[k]+self.smc.posicion)
                        self.Adquirir()
                self.mono.Mover(VectorPasoMono_Stp[i] + self.mono.posicion)
        
        
                
                
                


       
class Programa(): 
    
    def Iniciar(self):
        raiz = Tk()
        raiz.title('Martin y Gonzalo Pump and Probe')
        raiz.geometry('1000x800')   
        def SetearPuertosBoton():
            raiz.destroy()
            self.SetearPuertos()
        btn1 = Button(raiz, text="Setear Puertos", command=SetearPuertosBoton)
        btn1.grid(column=1, row=0)
        raiz.mainloop()
    
    def ProgramaMedicionALambdaFija(self):
        raiz1 = Tk()
        raiz1.title('Medicion a Lambda Fija')
        raiz1.geometry('1000x800')
        
        labelNombreArchivo = Label(raiz1, text="Ingrese el nombre del archivo con la extensión\n .csv. Por ejemplo: datos2.csv")
        labelNombreArchivo.grid(column=0, row=0)
        textoNombreArchivo = Entry(raiz1,width=15)
        textoNombreArchivo.grid(column=1, row=0)
        
        labelNumeroDeConstantesDeTiempo = Label(raiz1, text="Ingrese el número de constantes de tiempo de integracion\n del Lock-In. Debe ser un número entero positivo.")
        labelNumeroDeConstantesDeTiempo.grid(column=0, row=1)
        textoNumeroDeConstantesDeTiempo = Entry(raiz1,width=15)
        textoNumeroDeConstantesDeTiempo.grid(column=1, row=1)
    
        labelLongitudDeOndaFija = Label(raiz1, text="Ingrese la longitud de onda fija en nanómetros\n a la que desea realizar la medición.")
        labelLongitudDeOndaFija.grid(column=0, row=2)
        textoLongitudDeOndaFija = Entry(raiz1,width=15)
        textoLongitudDeOndaFija.grid(column=1, row=2)
    
        labelNumeroDeSubintervalos = Label(raiz1, text="Ingrese la cantidad de barridos distintos\n en los que desea seccionar el barrido completo.")
        labelNumeroDeSubintervalos.grid(column=0, row=3)
        textoNumeroDeSubintervalos = Entry(raiz1,width=15)
        textoNumeroDeSubintervalos.grid(column=1, row=3)
    
        def SiguienteDeLambdaFija():
            numeroDeSubintervalos = int(textoNumeroDeSubintervalos.get())
            labelTituloInicial = Label(raiz1, text="Ingresar datos en milímetros: desde 0 a 25")
            labelTituloInicial.grid(column=0, row=5)
            labelTituloInicial = Label(raiz1, text="Posicion Inicial")
            labelTituloInicial.grid(column=0, row=6,sticky=E)
            labelTituloFinal = Label(raiz1, text="Posicion Final")
            labelTituloFinal.grid(column=1, row=6)
            labelTituloPaso = Label(raiz1, text="Paso")
            labelTituloPaso.grid(column=2, row=6)
                    
            
            
            labelTituloConversor = Label(raiz1, text="Conversor de mm a fs")
            labelTituloConversor.grid(column=3, row=0)
            labelmm = Label(raiz1, text="mm")
            labelmm.grid(column=3, row=1)
            labelfs = Label(raiz1, text="fs")
            labelfs.grid(column=5, row=1)
            textomm = Entry(raiz1,width=15)
            textomm.grid(column=3, row=2)
            textofs = Entry(raiz1,width=15)
            textofs.grid(column=5, row=2)
            
            def ConvertirAfs():
                mm = textomm.get()
                fs = float(mm)*6666.666
                textofs.delete(0, END)
                textofs.insert(END, fs)

            def ConvertirAmm():
                fs = textofs.get()
                mm = float(fs)/6666.666
                textomm.delete(0, END)
                textomm.insert(END, mm)

            botonConvertirAmm = Button(raiz1, text="<-", command=ConvertirAmm)
            botonConvertirAmm.grid(column=4, row=1)
            
            botonConvertirAfs = Button(raiz1, text="->", command=ConvertirAfs)
            botonConvertirAfs.grid(column=4, row=2)
        
        
        
            if numeroDeSubintervalos>=1:
                textoPosicionInicial1 = Entry(raiz1,width=15)
                textoPosicionInicial1.grid(column=0, row=7,sticky=E)
                textoPosicionFinal1 = Entry(raiz1,width=15)
                textoPosicionFinal1.grid(column=1, row=7)
                textoPaso1 = Entry(raiz1,width=15)
                textoPaso1.grid(column=2, row=7)
            if numeroDeSubintervalos>=2:
                textoPosicionInicial2 = Entry(raiz1,width=15)
                textoPosicionInicial2.grid(column=0, row=8,sticky=E)
                textoPosicionFinal2 = Entry(raiz1,width=15)
                textoPosicionFinal2.grid(column=1, row=8)
                textoPaso2 = Entry(raiz1,width=15)
                textoPaso2.grid(column=2, row=8)
            if numeroDeSubintervalos>=3:
                textoPosicionInicial3 = Entry(raiz1,width=15)
                textoPosicionInicial3.grid(column=0, row=9,sticky=E)
                textoPosicionFinal3 = Entry(raiz1,width=15)
                textoPosicionFinal3.grid(column=1, row=9)
                textoPaso3 = Entry(raiz1,width=15)
                textoPaso3.grid(column=2, row=9)
            if numeroDeSubintervalos>=4:
                textoPosicionInicial4 = Entry(raiz1,width=15)
                textoPosicionInicial4.grid(column=0, row=10,sticky=E)
                textoPosicionFinal4 = Entry(raiz1,width=15)
                textoPosicionFinal4.grid(column=1, row=10)
                textoPaso4 = Entry(raiz1,width=15)
                textoPaso4.grid(column=2, row=10)
            if numeroDeSubintervalos>=5:
                textoPosicionInicial5 = Entry(raiz1,width=15)
                textoPosicionInicial5.grid(column=0, row=11,sticky=E)
                textoPosicionFinal5 = Entry(raiz1,width=15)
                textoPosicionFinal5.grid(column=1, row=11)
                textoPaso5 = Entry(raiz1,width=15)
                textoPaso5.grid(column=2, row=11)
            if numeroDeSubintervalos>=6:
                textoPosicionInicial6 = Entry(raiz1,width=15)
                textoPosicionInicial6.grid(column=0, row=12,sticky=E)
                textoPosicionFinal6 = Entry(raiz1,width=15)
                textoPosicionFinal6.grid(column=1, row=12)
                textoPaso6 = Entry(raiz1,width=15)
                textoPaso6.grid(column=2, row=12)
            if numeroDeSubintervalos>=7:
                textoPosicionInicial7 = Entry(raiz1,width=15)
                textoPosicionInicial7.grid(column=0, row=13,sticky=E)
                textoPosicionFinal7 = Entry(raiz1,width=15)
                textoPosicionFinal7.grid(column=1, row=13)
                textoPaso7 = Entry(raiz1,width=15)
                textoPaso7.grid(column=2, row=13)
            if numeroDeSubintervalos>=8:
                textoPosicionInicial8 = Entry(raiz1,width=15)
                textoPosicionInicial8.grid(column=0, row=14,sticky=E)
                textoPosicionFinal8 = Entry(raiz1,width=15)
                textoPosicionFinal8.grid(column=1, row=14)
                textoPaso8 = Entry(raiz1,width=15)
                textoPaso8.grid(column=2, row=14)
            if numeroDeSubintervalos>=9:
                textoPosicionInicial9 = Entry(raiz1,width=15)
                textoPosicionInicial9.grid(column=0, row=15,sticky=E)
                textoPosicionFinal9 = Entry(raiz1,width=15)
                textoPosicionFinal9.grid(column=1, row=15)
                textoPaso9 = Entry(raiz1,width=15)
                textoPaso9.grid(column=2, row=15)
            if numeroDeSubintervalos>=10:
                textoPosicionInicial10 = Entry(raiz1,width=15)
                textoPosicionInicial10.grid(column=0, row=16,sticky=E)
                textoPosicionFinal10 = Entry(raiz1,width=15)
                textoPosicionFinal10.grid(column=1, row=16)
                textoPaso10 = Entry(raiz1,width=15)
                textoPaso10.grid(column=2, row=16)
                
            
            labelGraficos = Label(raiz1, text="Seleccione los valores que desea graficar\n en función del tiempo de retardo:")
            labelGraficos.grid(column=0, row=17)
            
            
            Var1=IntVar()
            BotonV1 = Checkbutton(raiz1, text='X', variable=Var1).grid(column=0,row=18)
            
            Var2=IntVar()
            BotonV2 = Checkbutton(raiz1, text='Y', variable=Var2).grid(column=0,row=19)
            
            Var3=IntVar()
            BotonV3 = Checkbutton(raiz1, text='R', variable=Var3).grid(column=0,row=18, sticky=E)
            
            Var4=IntVar()
            BotonV4 = Checkbutton(raiz1, text='\u03B8', variable=Var4).grid(column=0,row=19, sticky=E)
            

            labelEjeX = Label(raiz1, text="Seleccione la magnitud que desea graficar en el eje X:")
            labelEjeX.grid(column=0, row=20)

            choices = ['Tiempo', 'Distancia']
            variable = StringVar(raiz1)
            variable.set('Tiempo')
            w = OptionMenu(raiz1, variable, *choices)
            w.grid(column=0,row=21)
            
            
            nombreArchivo = textoNombreArchivo.get()
            numeroDeConstantesDeTiempo = int(textoNumeroDeConstantesDeTiempo.get())
            longitudDeOndaFija_Stp = int(float(textoLongitudDeOndaFija.get())/0.03125)
        
            def IniciarMedicion():
                ejeX = variable.get()
                ValoresAGraficar = (Var1.get(),Var2.get(),Var3.get(),Var4.get())
                self.experimento.grafico = Grafico(ValoresAGraficar,0,ejeX)
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
                if numeroDeSubintervalos>=6:
                    VectorPosicionInicialSMC_Stp[5] = int(float(textoPosicionInicial6.get())*10000)
                    VectorPosicionFinalSMC_Stp[5] = int(float(textoPosicionFinal6.get())*10000)
                    VectorPasoSMC_Stp[5] = int(float(textoPaso6.get())*10000)
                if numeroDeSubintervalos>=7:
                    VectorPosicionInicialSMC_Stp[6] = int(float(textoPosicionInicial7.get())*10000)
                    VectorPosicionFinalSMC_Stp[6] = int(float(textoPosicionFinal7.get())*10000)
                    VectorPasoSMC_Stp[6] = int(float(textoPaso7.get())*10000)
                if numeroDeSubintervalos>=8:
                    VectorPosicionInicialSMC_Stp[7] = int(float(textoPosicionInicial8.get())*10000)
                    VectorPosicionFinalSMC_Stp[7] = int(float(textoPosicionFinal8.get())*10000)
                    VectorPasoSMC_Stp[7] = int(float(textoPaso8.get())*10000)
                if numeroDeSubintervalos>=9:
                    VectorPosicionInicialSMC_Stp[8] = int(float(textoPosicionInicial9.get())*10000)
                    VectorPosicionFinalSMC_Stp[8] = int(float(textoPosicionFinal9.get())*10000)
                    VectorPasoSMC_Stp[8] = int(float(textoPaso9.get())*10000)
                if numeroDeSubintervalos>=10:
                    VectorPosicionInicialSMC_Stp[9] = int(float(textoPosicionInicial10.get())*10000)
                    VectorPosicionFinalSMC_Stp[9] = int(float(textoPosicionFinal10.get())*10000)
                    VectorPasoSMC_Stp[9] = int(float(textoPaso10.get())*10000)
                    
                    
                tiempoDeMedicion = str(self.CalcularTiempoDeMedicionALambdaFija(numeroDeConstantesDeTiempo,longitudDeOndaFija_Stp,VectorPosicionInicialSMC_Stp,VectorPosicionFinalSMC_Stp,VectorPasoSMC_Stp))
                raizMedicion = Tk()
                raizMedicion.title('Martin y Gonzalo Pump and Probe - Midiendo a Lambda Fija')
                raizMedicion.geometry('1000x1000')   
                labelEstado = Label(raizMedicion, text="Realizando la medicion. Tiempo estimado:" + tiempoDeMedicion + 'segundos')
                labelEstado.grid(column=0, row=0)
                
                canvas = FigureCanvasTkAgg(self.experimento.grafico.fig, master=raizMedicion)
                canvas.get_tk_widget().grid(row=1,column=0)
                canvas.draw()
                self.experimento.MedicionALambdaFija(nombreArchivo,numeroDeConstantesDeTiempo,longitudDeOndaFija_Stp,VectorPosicionInicialSMC_Stp,VectorPosicionFinalSMC_Stp,VectorPasoSMC_Stp)
                self.experimento.grafico.GuardarGrafico(nombreArchivo)
                labelEstado = Label(raizMedicion, text="Medicion Finalizada. El archivo ha sido guardado con el nombre:" + nombreArchivo)
                labelEstado.grid(column=0, row=0)
                
                def Finalizar():
                    raizMedicion.destroy()    
                botonFinalizar = Button(raizMedicion, text="Finalizar", command=Finalizar)
                botonFinalizar.grid(column=1, row=1)
                
                raizMedicion.mainloop()
                
            botonIniciarMedicion = Button(raiz1, text="Iniciar Medicion", command=IniciarMedicion)
            botonIniciarMedicion.grid(column=1, row=22)
       
            
        botonSiguiente = Button(raiz1, text="Siguiente", command=SiguienteDeLambdaFija)
        botonSiguiente.grid(column=1, row=4)
        raiz1.mainloop()
    
    def CalcularTiempoDeMedicionALambdaFija(self, numeroDeConstantesDeTiempo,
                                            longitudDeOndaFija_Stp,
                                            VectorPosicionInicialSMC_Stp,
                                            VectorPosicionFinalSMC_Stp,
                                            VectorPasoSMC_Stp):
        TiempoDeMedicion = 0
        CantidadDeMediciones = 0
        TiempoDeDesplazamientoTotal = 0
        TiempoDeDesplazamientoPorPaso = 0
        TiempoMuerto = 0
        TiempoMuerto = VectorPosicionInicialSMC_Stp[0]/1000
        TiempoMonocromador = (longitudDeOndaFija_Stp-self.experimento.mono.posicion)/100
        for i in range(0, len(VectorPosicionInicialSMC_Stp)):
            if i>0:
                TiempoMuerto = TiempoMuerto + (VectorPosicionInicialSMC_Stp[i]-VectorPosicionFinalSMC_Stp[i-1])/1000
            CantidadDeMediciones = CantidadDeMediciones + (VectorPosicionFinalSMC_Stp[i]-VectorPosicionInicialSMC_Stp[i])/VectorPasoSMC_Stp[i]
            TiempoDeDesplazamientoPorPaso = VectorPasoSMC_Stp[i]/1000
            TiempoDeDesplazamientoTotal = TiempoDeDesplazamientoTotal + CantidadDeMediciones*TiempoDeDesplazamientoPorPaso
        TiempoDeMedicion = CantidadDeMediciones*(self.experimento.lockin.CalcularTiempoDeIntegracion(numeroDeConstantesDeTiempo)) + TiempoDeDesplazamientoTotal + TiempoMuerto + TiempoMonocromador
        return TiempoDeMedicion
    
    def CalcularTiempoDeMedicionAPosicionFijaSMC(self, numeroDeConstantesDeTiempo,
                                                 posicionFijaSMC_Stp,
                                                 VectorLongitudDeOndaInicial_Stp,
                                                 VectorLongitudDeOndaFinal_Stp,
                                                 VectorPasoMono_Stp):
        TiempoDeMedicion = 0
        CantidadDeMediciones = 0
        TiempoDeDesplazamientoTotal = 0
        TiempoDeDesplazamientoPorPaso = 0
        TiempoMuerto = 0
        TiempoMuerto = VectorLongitudDeOndaInicial_Stp[0]/100
        TiempoSMC = (posicionFijaSMC_Stp-self.experimento.smc.posicion)/1000
        for i in range(0, len(VectorLongitudDeOndaInicial_Stp)):
            if i>0:
                TiempoMuerto = TiempoMuerto + (VectorLongitudDeOndaInicial_Stp[i]-VectorLongitudDeOndaFinal_Stp[i-1])/100
            CantidadDeMediciones = CantidadDeMediciones + (VectorLongitudDeOndaFinal_Stp[i]-VectorLongitudDeOndaInicial_Stp[i])/VectorPasoMono_Stp[i]
            TiempoDeDesplazamientoPorPaso = VectorPasoMono_Stp[i]/100
            TiempoDeDesplazamientoTotal = TiempoDeDesplazamientoTotal + CantidadDeMediciones*TiempoDeDesplazamientoPorPaso
        TiempoDeMedicion = CantidadDeMediciones*(self.experimento.lockin.CalcularTiempoDeIntegracion(numeroDeConstantesDeTiempo)) + TiempoDeDesplazamientoTotal + TiempoMuerto + TiempoSMC
        return TiempoDeMedicion    
    
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
        raiz2 = Tk()
        raiz2.title('Medicion a Posicion Fija')
        raiz2.geometry('1000x800')
        
        labelNombreArchivo = Label(raiz2, text="Ingrese el nombre del archivo con la extensión\n .csv. Por ejemplo: datos2.csv")
        labelNombreArchivo.grid(column=0, row=0)
        textoNombreArchivo = Entry(raiz2,width=15)
        textoNombreArchivo.grid(column=1, row=0)
        
        labelNumeroDeConstantesDeTiempo = Label(raiz2, text="Ingrese el número de constantes de tiempo de integracion\n del Lock-In. Debe ser un número entero positivo.")
        labelNumeroDeConstantesDeTiempo.grid(column=0, row=1)
        textoNumeroDeConstantesDeTiempo = Entry(raiz2,width=15)
        textoNumeroDeConstantesDeTiempo.grid(column=1, row=1)
    
        labelPosicionFijaSMC = Label(raiz2, text="Ingrese la posición fija de la plataforma de retardo a la que desea\n realizar la medición. Debe ser un valor entre 0 y 25 milímetros.")
        labelPosicionFijaSMC.grid(column=0, row=2)
        textoPosicionFijaSMC = Entry(raiz2,width=15)
        textoPosicionFijaSMC.grid(column=1, row=2)
    
        labelNumeroDeSubintervalos = Label(raiz2, text="Ingrese la cantidad de secciones\n del barrido de longitud de onda.")
        labelNumeroDeSubintervalos.grid(column=0, row=3)
        textoNumeroDeSubintervalos = Entry(raiz2,width=15)
        textoNumeroDeSubintervalos.grid(column=1, row=3)
        
        def SiguienteDePosicionFijaSMC():
            numeroDeSubintervalos = int(textoNumeroDeSubintervalos.get())
            labelTituloInicial = Label(raiz2, text="Ingresar en milímetros:\n desde 0 a 25")
            labelTituloInicial.grid(column=0, row=5)
            labelTituloInicial = Label(raiz2, text="Posicion Inicial")
            labelTituloInicial.grid(column=0, row=5, sticky=E)
            labelTituloFinal = Label(raiz2, text="Posicion Final")
            labelTituloFinal.grid(column=1, row=5)
            labelTituloPaso = Label(raiz2, text="Paso")
            labelTituloPaso.grid(column=2, row=5)
        
            labelTituloConversor = Label(raiz2, text="Conversor de mm a fs")
            labelTituloConversor.grid(column=3, row=0)
            labelmm = Label(raiz2, text="mm")
            labelmm.grid(column=3, row=1)
            labelfs = Label(raiz2, text="fs")
            labelfs.grid(column=5, row=1)
            textomm = Entry(raiz2,width=15)
            textomm.grid(column=3, row=2)
            textofs = Entry(raiz2,width=15)
            textofs.grid(column=5, row=2)
            

            
            def ConvertirAfs():
                mm = textomm.get()
                fs = float(mm)*6666.666
                textofs.delete(0, END)
                textofs.insert(END, fs)

            def ConvertirAmm():
                fs = textofs.get()
                mm = float(fs)/6666.666
                textomm.delete(0, END)
                textomm.insert(END, mm)


            botonConvertirAmm = Button(raiz2, text="<-", command=ConvertirAmm)
            botonConvertirAmm.grid(column=4, row=1)
            
            botonConvertirAfs = Button(raiz2, text="->", command=ConvertirAfs)
            botonConvertirAfs.grid(column=4, row=2)
        
        
            if numeroDeSubintervalos>=1:
                textoPosicionInicial1 = Entry(raiz2,width=15)
                textoPosicionInicial1.grid(column=0, row=6, sticky=E)
                textoPosicionFinal1 = Entry(raiz2,width=15)
                textoPosicionFinal1.grid(column=1, row=6)
                textoPaso1 = Entry(raiz2,width=15)
                textoPaso1.grid(column=2, row=6)
            if numeroDeSubintervalos>=2:
                textoPosicionInicial2 = Entry(raiz2,width=15)
                textoPosicionInicial2.grid(column=0, row=7, sticky=E)
                textoPosicionFinal2 = Entry(raiz2,width=15)
                textoPosicionFinal2.grid(column=1, row=7)
                textoPaso2 = Entry(raiz2,width=15)
                textoPaso2.grid(column=2, row=7)
            if numeroDeSubintervalos>=3:
                textoPosicionInicial3 = Entry(raiz2,width=15)
                textoPosicionInicial3.grid(column=0, row=8, sticky=E)
                textoPosicionFinal3 = Entry(raiz2,width=15)
                textoPosicionFinal3.grid(column=1, row=8)
                textoPaso3 = Entry(raiz2,width=15)
                textoPaso3.grid(column=2, row=8)
            if numeroDeSubintervalos>=4:
                textoPosicionInicial4 = Entry(raiz2,width=15)
                textoPosicionInicial4.grid(column=0, row=9, sticky=E)
                textoPosicionFinal4 = Entry(raiz2,width=15)
                textoPosicionFinal4.grid(column=1, row=9)
                textoPaso4 = Entry(raiz2,width=15)
                textoPaso4.grid(column=2, row=9)
            if numeroDeSubintervalos>=5:
                textoPosicionInicial5 = Entry(raiz2,width=15)
                textoPosicionInicial5.grid(column=0, row=10, sticky=E)
                textoPosicionFinal5 = Entry(raiz2,width=15)
                textoPosicionFinal5.grid(column=1, row=10)
                textoPaso5 = Entry(raiz2,width=15)
                textoPaso5.grid(column=2, row=10)
            if numeroDeSubintervalos>=6:
                textoPosicionInicial6 = Entry(raiz2,width=15)
                textoPosicionInicial6.grid(column=0, row=12,sticky=E)
                textoPosicionFinal6 = Entry(raiz2,width=15)
                textoPosicionFinal6.grid(column=1, row=12)
                textoPaso6 = Entry(raiz2,width=15)
                textoPaso6.grid(column=2, row=12)
            if numeroDeSubintervalos>=7:
                textoPosicionInicial7 = Entry(raiz2,width=15)
                textoPosicionInicial7.grid(column=0, row=13,sticky=E)
                textoPosicionFinal7 = Entry(raiz2,width=15)
                textoPosicionFinal7.grid(column=1, row=13)
                textoPaso7 = Entry(raiz2,width=15)
                textoPaso7.grid(column=2, row=13)
            if numeroDeSubintervalos>=8:
                textoPosicionInicial8 = Entry(raiz2,width=15)
                textoPosicionInicial8.grid(column=0, row=14,sticky=E)
                textoPosicionFinal8 = Entry(raiz2,width=15)
                textoPosicionFinal8.grid(column=1, row=14)
                textoPaso8 = Entry(raiz2,width=15)
                textoPaso8.grid(column=2, row=14)
            if numeroDeSubintervalos>=9:
                textoPosicionInicial9 = Entry(raiz2,width=15)
                textoPosicionInicial9.grid(column=0, row=15,sticky=E)
                textoPosicionFinal9 = Entry(raiz2,width=15)
                textoPosicionFinal9.grid(column=1, row=15)
                textoPaso9 = Entry(raiz2,width=15)
                textoPaso9.grid(column=2, row=15)
            if numeroDeSubintervalos>=10:
                textoPosicionInicial10 = Entry(raiz2,width=15)
                textoPosicionInicial10.grid(column=0, row=16,sticky=E)
                textoPosicionFinal10 = Entry(raiz2,width=15)
                textoPosicionFinal10.grid(column=1, row=16)
                textoPaso10 = Entry(raiz2,width=15)
                textoPaso10.grid(column=2, row=16)

            labelGraficos = Label(raiz2, text="Seleccione los valores que desea graficar\n en función de la longitud de onda:")
            labelGraficos.grid(column=0, row=17)
            
            
            Var1=IntVar()
            BotonV1 = Checkbutton(raiz2, text='X', variable=Var1).grid(column=0,row=18)
            
            
            Var2=IntVar()
            BotonV2 = Checkbutton(raiz2, text='Y', variable=Var2).grid(column=0,row=19)
            
            Var3=IntVar()
            BotonV3 = Checkbutton(raiz2, text='R', variable=Var3).grid(column=0,row=18, sticky=E)
            
            Var4=IntVar()
            BotonV4 = Checkbutton(raiz2, text='\u03B8', variable=Var4).grid(column=0,row=19, sticky=E)
        
        
        
        
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
                raizMedicion = Tk()
                raizMedicion.title('Martin y Gonzalo Pump and Probe - Midiendo a Posicion de la plataforma de retardo fija')
                raizMedicion.geometry('1000x1000')   
                labelEstado = Label(raizMedicion, text="Realizando la medicion. Tiempo estimado:" + tiempoDeMedicion + 'segundos')
                labelEstado.grid(column=0, row=0)
                
                canvas = FigureCanvasTkAgg(self.experimento.grafico.fig, master=raizMedicion)
                canvas.get_tk_widget().grid(row=1,column=0)
                canvas.draw()
                
                #BOTON CANCELAR MEDICION
                self.experimento.MedicionAPosicionFijaSMC(nombreArchivo,numeroDeConstantesDeTiempo,posicionFijaSMC_Stp,VectorLongitudDeOndaInicial_Stp,VectorLongitudDeOndaFinal_Stp,VectorPasoMono_Stp)
                self.experimento.grafico.GuardarGrafico(nombreArchivo)
                labelEstado = Label(raizMedicion, text="Medicion Finalizada. El archivo ha sido guardado con el nombre:" + nombreArchivo)
                labelEstado.grid(column=0, row=0)
                
                def Finalizar():
                    raizMedicion.destroy()    
                botonFinalizar = Button(raizMedicion, text="Finalizar", command=Finalizar)
                botonFinalizar.grid(column=1, row=1)
                
                raizMedicion.mainloop()
                
            botonIniciarMedicion = Button(raiz2, text="Iniciar Medicion", command=IniciarMedicion)
            botonIniciarMedicion.grid(column=3, row=20)
        
        
        botonSiguiente = Button(raiz2, text="Siguiente", command=SiguienteDePosicionFijaSMC)
        botonSiguiente.grid(column=1, row=4)
        
        raiz2.mainloop()

    def ProgramaMedicionCompleta(self):
        raiz3 = Tk()
        raiz3.title('Medicion Completa')    
        raiz3.geometry('1400x800')
        
        labelNombreArchivo = Label(raiz3, text="Ingrese el nombre del archivo con la extensión\n .csv. Por ejemplo: datos2.csv")
        labelNombreArchivo.grid(column=0, row=0)
        textoNombreArchivo = Entry(raiz3,width=15)
        textoNombreArchivo.grid(column=1, row=0)
        
        labelNumeroDeConstantesDeTiempo = Label(raiz3, text="Ingrese el número de constantes de tiempo de integracion\n del Lock-In. Debe ser un número entero positivo.")
        labelNumeroDeConstantesDeTiempo.grid(column=0, row=1)
        textoNumeroDeConstantesDeTiempo = Entry(raiz3,width=15)
        textoNumeroDeConstantesDeTiempo.grid(column=1, row=1)
        
        labelNumeroDeSubintervalosSMC = Label(raiz3, text="Ingrese la cantidad de secciones del barrido\n de la plataforma de retardo.")
        labelNumeroDeSubintervalosSMC.grid(column=0, row=2)
        textoNumeroDeSubintervalosSMC = Entry(raiz3,width=15)
        textoNumeroDeSubintervalosSMC.grid(column=1, row=2)
        
        labelNumeroDeSubintervalosMono = Label(raiz3, text="Ingrese la cantidad de secciones\n del barrido de longitud de onda.")
        labelNumeroDeSubintervalosMono.grid(column=0, row=3)
        textoNumeroDeSubintervalosMono = Entry(raiz3,width=15)
        textoNumeroDeSubintervalosMono.grid(column=1, row=3)
        
        def Siguiente():
            numeroDeSubintervalosSMC = int(textoNumeroDeSubintervalosSMC.get())
            numeroDeSubintervalosMono = int(textoNumeroDeSubintervalosMono.get())
            
            labelTituloInicialMono = Label(raiz3, text="Ingresar datos en nanómetros:\n desde 400 a 1000")
            labelTituloInicialMono.grid(column=0, row=5)
            labelTituloInicialMono = Label(raiz3, text="Longitud de \n Onda Inicial")
            labelTituloInicialMono.grid(column=0, row=6, sticky=E)
            labelTituloFinalMono = Label(raiz3, text="Longitud de \n Onda Final")
            labelTituloFinalMono.grid(column=1, row=6)
            labelTituloPasoMono = Label(raiz3, text="Paso")
            labelTituloPasoMono.grid(column=2, row=6)
        
            labelTituloConversor = Label(raiz3, text="Conversor de mm a fs")
            labelTituloConversor.grid(column=3, row=0)
            labelmm = Label(raiz3, text="mm")
            labelmm.grid(column=3, row=1)
            labelfs = Label(raiz3, text="fs")
            labelfs.grid(column=5, row=1)
            textomm = Entry(raiz3,width=15)
            textomm.grid(column=3, row=2)
            textofs = Entry(raiz3,width=15)
            textofs.grid(column=5, row=2)
            

            
            def ConvertirAfs():
                mm = textomm.get()
                fs = float(mm)*6666.666
                textofs.delete(0, END)
                textofs.insert(END, fs)

            def ConvertirAmm():
                fs = textofs.get()
                mm = float(fs)/6666.666
                textomm.delete(0, END)
                textomm.insert(END, mm)


            botonConvertirAmm = Button(raiz3, text="<-", command=ConvertirAmm)
            botonConvertirAmm.grid(column=4, row=1)
            
            botonConvertirAfs = Button(raiz3, text="->", command=ConvertirAfs)
            botonConvertirAfs.grid(column=4, row=2)
        
            if numeroDeSubintervalosMono>=1:
                textoPosicionInicial1Mono = Entry(raiz3,width=15)
                textoPosicionInicial1Mono.grid(column=0, row=7, sticky=E)
                textoPosicionFinal1Mono = Entry(raiz3,width=15)
                textoPosicionFinal1Mono.grid(column=1, row=7)
                textoPaso1Mono = Entry(raiz3,width=15)
                textoPaso1Mono.grid(column=2, row=7)
            if numeroDeSubintervalosMono>=2:
                textoPosicionInicial2Mono = Entry(raiz3,width=15)
                textoPosicionInicial2Mono.grid(column=0, row=8, sticky=E)
                textoPosicionFinal2Mono = Entry(raiz3,width=15)
                textoPosicionFinal2Mono.grid(column=1, row=8)
                textoPaso2Mono = Entry(raiz3,width=15)
                textoPaso2Mono.grid(column=2, row=8)
            if numeroDeSubintervalosMono>=3:
                textoPosicionInicial3Mono = Entry(raiz3,width=15)
                textoPosicionInicial3Mono.grid(column=0, row=9, sticky=E)
                textoPosicionFinal3Mono = Entry(raiz3,width=15)
                textoPosicionFinal3Mono.grid(column=1, row=9)
                textoPaso3Mono = Entry(raiz3,width=15)
                textoPaso3Mono.grid(column=2, row=9)
            if numeroDeSubintervalosMono>=4:
                textoPosicionInicial4Mono = Entry(raiz3,width=15)
                textoPosicionInicial4Mono.grid(column=0, row=10, sticky=E)
                textoPosicionFinal4Mono = Entry(raiz3,width=15)
                textoPosicionFinal4Mono.grid(column=1, row=10)
                textoPaso4Mono = Entry(raiz3,width=15)
                textoPaso4Mono.grid(column=2, row=10)
            if numeroDeSubintervalosMono>=5:
                textoPosicionInicial5Mono = Entry(raiz3,width=15)
                textoPosicionInicial5Mono.grid(column=0, row=11, sticky=E)
                textoPosicionFinal5Mono = Entry(raiz3,width=15)
                textoPosicionFinal5Mono.grid(column=1, row=11)
                textoPaso5Mono = Entry(raiz3,width=15)
                textoPaso5Mono.grid(column=2, row=11)
            if numeroDeSubintervalosMono>=6:
                textoPosicionInicial6Mono = Entry(raiz3,width=15)
                textoPosicionInicial6Mono.grid(column=0, row=12,sticky=E)
                textoPosicionFinal6Mono = Entry(raiz3,width=15)
                textoPosicionFinal6Mono.grid(column=1, row=12)
                textoPaso6Mono = Entry(raiz3,width=15)
                textoPaso6Mono.grid(column=2, row=12)
            if numeroDeSubintervalosMono>=7:
                textoPosicionInicial7Mono = Entry(raiz3,width=15)
                textoPosicionInicial7Mono.grid(column=0, row=13,sticky=E)
                textoPosicionFinal7Mono = Entry(raiz3,width=15)
                textoPosicionFinal7Mono.grid(column=1, row=13)
                textoPaso7Mono = Entry(raiz3,width=15)
                textoPaso7Mono.grid(column=2, row=13)
            if numeroDeSubintervalosMono>=8:
                textoPosicionInicial8Mono = Entry(raiz3,width=15)
                textoPosicionInicial8Mono.grid(column=0, row=14,sticky=E)
                textoPosicionFinal8Mono = Entry(raiz3,width=15)
                textoPosicionFinal8Mono.grid(column=1, row=14)
                textoPaso8Mono = Entry(raiz3,width=15)
                textoPaso8Mono.grid(column=2, row=14)
            if numeroDeSubintervalosMono>=9:
                textoPosicionInicial9Mono = Entry(raiz3,width=15)
                textoPosicionInicial9Mono.grid(column=0, row=15,sticky=E)
                textoPosicionFinal9Mono = Entry(raiz3,width=15)
                textoPosicionFinal9Mono.grid(column=1, row=15)
                textoPaso9Mono = Entry(raiz3,width=15)
                textoPaso9Mono.grid(column=2, row=15)
            if numeroDeSubintervalosMono>=10:
                textoPosicionInicial10Mono = Entry(raiz3,width=15)
                textoPosicionInicial10Mono.grid(column=0, row=16,sticky=E)
                textoPosicionFinal10Mono = Entry(raiz3,width=15)
                textoPosicionFinal10Mono.grid(column=1, row=16)
                textoPaso10Mono = Entry(raiz3,width=15)
                textoPaso10Mono.grid(column=2, row=16)


        
            labelTituloInicialSMC = Label(raiz3, text="Ingresar datos en milímetros:\n desde 0 a 25")
            labelTituloInicialSMC.grid(column=4, row=5)
            labelTituloInicialSMC = Label(raiz3, text="Posicion Inicial")
            labelTituloInicialSMC.grid(column=4, row=6, sticky=E)
            labelTituloFinalSMC = Label(raiz3, text="Posicion Final")
            labelTituloFinalSMC.grid(column=5, row=6)
            labelTituloPasoSMC = Label(raiz3, text="Paso")
            labelTituloPasoSMC.grid(column=6, row=6)
        
            if numeroDeSubintervalosSMC>=1:
                textoPosicionInicial1SMC = Entry(raiz3,width=15)
                textoPosicionInicial1SMC.grid(column=4, row=7, sticky=E)
                textoPosicionFinal1SMC = Entry(raiz3,width=15)
                textoPosicionFinal1SMC.grid(column=5, row=7)
                textoPaso1SMC = Entry(raiz3,width=15)
                textoPaso1SMC.grid(column=6, row=7)
            if numeroDeSubintervalosSMC>=2:
                textoPosicionInicial2SMC = Entry(raiz3,width=15)
                textoPosicionInicial2SMC.grid(column=4, row=8, sticky=E)
                textoPosicionFinal2SMC = Entry(raiz3,width=15)
                textoPosicionFinal2SMC.grid(column=5, row=8)
                textoPaso2SMC = Entry(raiz3,width=15)
                textoPaso2SMC.grid(column=6, row=8)
            if numeroDeSubintervalosSMC>=3:
                textoPosicionInicial3SMC = Entry(raiz3,width=15)
                textoPosicionInicial3SMC.grid(column=4, row=9, sticky=E)
                textoPosicionFinal3SMC = Entry(raiz3,width=15)
                textoPosicionFinal3SMC.grid(column=5, row=9)
                textoPaso3SMC = Entry(raiz3,width=15)
                textoPaso3SMC.grid(column=6, row=9)
            if numeroDeSubintervalosSMC>=4:
                textoPosicionInicial4SMC = Entry(raiz3,width=15)
                textoPosicionInicial4SMC.grid(column=4, row=10, sticky=E)
                textoPosicionFinal4SMC = Entry(raiz3,width=15)
                textoPosicionFinal4SMC.grid(column=5, row=10)
                textoPaso4SMC = Entry(raiz3,width=15)
                textoPaso4SMC.grid(column=6, row=10)
            if numeroDeSubintervalosSMC>=5:
                textoPosicionInicial5SMC = Entry(raiz3,width=15)
                textoPosicionInicial5SMC.grid(column=4, row=11, sticky=E)
                textoPosicionFinal5SMC = Entry(raiz3,width=15)
                textoPosicionFinal5SMC.grid(column=5, row=11)
                textoPaso5SMC = Entry(raiz3,width=15)
                textoPaso5SMC.grid(column=6, row=11)
            if numeroDeSubintervalosSMC>=6:
                textoPosicionInicial6SMC = Entry(raiz3,width=15)
                textoPosicionInicial6SMC.grid(column=4, row=12,sticky=E)
                textoPosicionFinal6SMC = Entry(raiz3,width=15)
                textoPosicionFinal6SMC.grid(column=5, row=12)
                textoPaso6SMC = Entry(raiz3,width=15)
                textoPaso6SMC.grid(column=6, row=12)
            if numeroDeSubintervalosSMC>=7:
                textoPosicionInicial7SMC = Entry(raiz3,width=15)
                textoPosicionInicial7SMC.grid(column=4, row=13,sticky=E)
                textoPosicionFinal7SMC = Entry(raiz3,width=15)
                textoPosicionFinal7SMC.grid(column=5, row=13)
                textoPaso7SMC = Entry(raiz3,width=15)
                textoPaso7SMC.grid(column=6, row=13)
            if numeroDeSubintervalosSMC>=8:
                textoPosicionInicial8SMC = Entry(raiz3,width=15)
                textoPosicionInicial8SMC.grid(column=4, row=14,sticky=E)
                textoPosicionFinal8SMC = Entry(raiz3,width=15)
                textoPosicionFinal8SMC.grid(column=5, row=14)
                textoPaso8SMC = Entry(raiz3,width=15)
                textoPaso8SMC.grid(column=6, row=14)
            if numeroDeSubintervalosSMC>=9:
                textoPosicionInicial9SMC = Entry(raiz3,width=15)
                textoPosicionInicial9SMC.grid(column=4, row=15,sticky=E)
                textoPosicionFinal9SMC = Entry(raiz3,width=15)
                textoPosicionFinal9SMC.grid(column=5, row=15)
                textoPaso9SMC = Entry(raiz3,width=15)
                textoPaso9SMC.grid(column=6, row=15)
            if numeroDeSubintervalosSMC>=10:
                textoPosicionInicial10SMC = Entry(raiz3,width=15)
                textoPosicionInicial10SMC.grid(column=4, row=16,sticky=E)
                textoPosicionFinal10SMC = Entry(raiz3,width=15)
                textoPosicionFinal10SMC.grid(column=5, row=16)
                textoPaso10SMC = Entry(raiz3,width=15)
                textoPaso10SMC.grid(column=6, row=16)

            
            labelGrafico = Label(raiz3, text="Seleccione las magnitudes que desea graficar:")
            labelGrafico.grid(column=0, row=17)
            
            
            
            Var1=IntVar()
            BotonV1 = Checkbutton(raiz3, text='X', variable=Var1).grid(column=0,row=18)
            
            Var2=IntVar()
            BotonV2 = Checkbutton(raiz3, text='Y', variable=Var2).grid(column=0,row=19)
            
            Var3=IntVar()
            BotonV3 = Checkbutton(raiz3, text='R', variable=Var3).grid(column=0,row=18, sticky=E)
            
            Var4=IntVar()
            BotonV4 = Checkbutton(raiz3, text='\u03B8', variable=Var4).grid(column=0,row=19, sticky=E)
            
            labelEjeX = Label(raiz3, text="Seleccione la magnitud que desea graficar en el eje X:")
            labelEjeX.grid(column=0, row=20)
            
            choices = ['Tiempo', 'Distancia']
            variable = StringVar(raiz3)
            variable.set('Tiempo')
            w = OptionMenu(raiz3, variable, *choices)
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
                if numeroDeSubintervalos>=6:
                    VectorLongitudDeOndaInicial_Stp[5] = int(float(textoPosicionInicial6Mono.get())/0.03125)
                    VectorLongitudDeOndaFinal_Stp[5] = int(float(textoPosicionFinal6Mono.get())/0.03125)
                    VectorPasoMono_Stp[5] = int(float(textoPaso6Mono.get())/0.03125)
                if numeroDeSubintervalos>=7:
                    VectorLongitudDeOndaInicial_Stp[6] = int(float(textoPosicionInicial7Mono.get())/0.03125)
                    VectorLongitudDeOndaFinal_Stp[6] = int(float(textoPosicionFinal7Mono.get())/0.03125)
                    VectorPasoMono_Stp[6] = int(float(textoPaso7Mono.get())/0.03125)
                if numeroDeSubintervalos>=8:
                    VectorLongitudDeOndaInicial_Stp[7] = int(float(textoPosicionInicial8Mono.get())/0.03125)
                    VectorLongitudDeOndaFinal_Stp[7] = int(float(textoPosicionFinal8Mono.get())/0.03125)
                    VectorPasoMono_Stp[7] = int(float(textoPaso8Mono.get())/0.03125)
                if numeroDeSubintervalos>=9:
                    VectorLongitudDeOndaInicial_Stp[8] = int(float(textoPosicionInicial9Mono.get())/0.03125)
                    VectorLongitudDeOndaFinal_Stp[8] = int(float(textoPosicionFinal9Mono.get())/0.03125)
                    VectorPasoMono_Stp[8] = int(float(textoPaso9Mono.get())/0.03125)
                if numeroDeSubintervalos>=10:
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
                if numeroDeSubintervalos>=6:
                    VectorPosicionInicialSMC_Stp[5] = int(float(textoPosicionInicial6SMC.get())*10000)
                    VectorPosicionFinalSMC_Stp[5] = int(float(textoPosicionFinal6SMC.get())*10000)
                    VectorPasoSMC_Stp[5] = int(float(textoPaso6SMC.get())*10000)
                if numeroDeSubintervalos>=7:
                    VectorPosicionInicialSMC_Stp[6] = int(float(textoPosicionInicial7SMC.get())*10000)
                    VectorPosicionFinalSMC_Stp[6] = int(float(textoPosicionFinal7SMC.get())*10000)
                    VectorPasoSMC_Stp[6] = int(float(textoPaso7SMC.get())*10000)
                if numeroDeSubintervalos>=8:
                    VectorPosicionInicialSMC_Stp[7] = int(float(textoPosicionInicial8SMC.get())*10000)
                    VectorPosicionFinalSMC_Stp[7] = int(float(textoPosicionFinal8SMC.get())*10000)
                    VectorPasoSMC_Stp[7] = int(float(textoPaso8SMC.get())*10000)
                if numeroDeSubintervalos>=9:
                    VectorPosicionInicialSMC_Stp[8] = int(float(textoPosicionInicial9SMC.get())*10000)
                    VectorPosicionFinalSMC_Stp[8] = int(float(textoPosicionFinal9SMC.get())*10000)
                    VectorPasoSMC_Stp[8] = int(float(textoPaso9SMC.get())*10000)
                if numeroDeSubintervalos>=10:
                    VectorPosicionInicialSMC_Stp[9] = int(float(textoPosicionInicial10SMC.get())*10000)
                    VectorPosicionFinalSMC_Stp[9] = int(float(textoPosicionFinal10SMC.get())*10000)
                    VectorPasoSMC_Stp[9] = int(float(textoPaso10SMC.get())*10000)
                    
                
                raiz3.destroy()
                tiempoDeMedicion = str(self.CalcularTiempoDeMedicionCompleta(numeroDeConstantesDeTiempo,VectorPosicionInicialSMC_Stp,VectorPosicionFinalSMC_Stp,VectorPasoSMC_Stp,VectorLongitudDeOndaInicial_Stp,VectorLongitudDeOndaFinal_Stp,VectorPasoMono_Stp))
                raizMedicion = Tk()
                raizMedicion.title('Martin y Gonzalo Pump and Probe - Medición Completa')
                raizMedicion.geometry('1000x1000')   
                labelEstado = Label(raizMedicion, text="Realizando la medicion. Tiempo estimado:" + tiempoDeMedicion + 'segundos')
                labelEstado.grid(column=0, row=0)
                
                canvas = FigureCanvasTkAgg(self.experimento.grafico.fig, master=raizMedicion)
                canvas.get_tk_widget().grid(row=1,column=0)
                canvas.draw()
                
                #BOTON CANCELAR MEDICION
                
                self.experimento.MedicionCompleta(nombreArchivo,numeroDeConstantesDeTiempo,VectorPosicionInicialSMC_Stp,VectorPosicionFinalSMC_Stp,VectorPasoSMC_Stp,VectorLongitudDeOndaInicial_Stp,VectorLongitudDeOndaFinal_Stp,VectorPasoMono_Stp)
                self.experimento.grafico.PonerColorbars()
                self.experimento.grafico.GuardarGrafico(nombreArchivo)
                labelEstado = Label(raizMedicion, text="Medicion Finalizada. El archivo ha sido guardado con el nombre:" + nombreArchivo)
                labelEstado.grid(column=0, row=0)
                
                def Finalizar():
                    raizMedicion.destroy()    
                botonFinalizar = Button(raizMedicion, text="Finalizar", command=Finalizar)
                botonFinalizar.grid(column=1, row=1)
                
                raizMedicion.mainloop()
                
                
            botonIniciarMedicion = Button(raiz3, text="Iniciar Medicion", command=IniciarMedicion)
            botonIniciarMedicion.grid(column=3, row=22)
        
        
        
        botonSiguiente = Button(raiz3, text="Siguiente", command=Siguiente)
        botonSiguiente.grid(column=1, row=4)
        
        raiz3.mainloop()
    
    
        
    def SetearPuertos(self):
    
        raiz4 = Tk()
        raiz4.title('Martin y Gonzalo Pump and Probe - Seteo de puertos')
        raiz4.geometry('1000x800')
        
        labelSMC = Label(raiz4, text = 'Ingrese el número de puerto COM correspondiente al SMC. Ejemplo : 5')
        labelSMC.grid(column=0, row=0)
        textoSMC = Entry(raiz4, width=5)
        textoSMC.grid(column=1, row=0)
            
        labelMono = Label(raiz4, text = 'Ingrese el número de puerto COM correspondiente al Monocromador. Ejemplo : 4')
        labelMono.grid(column=0, row=1)
        textoMono = Entry(raiz4, width=5)
        textoMono.grid(column=1, row=1)
   
        labelLockIn = Label(raiz4, text = 'Ingrese el número de dirección correspondiente al Lock-In. Puede verse en la pantalla del mismo. Ejemplo : 11')
        labelLockIn.grid(column=0, row=2)
        textoLockIn = Entry(raiz4, width=5)
        textoLockIn.grid(column=1, row=2)
        
#       labelOscilos = Label(raiz4, text = 'Ingrese el número de puerto COM correspondiente al SMC. Ejemplo : 5')
#       labelSMC.grid(column=0, row=0)
#       textoSMC = Entry(raiz4, width=5)
#       textoSMC.grid(column=1, row=0)
    
        def AdquirirPuertos():
            self.VectorDePuertos = (int(textoSMC.get()), int(textoMono.get()), int(textoLockIn.get()))
        #    self.experimento = Experimento(self.VectorDePuertos) # CHEQUEAR SI AL SETEAR POR SEGUNDA VEZ LOS PUERTOS,
                                                                # HAY UN OBJETO NUEVO O ES EL MISMO
            raiz4.destroy()
            self.Continuar()

    
        botonOk = Button(raiz4, text = 'Setear', command = AdquirirPuertos)
        botonOk.grid(column=1,row=3)
        
        raiz4.mainloop()
        
    def Continuar(self):
        raiz = Tk()
        raiz.title('Martin y Gonzalo Pump and Probe')
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
            
        btn1 = Button(raiz, text="Setear Puertos", command=SetearPuertosBis)
        btn1.grid(column=1, row=0)
        btn2 = Button(raiz, text="A Lambda Fija", command=ProgramaMedicionALambdaFijaBis)
        btn2.grid(column=2, row=0)
        btn3 = Button(raiz, text="A Posicion Fija", command=ProgramaMedicionAPosicionFijaBis)
        btn3.grid(column=3, row=0)
        btn4 = Button(raiz, text="Completa", command=ProgramaMedicionCompletaBis)
        btn4.grid(column=4, row=0)
        raiz.mainloop()

