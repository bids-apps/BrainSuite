import os, io
import scipy.io as spio
import scipy as sp
import numpy as np
from sklearn.linear_model import LinearRegression
from read_data_utils import load_bfp_data, read_demoCSV, write_text_timestamp, readConfig
from stats_utils import randpairs_regression, multiLinReg_resid, LinReg_resid, multiLinReg_corr
from grayord_utils import vis_grayord_sigcorr, vis_grayord_sigpval
#%%
bfp_path = '/bfp'
fslpath = '/usr/share/fsl/5.0'

def bfp_linear_regr_pairwise(specs, outputdir):
    log_fname = os.path.join(specs.resultdir, 'bfp_linregr_pairwise_stat_log.txt')
    # write_text_timestamp(log_fname, 'Config file used: ' + config_file)
    if not os.path.isdir(specs.resultdir):
        os.makedirs(specs.resultdir)
    write_text_timestamp(log_fname,
                         "All outputs will be written in: " + specs.resultdir)
    # read demographic csv file
    sub_ID, sub_fname, _, reg_var, reg_cvar1, reg_cvar2 = read_demoCSV(
        specs.tsv,
        outputdir,
        specs.fileext,
        'participant_id',
        specs.exclude,
        specs.atlas,
        specs.main,
        specs.reg1, 
        specs.reg2)
    #%% makes file list for subjects
    print(
        'Identifying subjects for hypothesis testing, no atlas needs to be created...'
    )
    subTest_fname = []
    subTest_IDs = []
    for ind in range(len(sub_ID)):
        sub = sub_ID[ind]
        fname = sub_fname[ind]
        subTest_fname.append(fname)
        subTest_IDs.append(sub)
    
    if specs.test_all == 'False':
        numT = len(subTest_IDs)
        write_text_timestamp(
            log_fname,
            "User Option: Only subjects not used for atlas creation will be used for hypothesis testing"
        )
    else:
        numT = len(sub_ID)
        subTest_fname = sub_fname
        subTest_IDs = sub_ID
        write_text_timestamp(
            log_fname,
            "User Option: All subjects will be used for hypothesis testing")
    
    count1 = -1
    subTest_varmain = sp.zeros(numT)
    subTest_varc1 = sp.zeros(numT)
    subTest_varc2 = sp.zeros(numT)
    for ind in range(len(sub_ID)):
        varmain = reg_var[ind]
        varc1 = reg_cvar1[ind]
        varc2 = reg_cvar2[ind]
        count1 += 1
        subTest_varmain[count1] = varmain
        subTest_varc1[count1] = varc1
        subTest_varc2[count1] = varc2
    
    del sub_ID, sub_fname, reg_var, reg_cvar1, reg_cvar2,count1, numT
    
    import csv
    with open(specs.resultdir + "/subjects_testing.csv", 'w') as csvfile:
        csv.writer(csvfile).writerows(
            zip(subTest_IDs, subTest_varmain, subTest_varc1, subTest_varc2))
    write_text_timestamp(
        log_fname,
        ' There is no atlas needed for pairwise tests, all the subjects will be used for hypothesis testing.'
    )
    write_text_timestamp(
        log_fname,
        str(len(subTest_IDs)) + ' subjects will be used for hypothesis testing.')
    #%% Do Linear regression on the covariates
    write_text_timestamp(
        log_fname,
        'Doing linear regression on the covariates from the main variable.')
    
    subTest_varc12 = sp.zeros((subTest_varc1.shape[0], 2))
    subTest_varc12[:, 0] = subTest_varc1
    subTest_varc12[:, 1] = subTest_varc2
    regr = LinearRegression()
    regr.fit(subTest_varc12, subTest_varmain)
    pre = regr.predict(subTest_varc12)
    subTest_varmain2 = subTest_varmain - pre
    
    #%% Compute pairwise distance and perform regression
    corr_pval_max, corr_pval_fdr = randpairs_regression(
        bfp_path=bfp_path,
        sub_files=subTest_fname,
        reg_var=subTest_varmain2,
        num_pairs=2000,  # 19900,
        nperm=2000,
        len_time=int(specs.lentime),
        num_proc=1,
        pearson_fdr_test=False)
    #%%
    spio.savemat(os.path.join(specs.resultdir + '/' + specs.outname + '_corr_pval_max.mat'), {'corr_pval_max': corr_pval_max})
    spio.savemat(os.path.join(specs.resultdir + '/' + specs.outname + '_corr_pval_fdr.mat'), {'corr_pval_fdr': corr_pval_fdr})
    #%% Visualization of the results
    vis_grayord_sigpval(corr_pval_max, float(specs.sig_alpha),
                        surf_name=specs.outname + '_max',
                        out_dir=specs.resultdir,
                        smooth_iter=int(specs.smooth_iter),
                        bfp_path=bfp_path,
                        fsl_path=fslpath)
    
    vis_grayord_sigpval(corr_pval_fdr, float(specs.sig_alpha),
                        surf_name=specs.outname + 'fdr',
                        out_dir=specs.resultdir,
                        smooth_iter=int(specs.smooth_iter),
                        bfp_path=bfp_path,
                        fsl_path=fslpath)
    
    write_text_timestamp(log_fname, 'BFP regression analysis complete')