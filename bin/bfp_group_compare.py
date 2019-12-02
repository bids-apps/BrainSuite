#%%
# config_file = '/NCAdisk/SCD_structural_analysis/BOLD_study/BOLD_Analysis/032519/rest/group_config_stats.ini'
#%%#%%
### Import the required librariesimport configparser
import sys
import os
import scipy.io as spio
import scipy as sp
import numpy as np
# import configparser
#
# ### get BFP directory from config file
# config = configparser.ConfigParser()
# config.read(config_file)
# section = config.sections()
# bfp_path = config.get('inputs','bfp_path')
# sys.path.append(os.path.join(bfp_path, 'src/stats/') )

bfp_path = '/bfp'
fslpath = '/usr/share/fsl/5.0'


from read_data_utils import load_bfp_data, read_demoCSV, write_text_timestamp, readConfig, read_demoCSV_list
# os.chdir(bfp_path)
# cf = readConfig(config_file)

### Import BrainSync libraries
# sys.path.append(os.path.join(str(bfp_path), 'src/BrainSync/'))
from brainsync import IDrefsub_BrainSync, groupBrainSync, generate_avgAtlas
from stats_utils import dist2atlas, sync2atlas, multiLinReg_corr
from grayord_utils import vis_grayord_sigcorr

#%% 
# log_fname = os.path.join(specs.resultdir, 'bfp_group_stat_log.txt')
# write_text_timestamp(log_fname, 'Config file used: ' + config_file)
# if not os.path.isdir(specs.resultdir):
#     os.makedirs(specs.resultdir)
# write_text_timestamp(log_fname, "All outputs will be written in: " + specs.resultdir )
# # read demographic csv file
# sub_ID, sub_fname, subAtlas_idx, reg_var, reg_cvar1, reg_cvar2 = read_demoCSV(cf.csv_fname,
#                 cf.data_dir,
#                 cf.file_ext,
#                 cf.colsubj,
#                 cf.colvar_exclude,
#                 cf.colvar_group,
#                 cf.colvar_main,
#                 cf.colvar_reg1,
#                 cf.colvar_reg2)
#%%

def bfp_group_compare(specs, outputdir):
    log_fname = os.path.join(specs.resultdir, 'bfp_groupcomp_stat_log.txt')
    write_text_timestamp(log_fname, "All outputs will be written in: " + specs.resultdir)
    sub_ID, sub_fname, subAtlas_idx, reg_var, reg_cvar1, reg_cvar2 = read_demoCSV(specs.tsv,
                outputdir,
                specs.fileext,
                'participant_id',
                specs.exclude,
                specs.atlas,
                specs.main,
                specs.reg1,
                specs.reg2)

    data = read_demoCSV_list(specs.tsv)
    # sub_ID = data['participant_id']
    # reg_var = np.array(specs.main).astype(np.float)
    # var_group = data[specs.controls]

    print('Identifying subjects for atlas creation and hypothesis testing...')
    subTest_fname = []
    subTest_IDs = []
    subAtlas_fname = []
    subAtlas_IDs = []
    for ind in range(len(sub_ID)):
        sub = sub_ID[ind]
        fname = sub_fname[ind]
        if int(subAtlas_idx[ind]) == 1:
            subAtlas_fname.append(fname)
            subAtlas_IDs.append(sub)
        else:
            subTest_fname.append(fname)
            subTest_IDs.append(sub)

    if specs.test_all == 'False':
        numT = len(subTest_IDs)
        write_text_timestamp(log_fname,
                             "User Option: Only subjects not used for atlas creation will be used for hypothesis testing")
    else:
        numT = len(sub_ID)
        subTest_fname = sub_fname
        subTest_IDs = sub_ID
        write_text_timestamp(log_fname, "User Option: All subjects will be used for hypothesis testing")

    #%% makes file list for subjects
    print('Identifying subjects for each group testing...')
    count1=0
    subTest_varmain = sp.zeros(len(subTest_IDs)); subTest_varc1 = sp.zeros(len(subTest_IDs)); subTest_varc2 = sp.zeros(len(subTest_IDs))
    for ind in range(len(sub_ID)):
        varmain = reg_var[ind]
        varc1 = reg_cvar1[ind]
        varc2 = reg_cvar2[ind]
        if int(subAtlas_idx[ind]) !=1:
            subTest_varmain[count1] = varmain
            subTest_varc1[count1] = varc1
            subTest_varc2[count1] = varc2
            count1 +=1

    np.savetxt(specs.resultdir + "/subjects_testing.csv", subTest_IDs, delimiter=",", fmt='%s')
    write_text_timestamp(log_fname, str(len(subTest_IDs)) + ' subjects will be used for hypothesis testing.')
    #%%
    # reads reference data and creates atlas by BrainSync algorithm
    subAtlas_data = load_bfp_data(subAtlas_fname, int(int(specs.lentime)))

    if specs.atlas_groupsync == 'True':
        write_text_timestamp(log_fname, 'User Option: Group BrainSync algorithm will be used for atlas creation')
        atlas_data, _, _, _ = groupBrainSync(subAtlas_data)
        write_text_timestamp(log_fname, 'Done creating atlas')
    else:
        write_text_timestamp(log_fname, 'User Option: representative subject will be used for atlas creation')
        subRef_data, subRef_num = IDrefsub_BrainSync(subAtlas_data)
        write_text_timestamp(log_fname, 'Subject number ' + str(subRef_num) + ' will be used for atlas creation')
        atlas_data = generate_avgAtlas(subRef_data, subAtlas_data)

    spio.savemat(os.path.join(specs.resultdir + '/atlas.mat'), {'atlas_data': atlas_data})
    del subAtlas_data
    #%% sync and calculates geodesic distances
    subTest_data = load_bfp_data(subTest_fname, int(int(specs.lentime)))
    subTest_syndata = sync2atlas(atlas_data, subTest_data)
    subTest_diff = dist2atlas(atlas_data, subTest_syndata)
    spio.savemat(os.path.join(specs.resultdir + '/dist2atlas.mat'), {'subTest_diff': subTest_diff})
    del subTest_data, subTest_syndata
    #%% computes correlation after controlling for two covariates
    rval, pval, pval_fdr, msg = multiLinReg_corr(subTest_diff, subTest_varmain, subTest_varc1, subTest_varc2,bfp_path )
    #%%
    vis_grayord_sigcorr(pval, rval, specs.outname, specs.resultdir, int(specs.smooth_iter), specs.save_surfaces,bool('False'), 'True',bfp_path, fslpath)
    vis_grayord_sigcorr(pval, rval, specs.outname + '_fdr', specs.resultdir, int(specs.smooth_iter), specs.save_surfaces, bool('False'), 'False',bfp_path, fslpath)
    write_text_timestamp(log_fname, 'BFP regression analysis complete')