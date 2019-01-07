import scipy as sp
"""
Created on Tue Jul 11 22:42:56 2017

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

    if sp.any(sp.isnan(pre_signal)):
        print('there are NaNs in the data matrix, making them zero')

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

   Please cite the following publication:
       AA Joshi, M Chong, RM Leahy, BrainSync: An Orthogonal Transformation
       for Synchronization of fMRI Data Across Subjects, Proc. MICCAI 2017,
       in press.
       """
    if X.shape[0] > X.shape[1]:
        print('The input is possibly transposed. Please check to make sure \
that the input is time x vertices!')

    C = sp.dot(X, Y.T)
    U, _, V = sp.linalg.svd(C)
    R = sp.dot(U, V)
    Y2 = sp.dot(R, Y)
    return Y2, R
