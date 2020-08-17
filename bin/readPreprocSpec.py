#!/opt/conda/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import json
import configparser
from io import StringIO

class preProcSpec(object):

    def __init__(self, preprocfile, bids_dir, outputdir):
        self.atlas = 'BCI'
        self.singleThread = 'OFF'
        self.cache = '/tmp'
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
        self.bids_dir = bids_dir
        self.outputdir = outputdir

        self.read_success = True
        self.read_preprocfile(preprocfile)

        if self.read_success == False:
            return

        # self.create_subjectList()

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

        self.atlas = specs['BrainSuite']['Structural']['atlas']
        self.singleThread = specs['BrainSuite']['Structural']['singleThread']
        self.cache = specs['BrainSuite']['Structural']['cacheFolder']
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


