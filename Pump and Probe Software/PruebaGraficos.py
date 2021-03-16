# -*- coding: utf-8 -*-
"""
Created on Sat Mar 13 21:02:40 2021

@author: Usuario
"""
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def graficar():
    longitudDeOnda = 400
    fig = plt.figure()
    ax1 = fig.add_subplot(221)
    x = [1, 2, 3, 4, 5] 
    y = [1, 4, 9, 16, 25] 
    ax1.plot(x, y) 
    frase = '\u03BB = ' + str(longitudDeOnda) + ' nm'
    ax1.legend([frase])
    ax2 = fig.add_subplot(222)
    ax2.plot(x, y) 
#    ax2.legend('\u03BB = ' + str(longitudDeOnda) + ' nm')    

