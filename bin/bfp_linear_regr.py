import os
import io
import numpy as np
import scipy.io as spio
import csv
from read_data_utils import load_bfp_data, read_demoCSV, write_text_timestamp,readConfig
from brainsync import IDrefsub_BrainSync, groupBrainSync, generate_avgAtlas
from stats_utils import dist2atlas, sync2atlas, multiLinReg_corr
from grayord_utils import vis_grayord_sigcorr
bfp_path = '/bfp'
fslpath = '/usr/share/fsl/5.0'


def bfp_linear_regr(specs, outputdir):
    log_fname = os.path.join(specs.resultdir, 'bfp_linregr_stat_log.txt')
    if not os.path.isdir(specs.resultdir):
        os.makedirs(specs.resultdir)
    write_text_timestamp(log_fname,
                         "All outputs will be written in: " + specs.resultdir)
    # read demographic csv file
    sub_ID, sub_fname, subAtlas_idx, reg_var, reg_cvar1, reg_cvar2 = read_demoCSV(
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
    print('Identifying subjects for atlas creation and hypothesis testing...')
    subTest_fname = []; subTest_IDs = []; subAtlas_fname = []; subAtlas_IDs = []
    for ind in range(len(sub_ID)):
        sub = sub_ID[ind]
        fname = sub_fname[ind]
        if int(subAtlas_idx[ind]) ==1:
            subAtlas_fname.append(fname)
            subAtlas_IDs.append(sub)
        else:
            subTest_fname.append(fname)
            subTest_IDs.append(sub)

    if specs.test_all == 'False':
        numT = len(subTest_IDs)
        write_text_timestamp(log_fname, "User Option: Only subjects not used for atlas creation will be used for hypothesis testing")
    else:
        numT = len(sub_ID)
        subTest_fname = sub_fname
        subTest_IDs = sub_ID
        write_text_timestamp(log_fname, "User Option: All subjects will be used for hypothesis testing")

    count1=-1
    subTest_varmain = np.zeros(numT); subTest_varc1 = np.zeros(numT); subTest_varc2 = np.zeros(numT)
    for ind in range(len(sub_ID)):
        varmain = reg_var[ind]
        varc1 = reg_cvar1[ind]
        varc2 = reg_cvar2[ind]
        if specs.test_all == 'False':
            if int(subAtlas_idx[ind]) !=1:
                count1 +=1
        else:
            count1 +=1
        subTest_varmain[count1] = varmain
        subTest_varc1[count1] = varc1
        subTest_varc2[count1] = varc2

    del sub_ID, sub_fname, subAtlas_idx, reg_var, reg_cvar1, reg_cvar2, count1, numT
    write_text_timestamp(log_fname, str(len(subAtlas_IDs)) + ' subjects will be used for atlas creation.')
    write_text_timestamp(log_fname, str(len(subTest_IDs)) + ' subjects will be used for hypothesis testing.')
    #%%
    # reads reference data and creates atlas by BrainSync algorithm
    if len(specs.atlas_fname) !=0:
        write_text_timestamp(log_fname, 'User Option: User defined atlas will be used ' + specs.atlas_fname)
        df = spio.loadmat(specs.atlas_fname)
        atlas_data = df['atlas_data']
        del df
    else:
        subAtlas_data, subAtlas_numT = load_bfp_data(subAtlas_fname, int(specs.lentime),specs.matcht)
        with open(specs.resultdirr + "/subjects_atlas.csv", 'w') as csvfile:
            csv.writer(csvfile).writerows(zip(subAtlas_IDs, subAtlas_numT))
            del subAtlas_numT
        if specs.atlas_groupsync == 'True':
            write_text_timestamp(log_fname, 'User Option: Group BrainSync algorithm will be used for atlas creation')
            atlas_data, _, _, _ = groupBrainSync(subAtlas_data)
            write_text_timestamp(log_fname, 'Done creating atlas')
        else:
            write_text_timestamp(log_fname, 'User Option: representative subject will be used for atlas creation')
            subRef_data, subRef_num = IDrefsub_BrainSync(subAtlas_data)
            write_text_timestamp(log_fname, 'Subject number ' + str(subAtlas_IDs[subRef_num]) + ' will be used for atlas creation')
            atlas_data = generate_avgAtlas(subRef_data, subAtlas_data)
        del subAtlas_data
        spio.savemat(os.path.join(specs.resultdir + '/atlas.mat'), {'atlas_data': atlas_data})
    #%%
    # load data
    subTest_data, numT = load_bfp_data(subTest_fname, int(specs.lentime),bool(specs.matcht))
    with open(specs.resultdir + "/subjects_testing.csv", 'w') as csvfile:
        csv.writer(csvfile).writerows(zip(subTest_IDs, numT,subTest_varmain, subTest_varc1, subTest_varc2))
    #%% sync and calculates geodesic distances
    subTest_syndata = sync2atlas(atlas_data, subTest_data)
    subTest_diff,_ = dist2atlas(atlas_data, subTest_syndata)
    spio.savemat(os.path.join(specs.resultdir + '/dist2atlas.mat'), {'subTest_diff': subTest_diff})
    del subTest_data, subTest_syndata
    #%% computes correlation after controlling for two covariates
    rval, pval, pval_fdr, msg = multiLinReg_corr(subTest_diff, subTest_varmain, subTest_varc1, subTest_varc2, float(specs.sig_alpha), 'linear')
    spio.savemat(os.path.join(specs + '/' + specs.outname + '_rval.mat'), {'rval': rval})
    spio.savemat(os.path.join(specs + '/' + specs.outname + '_pval.mat'), {'pval': pval})
    spio.savemat(os.path.join(specs.resultdir + '/' + specs.outname + '_pval_fdr.mat'), {'pval_fdr': pval_fdr})
    write_text_timestamp(log_fname, 'Done runnning linear regression. ' + msg)
    #%%
    vis_grayord_sigcorr(pval, rval, float(specs.sig_alpha), specs.outname, specs.resultdir, int(specs.smooth_iter), specs.save_figures, bfp_path, fslpath)
    vis_grayord_sigcorr(pval_fdr, rval, float(specs.sig_alpha), specs.outname + '_fdr', specs.resultdir, int(specs.smooth_iter), bool(specs.save_figures), bfp_path, fslpath)
    write_text_timestamp(log_fname, 'BFP regression analysis complete')
