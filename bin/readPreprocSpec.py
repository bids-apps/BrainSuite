#!/opt/conda/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import json
import configparser
from io import StringIO
import nipype.pipeline.engine as pe
import nipype.interfaces.brainsuite as bs

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
        self.TR = 0
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
        self.bids_dir = bids_dir
        self.outputdir = outputdir

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
        self.fieldmapCorrection = undefined
        self.diffusion_time_ms = undefined

        # smoothing
        self.smoothvol = 3.0
        self.smoothsurf = 2.0

    def read_preprocfile(self, preprocfile):
        if not os.path.isfile(preprocfile):
            sys.stdout.write('Model specification file not found.\n')
            self.read_success = False
            return

        try:
            specs = json.load(open(preprocfile))
        except:
            sys.stdout.writable("There was an error reading the model specification file."
                                "\nPlease check that the format of the file is JSON.")
            return

        # svreg
        self.atlas = specs['BrainSuite']['Structural']['atlas']
        self.singleThread = bool(specs['BrainSuite']['Structural']['singleThread'])

        # nipype config
        self.cache = specs['BrainSuite']['Structural']['cacheFolder']

        # bse
        self.autoParameters = bool(specs['BrainSuite']['Structural']['autoParameters'])
        self.diffusionIterations = specs['BrainSuite']['Structural']['diffusionIterations']
        self.diffusionConstant = specs['BrainSuite']['Structural']['diffusionConstant']
        self.edgeDetectionConstant = specs['BrainSuite']['Structural']['edgeDetectionConstant']
        self.skipBSE = bool(specs['BrainSuite']['Structural']['skipBSE'])
        # bfc
        self.iterativeMode = bool(specs['BrainSuite']['Structural']['iterativeMode'])
        # pvc
        self.spatialPrior = specs['BrainSuite']['Structural']['spatialPrior']
        # cerebro
        self.costFunction = specs['BrainSuite']['Structural']['costFunction']
        self.useCentroids = bool(specs['BrainSuite']['Structural']['useCentroids'])
        self.linearConvergence = specs['BrainSuite']['Structural']['linearConvergence']
        self.warpConvergence = specs['BrainSuite']['Structural']['warpConvergence']
        self.warpLevel = specs['BrainSuite']['Structural']['warpLevel']
        # inner cortical mask
        self.tissueFractionThreshold = specs['BrainSuite']['Structural']['tissueFractionThreshold']

        # bdp
        self.skipDistortionCorr = bool(specs['BrainSuite']['Diffusion']['skipDistortionCorr'])
        self.phaseEncodingDirection = specs['BrainSuite']['Diffusion']['phaseEncodingDirection']
        self.estimateODF_3DShore = bool(specs['BrainSuite']['Diffusion']['estimateODF_3DShore'])
        self.estimateODF_GQI = bool(specs['BrainSuite']['Diffusion']['estimateODF_GQI'])
        self.generateStats = bool(specs['BrainSuite']['Diffusion']['generateStats'])
        self.forcePartialROIStats = bool(specs['BrainSuite']['Diffusion']['forcePartialROIStats'])

        self.echoSpacing = undefined if (specs['BrainSuite']['Diffusion']['echoSpacing'] == '' ) \
            else specs['BrainSuite']['Diffusion']['echoSpacing']
        self.fieldmapCorrection = undefined if (specs['BrainSuite']['Diffusion']['fieldmapCorrection']  == '') \
            else specs['BrainSuite']['Diffusion']['fieldmapCorrection']
        self.diffusion_time_ms = undefined if (specs['BrainSuite']['Diffusion']['diffusion_time_ms'] == '') \
            else specs['BrainSuite']['Diffusion']['diffusion_time_ms']

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
        self.shape = specs['BrainSuite']['Functional']['EnableShapeMeasures']
        self.t1space = specs['BrainSuite']['Functional']['T1SpaceProcessing']
        self.fslrigid = specs['BrainSuite']['Functional']['FSLRigid']
        self.simref = specs['BrainSuite']['Functional']['SimRef']
        self.rundetrend = specs['BrainSuite']['Functional']['RunDetrend']
        self.runnsr = specs['BrainSuite']['Functional']['RunNSR']
        self.scbpath = specs['BrainSuite']['Functional']['scbPath']
        self.T1mask = specs['BrainSuite']['Functional']['T1mask']

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
        config.set('main','memory', str(self.memory))
        config.set('main','EnableShapeMeasures', str(self.shape))
        config.set('main','T1SpaceProcessing', str(self.t1space))
        config.set('main','FSLRigid', str(self.fslrigid))
        config.set('main','SimRef', str(self.simref))
        config.set('main','RunDetrend', str(self.rundetrend))
        config.set('main','RunNSR', str(self.runnsr))
        config.set('main', 'scbPath', str(self.scbpath))
        config.set('main', 'T1mask', str(self.T1mask))

        with open('{0}/config.ini'.format(self.outputdir), 'w') as configfile:
            config.write(configfile)

        with open('{0}/config.ini'.format(self.outputdir), 'r') as fin:
            data = fin.read().splitlines(True)
        with open('{0}/config.ini'.format(self.outputdir), 'w') as fout:
            fout.writelines(data[1:])

        self.read_file = True


