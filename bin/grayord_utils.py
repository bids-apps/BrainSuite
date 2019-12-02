""" This module contains helful utility functions for handling and visualizing gray ordinate file """
import os
import scipy as sp
import numpy as np
import scipy.io as spio
import sys
sys.path.append('src/stats')
from surfproc import  patch_color_attrib
from dfsio import readdfs, writedfs
from os.path import join
from nilearn.image import load_img, new_img_like
from scipy.io import loadmat

FSL_PATH = '/usr/share/fsl/5.0'


def visdata_grayord(data,
                    surf_name,
                    out_dir,
                    smooth_iter,
                    colorbar_lim,
                    colormap,
                    save_dfs,
                    save_png,
                    bfp_path='.',
                    fsl_path=FSL_PATH):
    lsurf, rsurf = label_surf(
        data, colorbar_lim, smooth_iter, colormap, bfp_path=bfp_path)
    save2surfgord(lsurf, rsurf, out_dir, surf_name, bfp_path, save_dfs,
                  save_png)
    save2volgord(data, out_dir, surf_name, bfp_path)


def vis_grayord_sigcorr(pval, rval, surf_name, out_dir, smooth_iter, save_dfs,
                        save_png, save_vol, bfp_path, fsl_path):

    if save_vol:
        save2volgord(pval, out_dir, surf_name + '_pval', bfp_path, fsl_path)
        save2volgord(rval, out_dir, surf_name + '_rval', bfp_path, fsl_path)

    if save_dfs:
        print('outputs will be written to directory: ' + out_dir)
        plsurf, prsurf = label_surf(pval, [0, 0.05], smooth_iter, 'jet_r', bfp_path)
        # If p value above .05 then make the surface grey
        plsurf.vColor[plsurf.attributes > 0.05, :] = .5
        prsurf.vColor[prsurf.attributes > 0.05, :] = .5
        save2surfgord(plsurf, prsurf, out_dir, surf_name + '_pval_sig', bfp_path,
                      bool(save_dfs), bool(save_png))
        print('output pvalues on surface')
        print('colorbar limits are 0 to 0.05; colorbar class is jet reverse')

        lsurf, rsurf = label_surf(rval, [-.5, .5], smooth_iter, 'jet', bfp_path)
        # If p value above .05 then make the surface grey
        lsurf.vColor[plsurf.attributes > 0.05, :] = .5
        rsurf.vColor[prsurf.attributes > 0.05, :] = .5
        save2surfgord(lsurf, rsurf, out_dir, surf_name + '_rval_sig', bfp_path,
                      bool(save_dfs), bool(save_png))
        print('output pvalues on surface')
        print('colorbar limits are -0.5 to +0.5; colorbar class is jet')


def vis_grayord_sigpval(pval,
                        surf_name,
                        out_dir,
                        smooth_iter,
                        bfp_path,
                        fsl_path=FSL_PATH,
                        save_vol=True,
                        save_png=True):
    if save_vol == True:
        save2volgord(
            pval,
            out_dir,
            surf_name + '_pval_sig',
            bfp_path,
            fsl_path=fsl_path)

    plsurf, prsurf = label_surf(
        pval, [0, 0.05], smooth_iter, 'jet_r', bfp_path=bfp_path)
    # If p value above .05 then make the surface grey
    plsurf.vColor[plsurf.attributes >= 0.05, :] = .5
    prsurf.vColor[prsurf.attributes >= 0.05, :] = .5
    save2surfgord(
        plsurf,
        prsurf,
        out_dir,
        surf_name + 'pval_sig',
        bfp_path=bfp_path,
        save_png=save_png)


def label_surf(pval, colorbar_lim, smooth_iter, colormap, bfp_path='.'):
    lsurf = readdfs(os.path.join(bfp_path, 'supp_data/bci32kleft.dfs'))
    rsurf = readdfs(os.path.join(bfp_path, 'supp_data/bci32kright.dfs'))
    num_vert = lsurf.vertices.shape[0]
    lsurf.attributes = sp.zeros((lsurf.vertices.shape[0]))
    rsurf.attributes = sp.zeros((rsurf.vertices.shape[0]))
    #smooth surfaces
    # lsurf = smooth_patch(lsurf, iterations=smooth_iter)

    # rsurf = smooth_patch(rsurf, iterations=smooth_iter)

    # write on surface attributes
    lsurf.attributes = pval.squeeze()
    lsurf.attributes = lsurf.attributes[:num_vert]
    rsurf.attributes = pval.squeeze()
    rsurf.attributes = rsurf.attributes[num_vert:2 * num_vert]

    lsurf = patch_color_attrib(lsurf, clim=colorbar_lim, cmap=colormap)
    rsurf = patch_color_attrib(rsurf, clim=colorbar_lim, cmap=colormap)

    return lsurf, rsurf


def save2volgord(data, out_dir, vol_name, bfp_path='.', fsl_path=FSL_PATH):

    mni2mm = load_img(join(fsl_path, 'data/standard', 'MNI152_T1_2mm.nii.gz'))
    a = loadmat(join(bfp_path, 'supp_data', 'MNI2mm_gord_vol_coord.mat'))

    ind = ~np.isnan(a['voxc']).any(axis=1)
    voxc = np.int16(
        a['voxc'] - 1)  # subtract 1 to convert from MATLAB to Python indexing
    gordvol = np.ones(mni2mm.shape)

    gordvol[voxc[ind, 0], voxc[ind, 1], voxc[ind, 2]] = data[ind]
    grod = new_img_like(mni2mm, gordvol)
    grod.set_data_dtype(np.float64)
    outfile = join(out_dir, vol_name + '_MNI2mm.nii.gz')
    grod.to_filename(outfile)


def save2surfgord(lsurf,
                  rsurf,
                  out_dir,
                  surf_name,
                  bfp_path='.',
                  save_dfs=True,
                  save_png=True):
    # if label is zero, black out surface, attribute should be nan
    num_vert = lsurf.vertices.shape[0]
    lab = spio.loadmat(
        os.path.join(bfp_path, 'supp_data/USCBrain_grayordinate_labels.mat'))
    labs = lab['labels'].squeeze()
    labs = sp.float64(labs)
    lsurf.attributes[np.isnan(labs[:num_vert])] = 0
    lsurf.attributes[labs[:num_vert] == 0] = sp.nan
    rsurf.attributes[labs[num_vert:2 * num_vert] == 0] = sp.nan
    lsurf.vColor[sp.isnan(lsurf.attributes), :] = 0
    rsurf.vColor[sp.isnan(lsurf.attributes), :] = 0

    # if save_png == True:
    #     # Visualize left hemisphere
    #     view_patch_vtk(
    #         lsurf,
    #         azimuth=100,
    #         elevation=180,
    #         roll=90,
    #         outfile=out_dir + '/LeftLateral_' + surf_name + '.png',
    #         show=0)
    #     view_patch_vtk(
    #         lsurf,
    #         azimuth=-100,
    #         elevation=180,
    #         roll=-90,
    #         outfile=out_dir + '/LeftMedial_' + surf_name + '.png',
    #         show=0)
    #     # Visualize right hemisphere
    #     view_patch_vtk(
    #         rsurf,
    #         azimuth=-100,
    #         elevation=180,
    #         roll=-90,
    #         outfile=out_dir + '/RightLateral_' + surf_name + '.png',
    #         show=0)
    #     view_patch_vtk(
    #         rsurf,
    #         azimuth=100,
    #         elevation=180,
    #         roll=90,
    #         outfile=out_dir + '/RightMedial_' + surf_name + '.png',
    #         show=0)
    if save_dfs == True:
        writedfs(out_dir + '/Right_' + surf_name + '.dfs', rsurf)
        writedfs(out_dir + '/Left_' + surf_name + '.dfs', lsurf)
