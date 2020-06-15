"""
workspace for tools used for developing
not to be published
"""

import csv
import os
import scipy as sp
import numpy as np
import scipy.io as spio
from tqdm import tqdm
import itertools
import statsmodels.api as sm
from statsmodels.stats.multitest import fdrcorrection
from sklearn.decomposition import PCA
from surfproc import view_patch_vtk, patch_color_attrib, smooth_surf_function, smooth_patch
from dfsio import readdfs, writedfs
import sys
sys.path.append('../BrainSync')
import multiprocessing
from functools import partial
from brainsync import normalizeData, brainSync



def pair_dist(rand_pair, sub_files, reg_var, len_time=235):
    """ Pair distance """
    sub1_data = spio.loadmat(sub_files[rand_pair[0]])['dtseries'].T
    sub2_data = spio.loadmat(sub_files[rand_pair[1]])['dtseries'].T

    sub1_data, _, _ = normalizeData(sub1_data[:len_time, :])
    sub2_data, _, _ = normalizeData(sub2_data[:len_time, :])

    sub2_data, _ = brainSync(X=sub1_data, Y=sub2_data)
    fmri_diff = sp.sum((sub2_data - sub1_data)**2, axis=0)
    regvar_diff = sp.square(reg_var[rand_pair[0]] - reg_var[rand_pair[1]])

    return fmri_diff, regvar_diff


def randpairsdist_reg_parallel(bfp_path,
                               sub_files,
                               reg_var,
                               num_pairs=2000,
                               nperm=1000,
                               len_time=235,
                               num_proc=4,
                               fdr_test=False):
    """ Perform regression stats based on square distance between random pairs """

    # Get the number of vertices from a file
    num_vert = spio.loadmat(sub_files[0])['dtseries'].shape[0]

    # Generate pairs
    pairs = list(itertools.combinations(range(len(sub_files)), r=2))

    if num_pairs > 0:
        rn = np.random.permutation(len(pairs))
        pairs = [pairs[i] for i in rn]
        if num_pairs < len(pairs):
            pairs = pairs[:num_pairs]
        else:
            num_pairs = len(pairs)

    fmri_diff = sp.zeros((num_vert, num_pairs))
    regvar_diff = sp.zeros(num_pairs)

    results = multiprocessing.Pool(num_proc).imap(
        partial(
            pair_dist, sub_files=sub_files, reg_var=reg_var,
            len_time=len_time), pairs)

    ind = 0
    for res in results:
        fmri_diff[:, ind] = res[0]
        regvar_diff[ind] = res[1]
        ind += 1

    if not fdr_test:
        print('Performing Permutation test with MAX statistic')
        corr_pval = corr_perm_test(X=fmri_diff.T, Y=regvar_diff, nperm=nperm)
    else:
        print('Performing Pearson correlation with FDR testing')
        corr_pval = corr_pearson_fdr(X=fmri_diff.T, Y=regvar_diff, nperm=nperm)

    corr_pval[sp.isnan(corr_pval)] = .5

    labs = spio.loadmat(
        bfp_path +
        '/supp_data/USCBrain_grayordinate_labels.mat')['labels'].squeeze()
    labs[sp.isnan(labs)] = 0

    corr_pval[labs == 0] = 0.5

    return corr_pval


'''Deprecated'''


def randpairsdist_reg(bfp_path,
                      sub_files,
                      reg_var,
                      num_pairs=1000,
                      len_time=235):
    """ Perform regression stats based on square distance between random pairs """
    print('dist2atlas_reg, assume that the data is normalized')
    print('This function is deprecated!!!!!!!!!!')

    # Get the number of vertices from a file
    num_vert = spio.loadmat(sub_files[0])['dtseries'].shape[0]

    #Generate random pairs
    rand_pairs = sp.random.choice(len(sub_files), (num_pairs, 2), replace=True)

    fmri_diff = sp.zeros((num_vert, num_pairs))
    regvar_diff = sp.zeros(num_pairs)

    print('Reading subjects')

    # Compute distance to atlas
    for ind in tqdm(range(num_pairs)):
        sub1_data = spio.loadmat(sub_files[rand_pairs[ind, 0]])['dtseries'].T
        sub2_data = spio.loadmat(sub_files[rand_pairs[ind, 1]])['dtseries'].T

        sub1_data, _, _ = normalizeData(sub1_data[:len_time, :])
        sub2_data, _, _ = normalizeData(sub2_data[:len_time, :])

        sub2_data, _ = brainSync(X=sub1_data, Y=sub2_data)
        fmri_diff[:, ind] = sp.sum((sub2_data - sub1_data)**2, axis=0)
        regvar_diff[ind] = sp.square(reg_var[rand_pairs[ind, 0]] -
                                     reg_var[rand_pairs[ind, 1]])

    corr_pval = sp.zeros(num_vert)
    for ind in tqdm(range(num_vert)):
        _, corr_pval[ind] = sp.stats.pearsonr(fmri_diff[ind, :], regvar_diff)

    corr_pval[sp.isnan(corr_pval)] = .5

    labs = spio.loadmat(bfp_path + '/supp_data/USCBrain_grayord_labels.mat'
                        )['labels'].squeeze()

    corr_pval_fdr = sp.zeros(num_vert)
    _, corr_pval_fdr[labs > 0] = fdrcorrection(corr_pval[labs > 0])

    return corr_pval, corr_pval_fdr


def pairsdist_regression(bfp_path,
                         sub_files,
                         reg_var,
                         num_perm=1000,
                         num_pairs=0,
                         len_time=235):
    """ Perform regression stats based on square distance between random pairs """

    # Get the number of vertices from a file
    num_vert = spio.loadmat(sub_files[0])['dtseries'].shape[0]
    num_sub = len(sub_files)

    # Allocate memory for subject data
    sub_data = np.zeros(shape=(len_time, num_vert, num_sub))

    #Generate random pairs
    print('Reading subjects')
    for subno, filename in enumerate(tqdm(sub_files)):
        data = spio.loadmat(filename)['dtseries'].T
        sub_data[:, :, subno], _, _ = normalizeData(data[:len_time, :])

    pairs = list(itertools.combinations(range(num_sub), r=2))

    if num_pairs > 0:
        rn = np.random.permutation(len(pairs))
        pairs = [pairs[i] for i in rn]
        pairs = pairs[:num_pairs]

    fmri_diff = sp.zeros((num_vert, len(pairs)))
    regvar_diff = sp.zeros(len(pairs))

    print('Computing pairwise differences')
    for pn, pair in enumerate(tqdm(pairs)):
        Y2, _ = brainSync(X=sub_data[:, :, pair[0]], Y=sub_data[:, :, pair[1]])
        fmri_diff[:, pn] = np.sum((Y2 - sub_data[:, :, pair[0]])**2, axis=0)
        regvar_diff[pn] = (reg_var[pair[0]] - reg_var[pair[1]])**2

    corr_pval = corr_perm_test(X=fmri_diff.T, Y=regvar_diff)

    #    corr_pval = sp.zeros(num_vert)
    #    for ind in tqdm(range(num_vert)):
    #        _, corr_pval[ind] = sp.stats.pearsonr(fmri_diff[ind, :], regvar_diff)
    #    corr_pval[sp.isnan(corr_pval)] = .5
    #

    labs = spio.loadmat(
        bfp_path +
        '/supp_data/USCBrain_grayordinate_labels.mat')['labels'].squeeze()
    labs[sp.isnan(labs)] = 0

    corr_pval[labs == 0] = 0.5

    corr_pval_fdr = 0.5 * sp.ones(num_vert)
    _, corr_pval_fdr[labs > 0] = fdrcorrection(corr_pval[labs > 0])

    return corr_pval, corr_pval_fdr


def dist2atlas_reg(bfp_path, ref_atlas, sub_files, reg_var, len_time=235):
    """ Perform regression stats based on square distance to atlas """
    print('dist2atlas_reg, assume that the data is normalized')

    num_vert = ref_atlas.shape[1]
    num_sub = len(sub_files)

    # Take absolute value of difference from the mean
    # for the IQ measure
    reg_var = sp.absolute(reg_var - sp.mean(reg_var))

    diff = sp.zeros((num_vert, num_sub))

    # Compute distance to atlas
    for ind in tqdm(range(num_sub)):
        sub_data = spio.loadmat(sub_files[ind])['dtseries'].T
        sub_data, _, _ = normalizeData(sub_data[:len_time, :])
        Y2, _ = brainSync(X=ref_atlas, Y=sub_data)
        diff[:, ind] = sp.sum((Y2 - ref_atlas)**2, axis=0)

    corr_pval = sp.zeros(num_vert)
    for vrt in tqdm(range(num_vert)):
        _, corr_pval[vrt] = sp.stats.pearsonr(diff[vrt, :], reg_var)

    corr_pval[sp.isnan(corr_pval)] = .5

    lab = spio.loadmat(bfp_path + '/supp_data/USCBrain_grayord_labels.mat')
    labs = lab['labels'].squeeze()

    corr_pval_fdr = sp.zeros(num_vert)
    _, pv = fdrcorrection(corr_pval[labs > 0])
    corr_pval_fdr[labs > 0] = pv

    return corr_pval, corr_pval_fdr


def lin_reg(bfp_path,
            ref_atlas,
            sub_files,
            reg_var,
            Vndim=235,
            Sndim=20,
            len_time=235):
    """ Perform regression stats based on distance to atlas """

    num_vert = ref_atlas.shape[1]
    num_sub = len(sub_files)
    a = spio.loadmat(bfp_path + '/supp_data/USCBrain_grayord_labels.mat')
    labs = a['labels'].squeeze()

    labs[sp.isnan(labs)] = 0
    print('Computing PCA basis function from the atlas')
    pca = PCA(n_components=Vndim)
    pca.fit(ref_atlas.T)

    reduced_data = sp.zeros((Vndim, num_vert, num_sub))
    for ind in tqdm(range(num_sub)):

        sub_data = spio.loadmat(sub_files[ind])['dtseries'].T
        sub_data, _, _ = normalizeData(sub_data[:len_time, :])
        Y2, _ = brainSync(X=ref_atlas, Y=sub_data)

        if Vndim == len_time:
            reduced_data[:, :, ind] = sub_data
        else:
            reduced_data[:, :, ind] = pca.transform(Y2.T).T

    pval_linreg = sp.zeros(num_vert)

    pca = PCA(n_components=Sndim)

    for vrt in tqdm(range(num_vert)):
        X = reduced_data[:, vrt, :]
        if Sndim != num_sub:
            pca.fit(X.T)
            X = pca.transform(X.T).T
        X = sm.add_constant(X.T)
        est = sm.OLS(reg_var, X)
        pval_linreg[vrt] = est.fit().f_pvalue

    print('Regression is done')

    pval_linreg[sp.isnan(pval_linreg)] = .5

    pval_linreg_fdr = sp.zeros(num_vert)
    _, pv = fdrcorrection(pval_linreg[labs > 0])
    pval_linreg_fdr[labs > 0] = pv

    return pval_linreg, pval_linreg_fdr


def read_fcon1000_data(csv_fname,
                       data_dir,
                       reg_var_name='Verbal IQ',
                       num_sub=5,
                       reg_var_positive=1):
    """ reads fcon1000 csv and data"""

    count1 = 0
    sub_ids = []
    reg_var = []
    pbar = tqdm(total=num_sub)

    with open(csv_fname, newline='') as csvfile:
        creader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        for row in creader:

            # read the regression variable
            rvar = row[reg_var_name]

            # Read the filtered data by default
            fname = os.path.join(
                data_dir, row['ScanDir ID'] + '_rest_bold.32k.GOrd.filt.mat')

            # If the data does not exist for this subject then skip it
            if not os.path.isfile(fname) or int(row['QC_Rest_1']) != 1:
                continue

            if reg_var_positive == 1 and sp.float64(rvar) < 0:
                continue

            if count1 == 0:
                sub_data_files = []

            # Truncate the data at a given number of time samples This is needed because
            # BrainSync needs same number of time sampples
            sub_data_files.append(fname)
            sub_ids.append(row['ScanDir ID'])
            reg_var.append(float(rvar))

            count1 += 1
            pbar.update(1)  # update the progress bar
            #print('%d,' % count1, end='')
            if count1 == num_sub:
                break

    pbar.close()
    print('CSV file and the data has been read\nThere are %d subjects' %
          (len(sub_ids)))

    return sub_ids, sp.array(reg_var), sub_data_files