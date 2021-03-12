import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np

fig = plt.figure(figsize=(13,13))
ax1 = fig.add_subplot(221)
ax2 = fig.add_subplot(222)
vectorX = np.array(1)
vectorX = np.append(vectorX, 1.1)
vectorX = np.append(vectorX, 1.2)
vectorX = np.append(vectorX, 1.3)
vectorX = np.append(vectorX, 1.4)
vectorX = np.append(vectorX, 1.5)
vectorY = np.array(420)
vectorY = np.append(vectorY, 421)
vectorY = np.append(vectorY, 422)
vectorY = np.append(vectorY, 423)
vectorY = np.append(vectorY, 424)
vectorY = np.append(vectorY, 425)
vectorY = np.append(vectorY, 426)
vectorY = np.append(vectorY, 427)
vectorY = np.append(vectorY, 428)
vectorY = np.append(vectorY, 429)
M1 = np.zeros((len(vectorX),len(vectorY)))
M1[1][1]=5
M2 = np.zeros((len(vectorX),len(vectorY)))
M2[4][4]=5
plot1 = ax1.contourf(vectorY, vectorX, M1, 20, cmap='RdGy')
plot2 = ax2.contourf(vectorY, vectorX, M2, 20, cmap='RdGy')

divider = make_axes_locatable(ax1)
cax = divider.append_axes("right", size="5%", pad=0.05)
fig.colorbar(plot1,cax=cax)

divider = make_axes_locatable(ax2)
cax = divider.append_axes("right", size="5%", pad=0.05)
fig.colorbar(plot2,cax=cax)

plt.show()