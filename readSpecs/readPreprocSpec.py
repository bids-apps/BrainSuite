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

import os
import sys
import json
import configparser
from io import StringIO
import nipype.pipeline.engine as pe
import nipype.interfaces.brainsuite as bs
from datetime import datetime
from collections import OrderedDict

Obj = pe.Node(interface=bs.Bfc(), name='Obj')
undefined = Obj.inputs.biasRange

class preProcSpec(object):

    def __init__(self, bids_dir, outputdir):
        self.read_file = False

        # svreg
        self.atlas = 'BCI'
        self.singleThread = False

        # nipype config
        self.cache = '/tmp'

        # bfp
        self.taskname = ["rest"]
        self.TR = 2
        self.continuerun = 1
        self.multithread = 1
        self.tnlmpdf = 1
        self.fpr = 0.001
        self.fslotype= 'NIFTI_GZ'
        self.fwhm = 6
        self.highpass =0.005
        self.lowpass= 0.1
        self.memory = 16
        self.shape = 0
        self.t1space = 1
        self.fslrigid = 0
        self.bpoption = 1
        self.rundetrend = 1
        self.runnsr = 1
        self.uscrigid_similarity = 'inversion'
        self.bids_dir = bids_dir
        self.outputdir = outputdir

        self.scbpath = ''
        self.T1mask = True
        self.epit1corr = 0
        self.epit1corr_mask = 3
        self.epit1corr_rigidsim = 'mi'
        self.epit1corr_bias = 1
        self.epit1corr_numthreads = 60
        self.simref = 1

        # bse
        self.autoParameters = True
        self.prescale = False
        self.diffusionIterations = 3
        self.diffusionConstant = 25
        self.edgeDetectionConstant = 0.64
        self.skipBSE = False
        # bfc
        self.iterativeMode = False
        # pvc
        self.spatialPrior = 0.1
        # cerebro
        self.costFunction = 2
        self.useCentroids = False
        self.linearConvergence = 0.1
        self.warpConvergence = 100
        self.warpLevel = 5
        # inner cortical mask
        self.tissueFractionThreshold = 50.0

        # bdp
        self.fsleddy = False
        self.indexFile = ''
        self.acqpFile = ''
        self.flm = 'quadratic'
        self.slm = 'none'
        self.fep = False
        self.interp = 'spline'
        self.nvoxhp = 1000
        self.fudge_factor = 10
        self.dont_sep_offs_move = False
        self.dont_peas = False
        self.niter = 5
        self.eddy_final_resamp = 'jac'
        self.repol = False
        self.eddy_num_threads = 1
        self.is_shelled = False
        self.cnr_maps = False
        self.residuals = False
        self.useDerivatives = False
        self.correctedOutputDir = ''
        self.correctedOutputSuffix = ''
        self.skipDistortionCorr = False
        self.phaseEncodingDirection = "y"
        self.estimateODF_3DShore = False
        self.estimateODF_GQI = False
        self.generateStats = False
        self.forcePartialROIStats = False


        self.echoSpacing = undefined
        self.fieldmapCorrection = None
        self.diffusion_time_ms = undefined

        self.estimateODF_ERFO = False
        self.sigma_GQI = undefined
        self.ERFO_SNR = undefined

        # smoothing
        self.smoothvol = 3.0
        self.smoothsurf = 2.0

    def read_preprocfile(self, preprocfile, subjectID):

        try:
            if not os.path.isfile(preprocfile):
                sys.stdout.write('##############################################\n'
                                '##############################################\n'
                                '##############################################\n'
                                '************ ERROR!!! ************ \n'
                                'Preprocecssing specification file {0} not found.\n'
                                'If running Docker-based BrainSuite BIDS App, \n'
                                'please make sure that the path follows the filesystem of the container.\n'
                                '##############################################\n'
                                '##############################################\n'
                                '##############################################\n'.format(preprocfile))
                sys.exit(2)
        except TypeError as e:
            sys.stdout.write('##############################################\n'
                                '##############################################\n'
                                '##############################################\n'
                                '************ ERROR!!! ************ \n'
                                'Preprocecssing specification path not defined.\n'
                                '##############################################\n'
                                '##############################################\n'
                                '##############################################\n')
            print(e, '\n')
            sys.exit(2)

        try:
            specs = json.load(open(preprocfile))
            self.specs = specs
        except SyntaxError as e:
            sys.stdout.write('##############################################\n'
                             '##############################################\n'
                             '##############################################\n'
                             '************ ERROR!!! ************\n '
                             'There was an error reading the model specification file.\n'
                             'Please check that the JSON file is properly formatted.\n'
                             '##############################################\n'
                             '##############################################\n'
                             '##############################################\n'
                             '\n'
                             'JSON reading error message:\n'
            )
            print(e, '\n')
            sys.exit(2)

        # write a copy of the preproc.json file
        CT = datetime.now()
        CTstring = 'Y{0}M{1}D{2}H{3}M{4}S{5}ms{6}'.format(CT.year,CT.month,CT.day,CT.hour, CT.minute,CT.second,CT.microsecond)
        preprocArchived = os.path.join(self.outputdir, subjectID, 'preprocspecs_{0}.json'.format(CTstring))
        with open(preprocArchived, 'w') as f:
            json.dump(self.specs, f)

        # svreg
        self.atlas = specs['BrainSuite']['Anatomical']['atlas']
        self.singleThread = bool(specs['BrainSuite']['Anatomical']['singleThread'])

        # nipype config
        self.cache = specs['BrainSuite']['Global Settings']['cacheFolder']

        # bse
        self.autoParameters = bool(specs['BrainSuite']['Anatomical']['autoParameters'])
        self.prescale = bool(specs['BrainSuite']['Anatomical']['prescale'])
        self.diffusionIterations = specs['BrainSuite']['Anatomical']['diffusionIterations']
        self.diffusionConstant = specs['BrainSuite']['Anatomical']['diffusionConstant']
        self.edgeDetectionConstant = specs['BrainSuite']['Anatomical']['edgeDetectionConstant']
        self.skipBSE = bool(specs['BrainSuite']['Anatomical']['skipBSE'])
        # bfc
        self.iterativeMode = bool(specs['BrainSuite']['Anatomical']['iterativeMode'])
        # pvc
        self.spatialPrior = specs['BrainSuite']['Anatomical']['spatialPrior']
        # cerebro
        self.costFunction = specs['BrainSuite']['Anatomical']['costFunction']
        self.useCentroids = bool(specs['BrainSuite']['Anatomical']['useCentroids'])
        self.linearConvergence = specs['BrainSuite']['Anatomical']['linearConvergence']
        self.warpConvergence = specs['BrainSuite']['Anatomical']['warpConvergence']
        self.warpLevel = specs['BrainSuite']['Anatomical']['warpLevel']
        # inner cortical mask
        self.tissueFractionThreshold = specs['BrainSuite']['Anatomical']['tissueFractionThreshold']

        # bdp
        self.fsleddy = bool(specs['BrainSuite']['Diffusion']['fsleddy'])
        self.indexFile = specs['BrainSuite']['Diffusion']['indexFile']
        self.acqpFile = specs['BrainSuite']['Diffusion']['acqpFile']
        if self.fsleddy:
            if not os.path.exists(self.indexFile):
                print('Index file (indexFile field) for FSL eddy does not exist or cannot be found.')
                sys.exit(2)
            if not os.path.exists(self.acqpFile):
                print('Acquisition parameter (acqpFile field) file for FSL eddy does not exist or cannot be found.')
                sys.exit(2)
        self.skipDistortionCorr = bool(specs['BrainSuite']['Diffusion']['skipDistortionCorr'])
        self.phaseEncodingDirection = specs['BrainSuite']['Diffusion']['phaseEncodingDirection']
        self.estimateODF_3DShore = bool(specs['BrainSuite']['Diffusion']['estimateODF_3DShore'])
        self.estimateODF_GQI = bool(specs['BrainSuite']['Diffusion']['estimateODF_GQI'])
        self.estimateODF_ERFO = bool(specs['BrainSuite']['Diffusion']['estimateODF_ERFO'])
        self.diffusion_time_ms = specs['BrainSuite']['Diffusion']['diffusion_time_ms']
        if self.estimateODF_ERFO or self.estimateODF_3DShore or self.estimateODF_GQI:
            if not self.diffusion_time_ms:
                sys.exit('##############################################\n'
                             '##############################################\n'
                             '##############################################\n'
                             '************ ARGUMENT ERROR!!! ************\n '
                             'Estimation of ODF using 3DSHORE, GQI, or ERFO was \n'
                             'turned on but diffusion_time_ms was not set. Please.\n'
                             'set a numerical value for this parameter. \n'
                             '##############################################\n'
                             '##############################################\n'
                             '##############################################\n'
                             '\n')

        self.echoSpacing = undefined if (specs['BrainSuite']['Diffusion']['echoSpacing'] == '' ) \
            else specs['BrainSuite']['Diffusion']['echoSpacing']
        self.fieldmapCorrection = None if (specs['BrainSuite']['Diffusion']['fieldmapCorrection']  == '') \
            else specs['BrainSuite']['Diffusion']['fieldmapCorrection']

        self.sigma_GQI = undefined if (specs['BrainSuite']['Diffusion']['sigma_GQI'] == '') \
            else specs['BrainSuite']['Diffusion']['sigma_GQI']
        self.ERFO_SNR = undefined if (specs['BrainSuite']['Diffusion']['ERFO_SNR'] == '') \
            else specs['BrainSuite']['Diffusion']['ERFO_SNR']

        self.flm = specs['BrainSuite']['Diffusion']['flm']
        self.slm = specs['BrainSuite']['Diffusion']['slm']
        self.fep = bool(specs['BrainSuite']['Diffusion']['fep'])
        self.interp = specs['BrainSuite']['Diffusion']['interp']
        self.nvoxhp = specs['BrainSuite']['Diffusion']['nvoxhp']
        self.fudge_factor = specs['BrainSuite']['Diffusion']['fudge_factor']
        self.dont_sep_offs_move = bool(specs['BrainSuite']['Diffusion']['dont_sep_offs_move'])
        self.dont_peas = bool(specs['BrainSuite']['Diffusion']['dont_peas'])
        self.niter = specs['BrainSuite']['Diffusion']['niter']
        self.eddy_final_resamp = specs['BrainSuite']['Diffusion']['eddy_final_resamp']
        self.repol = bool(specs['BrainSuite']['Diffusion']['repol'])
        self.eddy_num_threads = bool(specs['BrainSuite']['Diffusion']['eddy_num_threads'])
        self.is_shelled = bool(specs['BrainSuite']['Diffusion']['is_shelled'])
        # self.cnr_maps = bool(specs['BrainSuite']['Diffusion']['cnr_maps'])
        # self.residuals = bool(specs['BrainSuite']['Diffusion']['residuals'])

        self.useDerivatives = bool(specs['BrainSuite']['Diffusion']['useDerivatives'])
        self.correctedOutputDir = specs['BrainSuite']['Diffusion']['correctedOutputDir']
        self.correctedOutputSuffix = specs['BrainSuite']['Diffusion']['correctedOutputSuffix']

        # check diffusion_time_ms dependency
        if self.estimateODF_3DShore:
            assert self.diffusion_time_ms != undefined, "If you would like to estimate using 3DShore, " \
                                                        "please define the diffusion time, in ms."


        # smoothing
        self.smoothvol = specs['BrainSuite']['PostProc']['smoothVol']
        self.smoothsurf = specs['BrainSuite']['PostProc']['smoothSurf']


        self.taskname = specs['BrainSuite']['Functional']['task-name']
        self.TR = specs['BrainSuite']['Functional']['TR']
        # self.continuerun = specs['BrainSuite']['ContinueRun']
        # self.multithread = specs['BrainSuite']['MultiThreading']
        self.tnlmpdf = specs['BrainSuite']['Functional']['EnabletNLMPdfFiltering']
        self.fpr = specs['BrainSuite']['Functional']['fpr']
        self.fslotype = specs['BrainSuite']['Functional']['FSLOUTPUTTYPE']
        self.fwhm = specs['BrainSuite']['Functional']['FWHM']
        self.highpass = specs['BrainSuite']['Functional']['HIGHPASS']
        self.lowpass = specs['BrainSuite']['Functional']['LOWPASS']
        self.memory = specs['BrainSuite']['Functional']['memory']
        self.multithread = specs['BrainSuite']['Functional']['MultiThreading']
        # self.shape = specs['BrainSuite']['Functional']['EnableShapeMeasures']
        # self.t1space = specs['BrainSuite']['Functional']['T1SpaceProcessing']
        self.fslrigid = specs['BrainSuite']['Functional']['FSLRigid']
        self.bpoption = specs['BrainSuite']['Functional']['BPoption']
        self.rundetrend = specs['BrainSuite']['Functional']['RunDetrend']
        self.runnsr = specs['BrainSuite']['Functional']['RunNSR']
        self.scbpath = specs['BrainSuite']['Functional']['scbPath']
        if not self.scbpath:
            self.scbpath = os.path.join(self.outputdir, subjectID, 'func', 'scb.mat')
        self.T1mask = specs['BrainSuite']['Functional']['T1mask']
        # self.epit1corr = specs['BrainSuite']['Functional']['epit1corr']
        # self.epit1corr_mask = specs['BrainSuite']['Functional']['epit1corr_mask']
        # self.epit1corr_rigidsim = specs['BrainSuite']['Functional']['epit1corr_rigidsim']
        # self.epit1corr_bias = specs['BrainSuite']['Functional']['epit1corr_bias']
        # self.epit1corr_numthreads = specs['BrainSuite']['Functional']['epit1corr_numthreads']
        self.uscrigid_similarity = specs['BrainSuite']['Functional']['uscrigid_similarity']
        self.simref = specs['BrainSuite']['Functional']['SimRef']

        ini_str = u'[main]\n' + open('/config.ini', 'r').read()
        ini_fp = StringIO(ini_str)
        config = configparser.RawConfigParser()
        # config.optionxform(str())
        config.optionxform = str
        config.read_file(ini_fp)
        # config = configparser.ConfigParser()
        # config.read('/config.ini')

        ## edit config file
        # config.set('main','CONTINUERUN', str(self.continuerun))
        # config.set('main','MultiThreading', str(self.multithread))
        config.set('main','EnabletNLMPdfFiltering', str(self.tnlmpdf))
        config.set('main','fpr', str(self.fpr))
        config.set('main','FSLOUTPUTTYPE', str(self.fslotype))
        config.set('main','FWHM', str(self.fwhm))
        config.set('main','HIGHPASS', str(self.highpass))
        config.set('main','LOWPASS', str(self.lowpass))
        config.set('main', 'MultiThreading', str(self.multithread))
        config.set('main','memory', str(self.memory))
        config.set('main','EnableShapeMeasures', str(self.shape))
        config.set('main','T1SpaceProcessing', str(self.t1space))
        config.set('main','FSLRigid', str(self.fslrigid))
        config.set('main','SimRef', str(self.simref))
        # config.set('main', 'epit1corr', str(self.epit1corr))
        # config.set('main', 'epit1corr_mask', str(self.epit1corr_mask))
        # config.set('main', 'epit1corr_rigidsim', str(self.epit1corr_rigidsim))
        # config.set('main', 'epit1corr_bias', str(self.epit1corr_bias))
        # config.set('main', 'epit1corr_numthreads', str(self.epit1corr_numthreads))

        config.set('main','RunDetrend', str(self.rundetrend))
        config.set('main','RunNSR', str(self.runnsr))
        config.set('main', 'scbPath', str(self.scbpath))
        config.set('main', 'T1mask', str(self.T1mask))
        config.set('main', 'uscrigid_similarity', str(self.uscrigid_similarity))

        with open('{0}/config.ini'.format(self.outputdir + '/' + subjectID), 'w') as configfile:
            config.write(configfile)

        with open('{0}/config.ini'.format(self.outputdir + '/' + subjectID), 'r') as fin:
            data = fin.read().splitlines(True)
        with open('{0}/config.ini'.format(self.outputdir + '/' + subjectID), 'w') as fout:
            fout.writelines(data[1:])

        self.read_file = True


    def write_preproc_params(self, outputdir, STAGES, dataset_description_file=None):

        timeofrun = datetime.now()

        paramfile = outputdir + '/brainsuite_run_params.json'
            #.format(timeofrun.strftime('%m%d%Y_time%H%M%S'))

        params= OrderedDict()

        if dataset_description_file:
            try:
                dataset_description = json.load(open(dataset_description_file))
                params['DATASET DESCRIPTION'] = []
                params['DATASET DESCRIPTION'].append({
                    'Dataset Name' : dataset_description['Name'],
                    'BIDSVersion': dataset_description['BIDSVersion']
                })
            except SyntaxError as e:
                sys.stdout.write('dataset_description.json file did not read in successfully due to syntax error:\n')
                print(e,'\n')
                sys.exit(2)
            except KeyError as e:
                sys.stdout.write('There is a missing JSON field in the dataset_description.json file:\n')
                print(e, '\n')
                sys.exit(2)

        params['BrainSuite BIDS App run parameters'] = []
        params['BrainSuite BIDS App run parameters'].append({
            'DATE and TIME OF RUN' : timeofrun.strftime('%Y-%m-%d %H:%M:%S'),
            'STAGES' : STAGES,
            'NIPYPE CACHE FOLDER': self.cache
        })

        if 'CSE' in STAGES:
            params['BrainSuite BIDS App run parameters'].append({
                'CSE': {
                    'autoParameters': self.autoParameters,
                    'diffusionIterations' : self.diffusionIterations,
                    'diffusionConstant' : self.diffusionConstant,
                    'edgeDetectionConstant' : self.edgeDetectionConstant,
                    'skipBSE' : self.skipBSE,
                    'iterativeMode' : self.iterativeMode,
                    'spatialPrior': self.spatialPrior,
                    'costFunction': self.costFunction ,
                    'useCentroids' : self.useCentroids,
                    'linearConvergence': self.linearConvergence,
                    'warpConvergence': self.warpConvergence,
                    'warpLevel': self.warpLevel,
                    'tissueFractionThreshold': self.tissueFractionThreshold
                }
            })
        if 'SVREG' in STAGES:
            params['BrainSuite BIDS App run parameters'].append({
                'SVREG' : {
                    'atlas': self.atlas,
                    'singleThread': self.singleThread
                }
            })

        if 'BDP' in STAGES:
            echoSpacing = self.echoSpacing
            fieldmapCorrection = self.fieldmapCorrection
            diffusion_time_ms = self.diffusion_time_ms
            if self.echoSpacing == undefined:
                echoSpacing = ''
            if self.fieldmapCorrection == undefined:
                fieldmapCorrection = ''
            if self.diffusion_time_ms == undefined:
                diffusion_time_ms = ''
            params['BrainSuite BIDS App run parameters'].append({
                'BDP': {
                    'skipDistortionCorr' : self.skipDistortionCorr,
                    'phaseEncodingDirection': self.phaseEncodingDirection,
                    'estimateODF_3DShore' : self.estimateODF_3DShore,
                    'estimateODF_GQI': self.estimateODF_GQI,
                    'echoSpacing': echoSpacing,
                    'fieldmapCorrection': fieldmapCorrection,
                    'diffusion_time_ms': diffusion_time_ms
                }
            })

        if ('CSE' in STAGES) or ('SVREG' in STAGES):
            params['BrainSuite BIDS App run parameters'].append({
                'POSTPROC SMOOTHING LEVELS': {
                        'smoothVol': self.smoothvol,
                        'smoothSurf': self.smoothsurf
                }
            })

        if 'BFP' in STAGES:
            params['BrainSuite BIDS App run parameters'].append({
                'BFP': {
                    'task-name': self.taskname,
                    'TR': self.TR,
                    'EnabletNLMPdfFiltering': self.tnlmpdf,
                    'fpr' : self.fpr,
                    'FSLOUTPUTTYPE': self.fslotype,
                    'FWHM': self.fwhm,
                    'HIGHPASS': self.highpass,
                    'LOWPASS': self.lowpass,
                    'memory': self.memory,
                    'EnableShapeMeasures': self.shape,
                    'T1SpaceProcessing': self.t1space,
                    'FSLRigid': self.fslrigid,
                    'BPoption': self.bpoption,
                    'RunDetrend': self.rundetrend,
                    'RunNSR': self.runnsr,
                    'scbPath': self.scbpath,
                    'T1mask': self.T1mask,
                    'epit1corr' : self.epit1corr,
                    'epit1corr_mask' : self.epit1corr_mask,
                    'epit1corr_rigidsim': self.epit1corr_rigidsim,
                    'epit1corr_bias' : self.epit1corr_bias,
                    'epit1corr_numthreads': self.epit1corr_numthreads,
                    'SimRef': self.simref
                }
            })

        with open(paramfile, 'w') as f:
            json.dump(params, f)

    def write_subjectIDsJSON(self, t1ws, args, WEBDIR):
        subjectIDs = {'subjects':[]}
        for i, t1 in enumerate(t1ws):
            subjectID = t1ws[i].split('/')[-1].split('_T1w')[0]
            if args.ignore_suffix:
                subjectID_tmp = [tok for tok in subjectID.split('_') if not args.ignore_suffix in tok]
                subjectID = '_'.join(subjectID_tmp)
            subjectIDs['subjects'].append(subjectID)

        with open(WEBDIR + '/subjectIDs.json', 'w') as f:
            json.dump(subjectIDs, f)
