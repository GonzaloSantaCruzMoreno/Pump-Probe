# -*- coding: utf-8 -*-
"""
Created on Thu Feb 25 16:29:35 2021

@author: Usuario
"""


import pyvisa
import time

class LockIn():
    def __init__(self,puerto):
        rm = pyvisa.ResourceManager()  # OJO EL SELF, PUEDE NO FUNCIONAR
        comando = 'GPIB0::' + str(puerto) + '::INSTR'
        self.address = rm.open_resource(comando)
        #self.ConfigurarLockIn()
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
