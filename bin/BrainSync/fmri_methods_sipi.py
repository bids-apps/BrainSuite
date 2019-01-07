# -*- coding: utf-8 -*-
"""
Created on Mon Jul 25 14:59:29 2016

@author: ajoshi
"""
import scipy as sp
from sklearn.metrics.pairwise import pairwise_distances
from sklearn.utils.linear_assignment_ import linear_assignment
import matplotlib.pyplot as plt
import nibabel.freesurfer.io as fsio
from dfsio import readdfs
from scipy.spatial import cKDTree
import nibabel as nib
#from lxml import etree
import numpy as np
from scipy.stats import f as f_distrib

def hotelling_t2(X,Y):

    nx=X.shape[1];ny=Y.shape[1];p=X.shape[0];
    Xbar=X.mean(1);Ybar=Y.mean(1);
    Xbar=Xbar.reshape(Xbar.shape[0],1,Xbar.shape[1])
    Ybar=Ybar.reshape(Ybar.shape[0],1,Ybar.shape[1])

    X_Xbar=X-Xbar
    Y_Ybar=Y-Ybar
    Wx=np.einsum('ijk,ljk->ilk',X_Xbar,X_Xbar)
    Wy=np.einsum('ijk,ljk->ilk',Y_Ybar,Y_Ybar)
    W=(Wx+Wy)/float(nx+ny-2)
    Xbar_minus_Ybar=Xbar-Ybar
    x = np.linalg.solve(W.transpose(2,0,1), Xbar_minus_Ybar.transpose(2,0,1))
    x=x.transpose(1,2,0);

    t2=np.sum(Xbar_minus_Ybar*x,0)
    t2=t2*float(nx*ny)/float(nx+ny);
    stat=(t2*float(nx+ny-1-p)/(float(nx+ny-2)*p));

    pval=1-np.squeeze(f_distrib.cdf(stat,p,nx+ny-1-p));
    return pval,t2

def interpolate_labels(fromsurf=[], tosurf=[]):
    ''' interpolate labels from surface to to surface'''
    tree = cKDTree(fromsurf.vertices)
    d, inds = tree.query(tosurf.vertices, k=1, p=2)
    tosurf.labels = fromsurf.labels[inds]
    return tosurf


def reduce3_to_bci_lh(reduce3labs):

    class h32k:
        pass


    class h:
        pass


    class s:
        pass


    class bs:
        pass


    class bci:
        pass

    ''' reduce3 to h32k'''
    r3 = readdfs('lh.Yeo2011_17Networks_N1000_reduce3.dfs')
    r3.labels=np.squeeze(reduce3labs.T)

    '''h32k to full res FS'''
    g_surf = nib.load('/big_disk/ajoshi/HCP_data/reference/100307/MNINonLinea\
r/Native/100307.L.very_inflated.native.surf.gii')
    h.vertices = g_surf.darrays[0].data
    h.faces = g_surf.darrays[1].data
    h = interpolate_labels(r3, h)

    ''' native FS ref to native FS BCI'''
    g_surf = nib.load('/big_disk/ajoshi/HCP_data/reference/100307/MNINon\
Linear/Native/100307.L.sphere.reg.native.surf.gii')
    s.vertices = g_surf.darrays[0].data
    s.faces = g_surf.darrays[1].data
    s.labels = h.labels

    ''' map to bc sphere'''
    bs.vertices, bs.faces = fsio.read_geometry('/big_disk/ajoshi/data/BCI\
_DNI_Atlas/surf/lh.sphere.reg')
    bs = interpolate_labels(s, bs)
    bci.vertices, bci.faces = fsio.read_geometry('/big_disk/ajoshi/data/BCI_DNI_A\
tlas/surf/lh.white')
    bci.labels = bs.labels
 #   writedfs('BCI_orig_rh.dfs', bci)


    bci.vertices, bci.faces = fsio.read_geometry('/big_disk/ajoshi/data/BCI_DNI_A\
tlas/surf/lh.inflated')
#    view_patch(bci, bci.labels)

#    writedfs('BCI_pial_rh.dfs.', bci)

    bci.vertices, bci.faces = fsio.read_geometry('/big_disk/ajoshi/data/BCI_\
DNI_Atlas/surf/lh.white')
#    writedfs('BCI_white_rh.dfs.', bci)


    bci.vertices[:, 0] += 96*0.8
    bci.vertices[:, 1] += 192*0.546875
    bci.vertices[:, 2] += 192*0.546875
    bci_bst = readdfs('/big_disk/ajoshi/data/BCI-DNI_brain_atlas/BCI-DNI_\
brain.left.inner.cortex.dfs')
    bci_bst = interpolate_labels(bci, bci_bst)
    labs=bci_bst.labels
    return labs



def reduce3_to_bci_rh(reduce3labs):

    class h32k:
        pass


    class h:
        pass


    class s:
        pass


    class bs:
        pass


    class bci:
        pass

    ''' reduce3 to h32k'''
    r3 = readdfs('rh.Yeo2011_17Networks_N1000_reduce3.dfs')
    r3.labels=np.squeeze(reduce3labs.T)

    '''h32k to full res FS'''
    g_surf = nib.load('/big_disk/ajoshi/HCP_data/reference/100307/MNINonLinea\
r/Native/100307.R.very_inflated.native.surf.gii')
    h.vertices = g_surf.darrays[0].data
    h.faces = g_surf.darrays[1].data
    h = interpolate_labels(r3, h)

    ''' native FS ref to native FS BCI'''
    g_surf = nib.load('/big_disk/ajoshi/HCP_data/reference/100307/MNINon\
Linear/Native/100307.R.sphere.reg.native.surf.gii')
    s.vertices = g_surf.darrays[0].data
    s.faces = g_surf.darrays[1].data
    s.labels = h.labels

    ''' map to bc sphere'''
    bs.vertices, bs.faces = fsio.read_geometry('/big_disk/ajoshi/data/BCI\
_DNI_Atlas/surf/rh.sphere.reg')
    bs = interpolate_labels(s, bs)
    bci.vertices, bci.faces = fsio.read_geometry('/big_disk/ajoshi/data/BCI_DNI_A\
tlas/surf/rh.white')
    bci.labels = bs.labels
 #   writedfs('BCI_orig_rh.dfs', bci)


    bci.vertices, bci.faces = fsio.read_geometry('/big_disk/ajoshi/data/BCI_DNI_A\
tlas/surf/rh.inflated')
#    view_patch(bci, bci.labels)

#    writedfs('BCI_pial_rh.dfs.', bci)

    bci.vertices, bci.faces = fsio.read_geometry('/big_disk/ajoshi/data/BCI_\
DNI_Atlas/surf/rh.white')
#    writedfs('BCI_white_rh.dfs.', bci)


    bci.vertices[:, 0] += 96*0.8
    bci.vertices[:, 1] += 192*0.546875
    bci.vertices[:, 2] += 192*0.546875
    bci_bst = readdfs('/big_disk/ajoshi/data/BCI-DNI_brain_atlas/BCI-DNI_\
brain.right.inner.cortex.dfs')
    bci_bst = interpolate_labels(bci, bci_bst)
    labs=bci_bst.labels
    return labs

def FCDM(fdata, Tc=.8):
    """ Computes functional connectivity density mappingh"""
    rho = sp.corrcoef(fdata)
    fcdm = sp.sum(rho>Tc,axis=1)
    return fcdm

def ICC(fleft, fright, Tc=.5):
    """ Computes functional connectivity density mappingh"""
    xcorr = sp.dot(fleft, fright.T)
    lcorr = sp.dot(fleft, fleft.T)
    rcorr = sp.dot(fright, fright.T)
    icc_l = sp.sum(lcorr>Tc, axis=1)
    icc_r = sp.sum(rcorr>Tc, axis=1)
    icc_lr = sp.sum(xcorr>Tc, axis=1)
    icc_rl = sp.sum(xcorr.T>Tc, axis=1)
    icc_l = icc_l - icc_lr
    icc_r = icc_r - icc_rl
    return sp.append(icc_l,icc_r, axis=0)



def rot_sub_data(ref,sub, area_weight=[]):
    """ref and sub matrices are of the form (vertices x time) """
    if len(area_weight) == 0:
        xcorr=sp.dot(sub.T, ref)
    else:
        xcorr=sp.dot((area_weight*sub).T, area_weight*ref)
    u,s,v=sp.linalg.svd(xcorr)
    R=sp.dot(v.T,u.T)
#    print sp.linalg.det(R)
    return sp.dot(sub,R.T), R, xcorr

def normdata(data=0):
    indx = sp.isnan(data)
    data[indx] = 0
    m = np.mean(data, 1)
    data = data - m[:, None]
    s = np.std(data, 1)+1e-116
    data = data/s[:, None]
    return data


def show_slices(slices,vmax=None,vmin=None):
    """ Function to display row of image slices """
    fig, axes = plt.subplots(1, len(slices))
    for i, slice in enumerate(slices):
        a = axes[i].imshow(slice.T, cmap="gray", origin="lower",vmax=vmax,vmin=vmin)
    fig.colorbar(a)


def reorder_labels(labels):

    nClusters = sp.int32(sp.amax(labels.flatten()) + 1)
    labels0_vec = sp.zeros((labels.shape[0], nClusters), 'bool')
    labelsi_vec = labels0_vec.copy()
    for i in range(nClusters):
        labels0_vec[:, i] = (labels[:, 0] == i)

    for i in range(labels.shape[1]):
        for j in range(nClusters):
            labelsi_vec[:, j] = (labels[:, i] == j)
        D = pairwise_distances(labelsi_vec.T, labels0_vec.T, metric='dice')
        D[~sp.isfinite(D)] = 1
        ind1 = linear_assignment(D)
        labels[:, i] = ind1[sp.int16(labels[:, i]), 1]

    return labels


def region_growing_fmri(seeds, affinity, conn):
    lab = sp.zeros(affinity.shape[0])
    for ind in range(len(seeds)):
        lab[seeds[ind]] = ind + 1

    prevsum = sp.sum(lab == 0) + 1
    while prevsum - sp.sum(lab == 0) > 0:
        maxaff = -999
        prevsum = sp.sum(lab == 0)
        can_aff = [None]*len(seeds)  # empty list
        can_vert = [None]*len(seeds)
        for seedno in range(len(seeds)):
            all_vert = sp.sum(conn[lab == seedno+1, :] > 0, axis=0) > 0
            can_vert[seedno] = sp.where(all_vert & (lab == 0))
            cv = sp.array(can_vert[seedno]).squeeze()
            if cv.size == 0:
                continue
#            print len(cv), seeds[seedno]
            # affinity of candidate vertices to labeled vertices
            can_aff[seedno] = affinity[cv, seeds[seedno]]
            maxaff = sp.amax([maxaff, sp.amax(can_aff[seedno])])

        for seedno in range(len(seeds)):
            A = sp.array(can_vert[seedno]).squeeze()
            ind = lab[A] == 0
            A = A[ind]
            if len(A) == 0:
                continue
            if sp.sum(lab == 0) <= 1:
                frac = 1.0
            else:
                frac = 0.9
            B = can_aff[seedno] >= frac*maxaff
            B = B.squeeze()
            B = B[ind]
            lab[A[B]] = seedno + 1

    labels = lab - 1
    return labels

import numpy as np
from scipy.stats import f as f_distrib


def hotelling_t2(X, Y):
    """X and Y are n_features x n_subjects x n_voxels"""
    nx=X.shape[1];ny=Y.shape[1];p=X.shape[0];
    Xbar=X.mean(1);Ybar=Y.mean(1);
    Xbar=Xbar.reshape(Xbar.shape[0],1,Xbar.shape[1])
    Ybar=Ybar.reshape(Ybar.shape[0],1,Ybar.shape[1])

    X_Xbar=X-Xbar
    Y_Ybar=Y-Ybar
    Wx=np.einsum('ijk,ljk->ilk',X_Xbar,X_Xbar)
    Wy=np.einsum('ijk,ljk->ilk',Y_Ybar,Y_Ybar)
    W=(Wx+Wy)/float(nx+ny-2)
    Xbar_minus_Ybar=Xbar-Ybar
    x = np.linalg.solve(W.transpose(2,0,1), Xbar_minus_Ybar.transpose(2,0,1))
    x=x.transpose(1,2,0);

    t2=np.sum(Xbar_minus_Ybar*x,0)
    t2=t2*float(nx*ny)/float(nx+ny);
    stat=(t2*float(nx+ny-1-p)/(float(nx+ny-2)*p));

    pval=1-np.squeeze(f_distrib.cdf(stat,p,nx+ny-1-p));
    return pval,t2
