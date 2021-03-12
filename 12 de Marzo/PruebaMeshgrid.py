# -*- coding: utf-8 -*-
"""
Created on Tue Mar  2 18:54:48 2021

@author: LEC
"""
import numpy as np

x = list()
z = list()

x.append(4)
x.append(3)
x.append(5)
z.append(1)
z.append(0)
z.append(2)

X, Z = np.meshgrid(x,z)

