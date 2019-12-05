#!/opt/conda/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import json
import configparser
from io import StringIO

class preProcSpec(object):

    def __init__(self, preprocfile, bids_dir):
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

        self.atlas = specs['BrainSuite']['atlas']
        self.singleThread = specs['BrainSuite']['singleThread']
        self.cache = specs['BrainSuite']['cacheFolder']
        self.TR = specs['BrainSuite']['TR']
        self.continuerun = specs['BrainSuite']['ContinueRun']
        self.multithread = specs['BrainSuite']['MultiThreading']
        self.tnlmpdf = specs['BrainSuite']['EnabletNLMPdfFiltering']
        self.fpr = specs['BrainSuite']['fpr']
        self.fslotype = specs['BrainSuite']['FSLoutputType']
        self.fwhm = specs['BrainSuite']['FWHM']
        self.highpass = specs['BrainSuite']['Highpass']
        self.lowpass = specs['BrainSuite']['Lowpass']
        self.memory = specs['BrainSuite']['memory']
        self.shape = specs['BrainSuite']['EnableShapeMeasures']
        self.t1space = specs['BrainSuite']['T1SpaceProcessing']
        self.fslrigid = specs['BrainSuite']['FSLRigid']
        self.simref = specs['BrainSuite']['SimRef']
        self.rundetrend = specs['BrainSuite']['RunDetrend']
        self.runnsr = specs['BrainSuite']['RunNSR']
        self.scbpath = specs['BrainSuite']['scbPath']

        ini_str = u'[main]\n' + open('/config.ini', 'r').read()
        ini_fp = StringIO(ini_str)
        config = configparser.RawConfigParser()
        # config.optionxform(str())
        config.optionxform = str
        config.readfp(ini_fp)
        # config = configparser.ConfigParser()
        # config.read('/config.ini')

        ## edit config file
        config.set('main','CONTINUERUN', str(self.continuerun))
        config.set('main','MultiThreading', str(self.multithread))
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

        with open('{0}/config.ini'.format(self.bids_dir), 'wb') as configfile:
            config.write(configfile)

        with open('{0}/config.ini'.format(self.bids_dir), 'r') as fin:
            data = fin.read().splitlines(True)
        with open('{0}/config.ini'.format(self.bids_dir), 'w') as fout:
            fout.writelines(data[1:])


