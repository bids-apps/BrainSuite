#!/opt/conda/bin/python
# -*- coding: utf-8 -*-

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
        self.bids_dir = bids_dir
        self.outputdir = outputdir

        self.scbpath = ''
        self.T1mask = True
        self.epit1corr = 1
        self.epit1corr_mask = 3
        self.epit1corr_rigidsim = 'mi'
        self.epit1corr_bias = 1
        self.epit1corr_numthreads = 60
        self.simref = 1

        # bse
        self.autoParameters = True
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
        if not os.path.isfile(preprocfile):
            sys.stdout.write('##############################################\n'
                             '##############################################\n'
                             '##############################################\n'
                             '************ WARNING!!! ************ \n'
                             'Preprocecssing specification file not found.\n'
                             'Running with default parameters!!!!'
                             '##############################################\n'
                             '##############################################\n'
                             '##############################################\n')
            self.read_success = False
            return

        try:
            specs = json.load(open(preprocfile))
            self.specs = specs
        except Exception as e:
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
            return

        # svreg
        self.atlas = specs['BrainSuite']['Anatomical']['atlas']
        self.singleThread = bool(specs['BrainSuite']['Anatomical']['singleThread'])

        # nipype config
        self.cache = specs['BrainSuite']['Global Settings']['cacheFolder']

        # bse
        self.autoParameters = bool(specs['BrainSuite']['Anatomical']['autoParameters'])
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
        self.T1mask = specs['BrainSuite']['Functional']['T1mask']
        self.epit1corr = specs['BrainSuite']['Functional']['epit1corr']
        self.epit1corr_mask = specs['BrainSuite']['Functional']['epit1corr_mask']
        self.epit1corr_rigidsim = specs['BrainSuite']['Functional']['epit1corr_rigidsim']
        self.epit1corr_bias = specs['BrainSuite']['Functional']['epit1corr_bias']
        self.epit1corr_numthreads = specs['BrainSuite']['Functional']['epit1corr_numthreads']
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
        config.set('main', 'epit1corr', str(self.epit1corr))
        config.set('main', 'epit1corr_mask', str(self.epit1corr_mask))
        config.set('main', 'epit1corr_rigidsim', str(self.epit1corr_rigidsim))
        config.set('main', 'epit1corr_bias', str(self.epit1corr_bias))
        config.set('main', 'epit1corr_numthreads', str(self.epit1corr_numthreads))

        config.set('main','RunDetrend', str(self.rundetrend))
        config.set('main','RunNSR', str(self.runnsr))
        config.set('main', 'scbPath', str(self.scbpath))
        config.set('main', 'T1mask', str(self.T1mask))

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
            except:
                print('dataset_description.json file did not read in successfully.\n')

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
