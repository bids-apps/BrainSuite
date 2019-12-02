import scipy as sp
import numpy as np
from numpy.random import random
from scipy.stats import special_ortho_group
from tqdm import tqdm
import scipy.io as spio
"""
Created on Tue Jul 11 22:42:56 2017
Author Anand A Joshi (ajoshi@usc.edu)
   Please cite the following publication:
   Joshi, A. A., Chong, M., Li, J., Choi, S., & Leahy, R. M. (2018). Are you thinking what I'm thinking? Synchronization of resting fMRI time-series across subjects. NeuroImage, 172, 740-752. https://doi.org/10.1016/j.neuroimage.2018.01.058
"""
def normalizeData(pre_signal):
    """
     normed_signal, mean_vector, std_vector = normalizeData(pre_signal)
     This function normalizes the input signal to have 0 mean and unit
     norm in time.
     pre_signal: Time x Original Vertices data
     normed_signal: Normalized (Time x Vertices) signal
     mean_vector: 1 x Vertices mean for each time series
     norm_vector : 1 x Vertices norm for each time series
    """

    #    if sp.any(sp.isnan(pre_signal)):
    #        print('there are NaNs in the data matrix, making them zero')

    pre_signal[sp.isnan(pre_signal)] = 0
    mean_vector = sp.mean(pre_signal, axis=0, keepdims=True)
    normed_signal = pre_signal - mean_vector
    norm_vector = sp.linalg.norm(normed_signal, axis=0, keepdims=True)
    norm_vector[norm_vector == 0] = 1e-116
    normed_signal = normed_signal / norm_vector

    return normed_signal, mean_vector, norm_vector

def brainSync(X, Y):
    """
   Input:
       X - Time series of the reference data (Time x Vertex) \n
       Y - Time series of the subject data (Time x Vertex)

   Output:
       Y2 - Synced subject data (Time x Vertex)\n
       R - The orthogonal rotation matrix (Time x Time)
       """
    if X.shape[0] > X.shape[1]:
        print('The input is possibly transposed. Please check to make sure \
that the input is time x vertices!')

    C = sp.dot(X, Y.T)
    U, _, V = sp.linalg.svd(C)
    R = sp.dot(U, V)
    Y2 = sp.dot(R, Y)
    return Y2, R

def IDrefsub_BrainSync(sub_data):
    ''' 
    Input:
        sub_data: input vector x time x subject data matrix containing reference subjects 
            load data by using module stats_utils.load_bfp_data
    Ouput:
        subRef_data = vector x time matrix the of most representative subject
        q = # of reference subject according to order of sub_data input 
    '''
    nSub = sub_data.shape[2]
    print('calculating pairwise correlations between all pairs of ' + str(nSub) + ' subjects')
    dist_all_orig = sp.zeros([nSub, nSub])
    dist_all_rot = dist_all_orig.copy()

    for ind1 in range(nSub):
        for ind2 in range(nSub):
            dist_all_orig[ind1, ind2] = sp.linalg.norm(sub_data[:, :, ind1] - sub_data[:, :, ind2])
            sub_data_rot, _ = brainSync(X=sub_data[:, :, ind1], Y=sub_data[:, :, ind2])
            dist_all_rot[ind1, ind2] = sp.linalg.norm(sub_data[:, :, ind1] -sub_data_rot)
            print(ind1, ind2, dist_all_rot[ind1, ind2])
    q = sp.argmin(dist_all_rot.sum(1))
    subRef_data = sub_data[:, :, q]
    print('Subject number ' + str(q) + ' identified as most representative subject')
    return subRef_data, q

def generate_avgAtlas(subRef_data, sub_data):
    ''' 
    generates atlas by syncing data across subjects to one reference subject 
    Inputs:
        subRef_data: Vertex x Time matrix of reference subject
        sub_data: Vertex x Time x Subject matrix of subject data
    Output:
        avgAtlas_data: Vertex x Time matrix of average atlas
    '''
    subNum = sub_data.shape[2]
    numT = subRef_data.shape[0]
    numV = subRef_data.shape[1]
    avg_atlas = sp.zeros((numT,numV))
    for ind in range(int(subNum)):
        s_data, _ = brainSync(subRef_data, sub_data[:,:,ind])
        avg_atlas += s_data
    avg_atlas /= subNum

    return avg_atlas

def ref_avg_atlas(ref_id, sub_files, len_time=235):
    ''' Generates atlas by syncing to one reference subject'''
    ''' Input '''

    ref_data = spio.loadmat(sub_files[ref_id])['dtseries'].T
    ref_data, _, _ = normalizeData(ref_data[:len_time, :])

    for ind in tqdm(range(len(sub_files))):
        sub_data = spio.loadmat(sub_files[ind])['dtseries'].T
        sub_data, _, _ = normalizeData(sub_data[:len_time, :])
        s_data, _ = brainSync(X=ref_data, Y=sub_data)
        if ind == 0:
            avg_atlas = s_data
        else:
            avg_atlas += s_data

    avg_atlas /= len(sub_files)

    return avg_atlas

def groupBrainSync(S):
    # Group BrainSync algorithm developed by Haleh Akrami

    numT = S.shape[0]
    numV = S.shape[1]
    SubNum = S.shape[2]

    # init random matrix for Os
    Os = sp.zeros((numT, numT, SubNum))
    for i in range(SubNum):  #initializeing O
        #        R = 2 * rnd.random(size=(numT, numT)) - 1; #define a random matrix with unity distributian from -1 to 1
        Os[:, :, i] = special_ortho_group.rvs(
            numT)  #(sp.dot(R , R.T)^(-1/2) , R;  #orthogonal rows of matrix

    Error = 1
    PreError = 1
    relcost = 1

    alpha = 1e-6
    var = 0
    Costdif = sp.zeros(10000)

    print('init done')

    # Initialize PreError from gloal average
    X = sp.zeros((numT, numV))
    for j in range(SubNum):  #calculate X
        X = sp.dot(Os[:, :, j], S[:, :, j]) + X

    X = X / SubNum
    InError = 0

    for j in range(SubNum):
        etemp = sp.dot(Os[:, :, j], S[:, :, j]) - X
        InError = InError + sp.trace(sp.dot(etemp,
                                            etemp.T))  #calculating error

    # Find best Orthogognal map, by minimizing error (distance) from average
    while relcost > alpha:
        var = var + 1

        print('subject iteration')
        for i in tqdm(range(SubNum)):
            X = sp.zeros((numT, numV))
            for j in range(SubNum):  #calculate X average excluded subject i
                if j != i:
                    X = sp.dot(Os[:, :, j], S[:, :, j]) + X
            # Y is i excluded average
            Y = X / (SubNum - 1)

            # Update Orthogonal matrix with BrainSync projection technique
            U, _, V = sp.linalg.svd(sp.dot(Y, S[:, :, i].T))
            Os[:, :, i] = sp.dot(U, V)

    # print('calculate error')
        Error = 0
        # New Average with all subject updated orthogonal matrix
        # update last subject outside loop
        X2 = (X + sp.dot(Os[:, :, i], S[:, :, i])) / SubNum

        # Calculate error of all subjects from average map
        for j in range(SubNum):
            etemp = sp.dot(Os[:, :, j], S[:, :, j]) - X2
            Error = Error + sp.trace(sp.dot(etemp,
                                            etemp.T))  #calculating error

        relcost = np.abs(Error - PreError) / np.abs(InError)
        Costdif[var] = PreError - Error
        PreError = Error

        print('Error = %g, var = %g, relcost = %g\n' % (Error, var, relcost))

    Costdif= Costdif[:var] # = []
    Costdif = Costdif[1:]
    TotalError = Error

    return X2, Os, Costdif, TotalError