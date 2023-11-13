from __future__ import division

import os
import shutil
import warnings
import datetime
warnings.filterwarnings("ignore")
import numpy as np
import nibabel as nib
import matplotlib
import matplotlib.style
matplotlib.use('Agg')   # generate pdf output by default
matplotlib.interactive(False)
matplotlib.style.use('classic')
from matplotlib.backends.backend_pdf import PdfPages
from eddy_qc.QUAD import (quad_msr, quad_tables, quad_mot, quad_s2v_mot, quad_eddy,
                            quad_ol_mat, quad_cnr_maps, quad_avg_maps, quad_susc, quad_json)
from eddy_qc.utils import (fslpy, utils, ref_page)
import json


#=========================================================================================
# FSL QUAD (QUality Assessment for DMRI)
# Matteo Bastiani
# 01-06-2017, FMRIB, Oxford
#=========================================================================================
def main(eddyBase, eddyIdx, eddyParams, mask, bvalsFile, bvecsFile, oDir, field, slspecFile, jsonFile, verbose):
    """
    Generate a QC report pdf for single subject dMRI data.
    The script will look for EDDY output files that are generated according to the user
    specified options. If a feature (e.g., output the CNR maps) has not been used, then
    no page in the final report based on it will be produced.
    The script also produces a qc.json file that contains summery qc indices and basic
    information about the data.
    The JSON file can then be read by SQUAD to generate a group report. If the update flag
    is true, the single subject pdf will be updated with the whole group context.

    Compulsory arguments:
       eddyBase             Basename (including path) specified when running EDDY
       -idx, --eddyIdx      File containing indices for all volumes into acquisition parameters
       -par, --eddyParams   File containing acquisition parameters
       -m, --mask           Binary mask file
       -b, --bvals          b-values file

    Optional arguments:
       -g, --bvecs          b-vectors file - only used when <eddyBase>.eddy_residuals file is present
       -o, --output-dir     Output directory - default = '<eddyBase>.qc'
       -f, --field          TOPUP estimated field (in Hz)
       -s, --slspec         Text file specifying slice/group acquisition
       -j, --json           JSON file specifying acquisition parameters (alternative for --slspec)
       -v, --verbose        Display debug messages

    Output:
       output-dir/qc.pdf: single subject QC report
       output-dir/qc.json: single subject QC and data info database
       output-dir/vols_no_outliers.txt: text file that contains the list of the non-outlier volumes (based on eddy residuals)
    """
    # EDDY BASENAME
    if os.path.isfile(eddyBase + '.nii.gz'):
        eddyFile = eddyBase + '.nii.gz'
    elif os.path.isfile(eddyBase + '.nii'):
        eddyFile = eddyBase + '.nii'
    else:
        raise ValueError(eddyBase + ' does not appear to be a valid EDDY output basename')

    # EDDY INDICES
    if os.path.isfile(eddyIdx):
        eddyIdxs = np.genfromtxt(eddyIdx,dtype=int)
    else:
        raise ValueError(eddyIdx + ' does not appear to be a valid EDDY index file')
    # ACQUISITION PARAMETERS
    if os.path.isfile(eddyParams):
        eddyPara = np.genfromtxt(eddyParams, dtype=float)
        #eddyPara = eddyPara.flatten()
        if eddyPara.ndim > 1:
            tmp_eddyPara = np.ascontiguousarray(eddyPara).view(np.dtype((np.void, eddyPara.dtype.itemsize * eddyPara.shape[1])))
            _, idx, inv_idx = np.unique(tmp_eddyPara, return_index=True, return_inverse=True)
            eddyIdxs = inv_idx[eddyIdxs-1]+1
            eddyPara = eddyPara[idx]
        eddyPara = eddyPara.flatten()
    else:
        raise ValueError(eddyParams + ' does not appear to be a valid EDDY parameter file')
    # MASK
    if os.path.isfile(mask + '.nii.gz'):
        mask = mask + '.nii.gz'
    elif os.path.isfile(mask + '.nii'):
        mask = mask + '.nii'
    elif os.path.isfile(mask):
        mask = mask
    else:
        raise ValueError(mask + ' does not appear to be a valid brain mask file')
    # BVALS
    if os.path.isfile(bvalsFile):
        bvals = np.genfromtxt(bvalsFile, dtype=float)
    else:
        raise ValueError(bvalsFile + ' does not appear to be a valid bvals file')
    # BVECS
    if bvecsFile is not None:
        if os.path.isfile(bvecsFile):
            bvecs = np.genfromtxt(bvecsFile, dtype=float)
            if bvecs.shape[1] != bvals.size:
                raise ValueError('bvecs and bvals do not have consistent dimensions')
        else:
            raise ValueError(bvecsFile + ' does not appear to be a valid bvecs file')
    else:
        bvecs=np.array([])
    # Fieldmap
    if field is not None:
        if os.path.isfile(field):
            fieldFile = field
        elif os.path.isfile(field + '.nii.gz'):
            fieldFile = field + '.nii.gz'
        elif os.path.isfile(field + '.nii'):
            fieldFile = field + '.nii'
        else:
            fieldFile = []
            raise ValueError(field + ' does not appear to be a valid TOPUP output field')
    else:
        fieldFile = ''
    # Slspec
    if jsonFile is not None and slspecFile is not None:
        raise ValueError("Provide either an slspec file or a json file, not both")
    elif slspecFile is not None:
        if os.path.isfile(slspecFile):
            slspec = np.genfromtxt(slspecFile, dtype=int)
        else:
            raise ValueError(slspecFile + ' does not appear to be a valid slspec file')
    elif jsonFile is not None:
        if os.path.isfile(jsonFile):
            with open(jsonFile, 'r') as f:
                as_dict = json.load(f)
        else:
            raise ValueError(jsonFile + ' does not appear to be a valid JSON file')
        if 'SliceTiming' not in as_dict:
            raise ValueError(jsonFile + ' does not have a field with SliceTiming')
        slspec = utils.timings_to_slspec(as_dict['SliceTiming'])
        if slspec.shape[1] == 1:  # flatten in case of single-band data to be consistent with --slspec flag
            slspec = slspec[:, 0]
    else:
        slspec=np.array([])
    # OUTPUT FOLDER
    if oDir is not None:
        out_dir = oDir
    else:
        out_dir = eddyBase + '.qc'

    # Load eddy corrected file and check for consistency between input dimensions
    eddy_epi = nib.load(eddyFile)
    if eddy_epi.shape[3] != np.max(bvals.shape):
        raise ValueError('Number of elements in bvals does not appear to be consistent with EDDY corrected file')
    elif eddy_epi.shape[3] != np.max(eddyIdxs.shape):
        raise ValueError('Number of eddy indices does not appear to be consistent with EDDY corrected file')
    # Load binary brain mask file
    mask_vol = nib.load(mask)
    if eddy_epi.shape[0:3] != mask_vol.shape:
        raise ValueError('Mask and data dimensions are not consistent')

    #=========================================================================================
    # If directory exists, throw error. Otherwise, create
    #=========================================================================================
    if not os.path.exists(out_dir):
        # raise ValueError(out_dir + ' directory already exists! Please specify a different one.')
        os.makedirs(out_dir)

    #=========================================================================================
    # If FSL v > 6.0.1, get the eddy input parameters
    #=========================================================================================
    ec = utils.EddyCommand(eddyBase, 'quad', verbose)
    eddyInput = ec._parameters

    #=========================================================================================
    # Get data info and fill data dictionary
    #=========================================================================================
    rounded_bvals = utils.round_bvals(bvals)
    unique_bvals, counts = np.unique(rounded_bvals.astype(int), return_counts=True)

    unique_pedirs, counts_pedirs = np.unique(eddyIdxs, return_counts=True)
    protocol = np.full((unique_pedirs.size,unique_bvals.size), -1, dtype=int)
    c_b = 0
    for b in unique_bvals:
        c_p = 0
        for p in unique_pedirs:
            protocol[c_p, c_b] = ((rounded_bvals==b) & (eddyIdxs==p)).sum()
            c_p = c_p + 1
        c_b = c_b + 1
    data = {
        'subj_id':eddyFile,
        'mask_id':mask,
        'qc_path':out_dir,
        'no_dw_vols':(bvals > 100).sum(),
        'no_b0_vols':(bvals <= 100).sum(),
        'protocol':protocol.flatten(),
        'no_PE_dirs':np.size(unique_pedirs),
        'no_shells':(unique_bvals > 0).sum(),
        'bvals_id':bvalsFile,
        'bvals':rounded_bvals,
        'bvecs_id':bvecsFile,
        'bvecs':bvecs,
        'unique_bvals':unique_bvals[unique_bvals > 100],
        'bvals_dirs':counts[unique_bvals > 100],
        'eddy_idxs':eddyIdxs,
        'eddy_para':eddyPara,
        'unique_pedirs':unique_pedirs,
        'pedirs_count':counts_pedirs,
        'vol_size':eddy_epi.shape,
        'vox_size':np.array(eddy_epi.header.get_zooms()),
        'eddy_epi':eddy_epi,
        'mask':mask_vol.get_fdata(),
    }


    #=========================================================================================
    # Initialize eddyOutput dictionary
    #=========================================================================================
    eddyOutput = {
        'motionFlag':False,
        'motion':[],
        'avg_abs_mot':-1.0,
        'avg_rel_mot':-1.0,

        'paramsFlag':False,
        'params':[],
        'avg_params':np.full(9, -1.0),

        's2vFlag':False,
        's2vParams':[],
        'var_s2v_params':np.full((data['bvals'].size,6), -1.0),
        'avg_std_s2v_params':np.full(6, -1.0),

        'olFlag':False,
        'olMap':[],
        'olMap_std':[],
        'tot_ol':-1.0,
        'b_ol':np.full(data['unique_bvals'].size, -1.0),
        'pe_ol':np.full(data['no_PE_dirs'], -1.0),

        'cnrFlag':False,
        'cnrFile':[],
        'avg_cnr':np.full(1+data['unique_bvals'].size, -1.0),
        'std_cnr':np.full(1+data['unique_bvals'].size, -1.0),

        'rssFlag':False,
        'rssFile':[],
        'avg_rss':np.full(data['bvals'].size, -1.0),

        'fieldFlag':False,
        'fieldFile':[],
        'std_displacement':np.full(1, -1.0),
    }


    #=========================================================================================
    # Check which output files exist and compute qc stats
    #=========================================================================================
    outputFile = eddyBase + '.nii.gz'
    motionFile = eddyBase + '.eddy_movement_rms'            # Text file containing no. volumes X 2 columns
    paramsFile = eddyBase + '.eddy_parameters'              # Text file containing no. volumes X 9 columns
    s2vParamsFile = eddyBase + '.eddy_movement_over_time'   # Text file containing (no. volumes X no.slices / MB) rows and 6 columns
    olMapFile = eddyBase + '.eddy_outlier_map'              # Text file containing binary matrix [no. volumes X no. slices]
    cnrFile = eddyBase + '.eddy_cnr_maps.nii.gz'            # 4D file containing the eddy-based b-CNR maps (std(pred)/std(res))
    rssFile = eddyBase + '.eddy_residuals.nii.gz'           # 4D file containing the eddy-based residuals

    # figure out the number of slices
    for fn in (outputFile, cnrFile, rssFile):
        if os.path.isfile(fn):
            n_slices = nib.load(fn).shape[2]
            break
    else:
        raise ValueError("no eddy output images found, so could not determine number of slices")

    if os.path.isfile(motionFile):
        eddyOutput['motionFlag'] = True
        if verbose:
            print('RMS movement estimates file detected')
        eddyOutput['motion'] = np.genfromtxt(motionFile,dtype=float)
        eddyOutput['avg_abs_mot'] = np.mean(eddyOutput['motion'][:,0])
        eddyOutput['avg_rel_mot'] = np.mean(eddyOutput['motion'][:,1])

    if os.path.isfile(paramsFile):
        eddyOutput['paramsFlag'] = True
        if verbose:
            print('Eddy parameters file detected')
        eddyOutput['params'] = np.genfromtxt(paramsFile, dtype=float)
        eddyOutput['avg_params'][0:6] = np.mean(eddyOutput['params'][:,0:6], axis=0)
        eddyOutput['avg_params'][6:9] = np.std(eddyOutput['params'][:,6:9], axis=0)

    if os.path.isfile(s2vParamsFile):
        eddyOutput['s2vFlag'] = True
        if verbose:
            print('Eddy s2v movement file detected')
        eddyOutput['s2vParams'] = np.genfromtxt(s2vParamsFile, dtype=float)
        eddyOutput['s2vParams'][:,3:6] = np.rad2deg(eddyOutput['s2vParams'][:,3:6])
        n_vox_thr = 240 # Minimum number of voxels in a masked slice

        n_lines = eddyOutput['s2vParams'].shape[0]
        n_excitations = n_lines // bvals.size
        if bvals.size * n_excitations != n_lines:
            raise ValueError(f"Unexpected number of lines in {s2vParamsFile}. {n_lines} lines detected, which is not divisible by the number of volumes ({bvals.size}).")
        multiband_factor = n_slices // n_excitations
        if n_excitations * multiband_factor != n_slices:
            raise ValueError(f"Unexpected number of lines in {s2vParamsFile}. {n_excitations} lines detected per volume, which is not a denominator of the number of volumes ({n_slices}).")
        n_ex = n_slices // multiband_factor

        if multiband_factor == 1:
            if slspec.size == 0:
                if verbose:
                    print('Warning: slspec or json file not provided for single-band data. Assuming interleaved acquisition strategy.')
                all_slice_indices = np.arange(n_slices)
                # assume interleaved acquisition (odd slices first)
                slspec = np.concatenate((all_slice_indices[::2], all_slice_indices[1::2]))
            if slspec.shape != (n_slices, ):
                raise ValueError("Number of excitations in eddy output volumes does not match the provided --slspec/--json. Did you provide the correct --slspec or --json files?")
            ex_check = np.sum(data['mask'], axis=(0, 1))[slspec] > n_vox_thr
        else:
            ex_check = slice(None)

        for i in np.arange(0, data['bvals'].size):
            tmp = eddyOutput['s2vParams'][i*n_ex:(i+1)*n_ex]
            eddyOutput['var_s2v_params'][i] = np.var(tmp[ex_check], ddof=1, axis=0)
        eddyOutput['avg_std_s2v_params'] = np.sqrt(np.mean(eddyOutput['var_s2v_params'], axis=0))

    if os.path.isfile(olMapFile):
        eddyOutput['olFlag'] = True
        if verbose:
            print('Outliers output files detected')
        eddyOutput['olMap'] = np.genfromtxt(olMapFile,dtype=None, delimiter=" ", skip_header=1)
        eddyOutput['olMap_std'] = np.genfromtxt(eddyBase + '.eddy_outlier_n_stdev_map', dtype=float, delimiter=" ", skip_header=1)
        eddyOutput['tot_ol'] = 100*np.count_nonzero(eddyOutput['olMap'])/(data['no_dw_vols']*data['vol_size'][2])
        for i in range(0, data['unique_bvals'].size):
            eddyOutput['b_ol'][i] = 100*np.count_nonzero(eddyOutput['olMap'][data['bvals'] == data['unique_bvals'][i], :])/(data['bvals_dirs'][i]*data['vol_size'][2])
        for i in range(0, data['no_PE_dirs']):
            eddyOutput['pe_ol'][i] = 100*np.count_nonzero(eddyOutput['olMap'][data['eddy_idxs'] == data['unique_pedirs'][i],:])/(data['pedirs_count'][i]*data['vol_size'][2])

    if os.path.isfile(cnrFile):
        eddyOutput['cnrFlag'] = True
        eddyOutput['cnrFile'] = cnrFile
        if verbose:
            print('CNR output files detected')
        cnrImg = nib.load(cnrFile)
        cnr = cnrImg.get_fdata()
        if np.count_nonzero(np.isnan(cnr)):
            print("!!!Warning!!! NaNs detected in the CNR maps!!!")
        finiteMask = (data['mask'] != 0) * np.isfinite(cnr[:,:,:,0])
        eddyOutput['avg_cnr'][0] = round(np.nanmean(cnr[:,:,:,0][finiteMask]), 2)
        eddyOutput['std_cnr'][0] = round(np.nanstd(cnr[:,:,:,0][finiteMask]), 2)
        for i in range(0,data['unique_bvals'].size):
            finiteMask = (data['mask'] != 0) * np.isfinite(cnr[:,:,:,i+1])
            eddyOutput['avg_cnr'][i+1] = round(np.nanmean(cnr[:,:,:,i+1][finiteMask]), 2)
            eddyOutput['std_cnr'][i+1] = round(np.nanstd(cnr[:,:,:,i+1][finiteMask]), 2)

    if os.path.isfile(rssFile):
        eddyOutput['rssFlag'] = True
        if verbose:
            print('Eddy residuals file detected')
        eddyOutput['rssFile'] = rssFile
        rssImg = nib.load(rssFile)
        rss = rssImg.get_fdata()
        for i in range(0,data['bvals'].size):
            eddyOutput['avg_rss'][i] = np.mean(np.power(rss[:,:,:,i][data['mask'] != 0.0], 2))
        rssImg.uncache()
        del rss
        np.savetxt(data['qc_path'] + '/eddy_msr.txt', np.reshape(eddyOutput['avg_rss'], (1,-1)), fmt='%f', delimiter=' ')

    if os.path.isfile(fieldFile):
        eddyOutput['fieldFlag'] = True
        if verbose:
            print('Topup fieldmap file detected')
        eddyOutput['fieldFile'] = fieldFile
        fieldImg = nib.load(fieldFile)
        fieldMap = fieldImg.get_fdata()
        dispField = fieldMap*eddyPara[3]
        eddyOutput['std_displacement'] = np.std(dispField[data['mask'] != 0.0])
        fieldImg.uncache()
        del fieldMap


    # Stop if motion or parameters estimates are missing
    if (eddyOutput['motionFlag'] == False or
        eddyOutput['paramsFlag'] == False):
        raise ValueError('Motion estimates and/or eddy estimated parameters are missing!')

    #================================================
    # Add pages to QC report if information is there
    #================================================
    pp = PdfPages(data['qc_path'] + '/qc.pdf')

    ref_page.main(pp, data, ec)
    quad_tables.main(pp, data, eddyOutput, False)
    if eddyOutput['motionFlag']:
        quad_mot.main(pp, data, eddyOutput)
    if eddyOutput['s2vFlag']:
        quad_s2v_mot.main(pp, data, eddyOutput)
    if eddyOutput['paramsFlag']:
        quad_eddy.main(pp, data, eddyOutput)
    if eddyOutput['fieldFlag']:
        quad_susc.main(pp, data, eddyOutput)
    quad_avg_maps.main(pp, data, eddyOutput)
    if eddyOutput['olFlag']:
        quad_ol_mat.main(pp, data, eddyOutput)
    if eddyOutput['cnrFlag']:
        quad_cnr_maps.main(pp, data, eddyOutput)
    if eddyOutput['rssFlag']:
        quad_msr.main(pp, data, eddyOutput)

    #================================================
    # Set the file's metadata via the PdfPages object:
    #================================================
    d = pp.infodict()
    d['Title'] = 'eddy_quad QC report'
    d['Author'] = u'Matteo Bastiani'
    d['Subject'] = 'subject QC report'
    d['Keywords'] = 'QC dMRI'
    d['CreationDate'] = datetime.datetime.today()
    d['ModDate'] = datetime.datetime.today()

    pp.close()


    #=========================================================================================
    # Export stats and data info to json file
    #=========================================================================================
    quad_json.main(data, eddyOutput, ec)
