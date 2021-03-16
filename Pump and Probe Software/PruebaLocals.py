# -*- coding: utf-8 -*-
"""
Created on Fri Mar 12 18:07:02 2021

@author: LEC
"""

class Grafico():
    def __init__(self):
        self.b1 = 0
    
    def chequeo(self):
        a = 5
        print('a' in locals())
        print(hasattr(self,'b1'))