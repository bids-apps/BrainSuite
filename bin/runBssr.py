# -*- coding: utf-8 -*-
'''
Copyright (C) 2023 The Regents of the University of California

Created by Yeun Kim

This file is part of the BrainSuite BIDS App.

The BrainSuite BIDS App is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public License
as published by the Free Software Foundation, version 2.1.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
'''

import sys
import rpy2
from rpy2.robjects.packages import importr
import rpy2.robjects as ro
import warnings
from rpy2.rinterface import RRuntimeWarning
warnings.filterwarnings("ignore", category=RRuntimeWarning)
import numpy as np
import rpy2.robjects.numpy2ri
rpy2.robjects.numpy2ri.activate()

valid_analysis_types = ['vbm', 'tbm', 'cbm', 'dbm', 'roi', 'croi', 'droi']
# ro.r('.libPaths( c( .libPaths(), "/usr/local/lib/R/site-library/") )')
bssr = importr('bssr')

def equal(a, b):
    return abs( a - b ) <= 0

def load_bss_data(specs):

    # make optional strings
    if not specs.smooth or specs.smooth == '' or equal(float(specs.smooth), 0):
        OPT = 0
    else:
        OPT = specs.smooth

    if specs.measure not in valid_analysis_types:
        sys.stdout.write("Specified measure of interest is not a valid type.\n")
        sys.exit(1)

    elif specs.measure == "cbm":
        bss_data = bssr.load_bss_data(type='cbm', subjdir= specs.outputdir, csv=specs.tsv, hemi=specs.hemi,
                                      smooth=OPT, exclude_col = specs.exclude_col)
    elif specs.measure == "tbm":
        bss_data = bssr.load_bss_data(type = 'tbm', subjdir=specs.outputdir, csv = specs.tsv, smooth=OPT,
                                      maskfile=specs.maskfile, exclude_col=specs.exclude_col)

    elif specs.measure == "dbm":
        bss_data = bssr.load_bss_data(type= 'dbm', subjdir=specs.outputdir, csv= specs.tsv, smooth=OPT,
                                      measure=specs.dbmmeas, maskfile=specs.maskfile, exclude_col=specs.exclude_col)
    elif specs.measure == "roi":
        rois = ro.vectors.IntVector(specs.roi)
        bss_data = bssr.load_bss_data(type='roi', subjdir=specs.outputdir, csv= specs.tsv, roiids=rois,
                                      roimeas=specs.roimeas, exclude_col = specs.exclude_col)

    else:
        sys.stdout.write("This imaging measure it not supported yet.")
        sys.exit(1)

    return bss_data

def run_model(specs, bss_data):
    if specs.measure == "roi":
        if specs.test == 'anova':
            cov = "+".join(specs.covariates)
            bss_model = bssr.bss_anova(main_effect=specs.main_effect, covariates=cov, bss_data=bss_data,
                                       mult_comp=specs.mult_comp)
        elif specs.test == 'lm':
            cov = "+".join(specs.covariates)
            bss_model = bssr.bss_anova(main_effect=specs.main_effect, covariates=cov, bss_data=bss_data,
                                       mult_comp=specs.mult_comp)

        elif specs.test == 'corr':
            bss_model = bssr.bss_corr(corr_var=specs.corr_var, bss_data=bss_data, mult_comp=specs.mult_comp)

        elif specs.test == 'ttest':
            bss_model = bssr.bss_ttest(group_var=specs.group_var, bss_data=bss_data, paired=specs.paired,
                                       mult_comp=specs.mult_comp)

        else:
            sys.stdout.write("Specified test is not a valid type.\n")
            sys.exit(1)

    else:
        if specs.test == 'anova':
            cov = "+".join(specs.covariates)
            bss_model = bssr.bss_anova(main_effect=specs.main_effect, covariates=cov, bss_data=bss_data,
                                       mult_comp=specs.mult_comp) #, niter=specs.niter, pvalue=specs.pvalue
        elif specs.test == 'lm':
            cov = "+".join(specs.covariates)
            bss_model = bssr.bss_anova(main_effect=specs.main_effect, covariates=cov, bss_data=bss_data,
                                       mult_comp=specs.mult_comp) #, niter=specs.niter, pvalue=specs.pvalue

        elif specs.test == 'corr':
            bss_model = bssr.bss_corr(corr_var=specs.corr_var, bss_data=bss_data, mult_comp=specs.mult_comp)

        elif specs.test == 'ttest':
            bss_model = bssr.bss_ttest(group_var=specs.group_var, bss_data=bss_data, paired=specs.paired,
                                       mult_comp=specs.mult_comp)

        else:
            sys.stdout.write("Specified test is not a valid type.\n")
            sys.exit(1)
    return bss_model

def save_bss(bss_data, bss_model, outdir):
    bssr.save_bss_out(bss_data, bss_model, outdir=outdir, overwrite = True)
