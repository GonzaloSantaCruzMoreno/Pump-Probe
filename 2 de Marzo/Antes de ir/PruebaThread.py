# -*- coding: utf-8 -*-
"""
Created on Sun Feb 28 17:20:15 2021

@author: Usuario
"""
import time
import threading as th



def IniciarMedicion():
    t.start()
def Medicion():
    while getattr(t, "do_run", True):
        print('medicion')
        time.sleep(2)

t = th.Thread(target=Medicion)
    
def FrenarMedicion():
    t.do_run = False
    t.join()
