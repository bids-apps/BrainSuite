#!/usr/bin/env fslpython

import numpy as np
import matplotlib.pyplot as plt
import seaborn
seaborn.set()







#=========================================================================================
# QUAD - Motion parameters
# Matteo Bastiani
# 01-06-2017, FMRIB, Oxford
#=========================================================================================

def main(pdf, data, eddy):
    """
    Generate page of the single subject report pdf that contains plots of the estimated 
    motion parameters.
    Absolute and relative displacement plots are also shown.
    
    Arguments:
        - pdf: qc pdf file
        - data: data dictionary containg information about the dataset
        - eddy: EDDY dictionary containg useful qc information
    """
    #================================================
    # Prepare figure
    plt.figure(figsize=(8.27,11.69))   # Standard portrait A4 sizes
    plt.suptitle('Subject ' + data['subj_id'],fontsize=10, fontweight='bold')

    # Plot estimated translations along the 3 axes
    ax1 = plt.subplot2grid((3,1), (0,0))
    ax1.plot(eddy['params'][:,0], 'r', linewidth=2, label="x")
    ax1.plot(eddy['params'][:,1], 'g', linewidth=2, label="y")
    ax1.plot(eddy['params'][:,2], 'b', linewidth=2, label="z")
    ax1.set_xbound(1, data['bvals'].size)
    ax1.set_xlabel("Volume")
    ax1.set_ylabel("Translation [mm]")
    ax1.set_title("Eddy estimated translations (mm)")
    ax1.legend(loc='best', frameon=True, framealpha=0.5)

    # Plot estimated rotations around the 3 axes
    ax2 = plt.subplot2grid((3,1), (1,0))
    ax2.plot(np.rad2deg(eddy['params'][:,3]), 'r', linewidth=2, label="x")
    ax2.plot(np.rad2deg(eddy['params'][:,4]), 'g', linewidth=2, label="y")
    ax2.plot(np.rad2deg(eddy['params'][:,5]), 'b', linewidth=2, label="z")
    ax2.set_xbound(1, data['bvals'].size)
    ax2.set_xlabel("Volume")
    ax2.set_ylabel("Rotation [deg]")
    ax2.set_title("Eddy estimated rotations (deg)")
    ax2.legend(loc='best', frameon=True, framealpha=0.5)

    # Plot estimated absolute and relative displacement 
    ax3 = plt.subplot2grid((3,1), (2,0))
    ax3.plot(eddy['motion'][:,0], 'r', linewidth=2, label="Absolute")
    ax3.plot(eddy['motion'][:,1], 'b', linewidth=2, label="Relative")
    ax3.set_xbound(1, data['bvals'].size)
    ax3.set_xlabel("Volume")
    ax3.set_ylabel("Displacement [mm]")
    ax3.set_title('Estimated mean displacement')
    ax3.legend(loc='best', frameon=True, framealpha=0.5)
    ax3.set_ylim(0, 0.5+np.max(eddy['motion']))

    # Format figure, save and close it
    plt.tight_layout(h_pad=1, pad=4)
    plt.savefig(pdf, format='pdf')
    plt.close()
    
    #================================================
    # Generate individual plots separately
    
    # Prepare figure
    plt.figure(figsize=(8.27,4)) 

    # Plot estimated translations along the 3 axes
    ax1 = plt.subplot(111)
    ax1.plot(eddy['params'][:,0], 'r', linewidth=2, label="x")
    ax1.plot(eddy['params'][:,1], 'g', linewidth=2, label="y")
    ax1.plot(eddy['params'][:,2], 'b', linewidth=2, label="z")
    ax1.set_xbound(1, data['bvals'].size)
    ax1.set_xlabel("Volume")
    ax1.set_ylabel("Translation [mm]")
    ax1.set_title("Eddy estimated translations (mm)")
    ax1.legend(loc='best', frameon=True, framealpha=0.5)
    
    plt.tight_layout()
    plt.savefig(data['qc_path']+'translations.png', format='png')
    plt.close()
    
    plt.figure(figsize=(8.27,4))  

    # Plot estimated rotations around the 3 axes
    ax2 = plt.subplot(111)
    ax2.plot(np.rad2deg(eddy['params'][:,3]), 'r', linewidth=2, label="x")
    ax2.plot(np.rad2deg(eddy['params'][:,4]), 'g', linewidth=2, label="y")
    ax2.plot(np.rad2deg(eddy['params'][:,5]), 'b', linewidth=2, label="z")
    ax2.set_xbound(1, data['bvals'].size)
    ax2.set_xlabel("Volume")
    ax2.set_ylabel("Rotation [deg]")
    ax2.set_title("Eddy estimated rotations (deg)")
    ax2.legend(loc='best', frameon=True, framealpha=0.5)
    
    plt.tight_layout()
    plt.savefig(data['qc_path']+'rotations.png', format='png')
    plt.close()

    plt.figure(figsize=(8.27,4))

    # Plot estimated absolute and relative displacement 
    ax3 = plt.subplot(111)
    ax3.plot(eddy['motion'][:,0], 'r', linewidth=2, label="Absolute")
    ax3.plot(eddy['motion'][:,1], 'b', linewidth=2, label="Relative")
    ax3.set_xbound(1, data['bvals'].size)
    ax3.set_xlabel("Volume")
    ax3.set_ylabel("Displacement [mm]")
    ax3.set_title('Estimated mean displacement')
    ax3.legend(loc='best', frameon=True, framealpha=0.5)
    ax3.set_ylim(0, 0.5+np.max(eddy['motion']))

    plt.tight_layout()
    plt.savefig(data['qc_path']+'displacement.png', format='png')
    plt.close()