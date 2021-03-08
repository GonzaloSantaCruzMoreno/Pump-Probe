import tkinter as tk
import threading as th
import numpy as np
import time

def MediciónManual():
    raiz5 = tk.Tk()
    raiz5.title('Pump and Probe Software - Medición Manual')
    raiz5.geometry('1000x800')    
    labelNumeroDeConstantesDeTiempo = tk.Label(raiz5, text = 'Numero de constantes de tiempo a esperar del Lock In:')
    labelNumeroDeConstantesDeTiempo.grid(column=0, row=0)
    textoNumeroDeConstantesDeTiempo = tk.Entry(raiz5, width=5)
    textoNumeroDeConstantesDeTiempo.grid(column=1, row=0)
    def SetearNumeroDeConstantesDeTiempo():
        comando = int(textoNumeroDeConstantesDeTiempo.get())
#        self.experimento.lockin.CalcularTiempoDeIntegracion(comando)
    botonSetearNumeroDeConstantesDeTiempo = tk.Button(raiz5, text="Setear", command=SetearNumeroDeConstantesDeTiempo)
    botonSetearNumeroDeConstantesDeTiempo.grid(column=2, row=0)
    
    labelPosicionSMC = tk.Label(raiz5, text = 'Posicion plataforma de retardo en mm. (ej: 5.24)')
    labelPosicionSMC.grid(column=0, row=1)
    textoPosicionSMC = tk.Entry(raiz5, width=5)
    textoPosicionSMC.grid(column=1, row=1)
    def IrALaPosicionSMC():
        comando = float(textoPosicionSMC.get())
#        self.experimento.smc.Mover(comando)
    botonIrALaPosicionSMC = tk.Button(raiz5, text="Mover", command=IrALaPosicionSMC)
    botonIrALaPosicionSMC.grid(column=2, row=1)
    
    labelPosicionMonocromador = tk.Label(raiz5, text = 'Posicion red de difracción en nm. (ej: 532.7)')
    labelPosicionMonocromador.grid(column=0, row=2)
    textoPosicionMonocromador = tk.Entry(raiz5, width=5)
    textoPosicionMonocromador.grid(column=1, row=2)
    def IrALaPosicionMonocromador():
        comando = float(textoPosicionMonocromador.get())
#        self.experimento.mono.Mover(comando)
    botonIrALaPosicionMonocromador = tk.Button(raiz5, text="Mover", command=IrALaPosicionMonocromador)
    botonIrALaPosicionMonocromador.grid(column=2, row=2)

    labelX = tk.Label(raiz5, text = 'X')
    labelX.grid(column=0, row=4)
    textoX = tk.Entry(raiz5, width=5)
    textoX.grid(column=0, row=5)
    labelY = tk.Label(raiz5, text = 'Y')
    labelY.grid(column=1, row=4)
    textoY = tk.Entry(raiz5, width=5)
    textoY.grid(column=1, row=5)
    labelR = tk.Label(raiz5, text = 'R')
    labelR.grid(column=2, row=4)
    textoR = tk.Entry(raiz5, width=5)
    textoR.grid(column=2, row=5)
    labelTheta = tk.Label(raiz5, text = '\u03B8')
    labelTheta.grid(column=3, row=4)
    textoTheta = tk.Entry(raiz5, width=5)
    textoTheta.grid(column=3, row=5)
    labelAuxIn = tk.Label(raiz5, text = 'Aux In 1 (Señal DC)')
    labelAuxIn.grid(column=4, row=4)
    textoAuxIn = tk.Entry(raiz5, width=5)
    textoAuxIn.grid(column=4, row=5)
    labelCocienteXConAuxIn = tk.Label(raiz5, text = 'X/Aux In 1')
    labelCocienteXConAuxIn.grid(column=5, row=4)
    textoCocienteXConAuxIn = tk.Entry(raiz5, width=5)
    textoCocienteXConAuxIn.grid(column=5, row=5)

    def IniciarMedicion():
        global t
        t = th.Thread(target=Medicion)   
        t.do_run = True
#        if t.do_run == True:
        t.start()
#        if t.do_run == False:
#            t.do_run = True
    def Medicion():
        MedicionBis()
        print('hola')
    def MedicionBis():
        while True:
            if t.do_run == False:
                return
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
            time.sleep(0.5)
    def FrenarMedicion():
        t.do_run = False
        t.join()
    
    botonIniciarMedicion = tk.Button(raiz5, text="Iniciar Medicion", command=IniciarMedicion)
    botonIniciarMedicion.grid(column=1, row=3)
    botonFrenarMedicion = tk.Button(raiz5, text="Frenar Medicion", command=FrenarMedicion)
    botonFrenarMedicion.grid(column=2, row=3)
    raiz5.mainloop()
        
