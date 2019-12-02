#!/opt/conda/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import json
import configparser

class preProcSpec(object):

    def __init__(self, preprocfile):
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

        config = configparser.ConfigParser()
        config.read('/config.ini')

        ## edit config file
        config.set('CONTINUERUN', str(self.continuerun))
        config.set('MultiThreading', str(self.multithread))
        config.set('EnabletNLMPdfFiltering', str(self.tnlmpdf))
        config.set('fpr', str(self.fpr))
        config.set('FSLOUTPUTTYPE', str(self.fslotype))
        config.set('FWHM', str(self.fwhm))
        config.set('HIGHPASS', str(self.highpass))
        config.set('LOWPASS', str(self.lowpass))
        config.set('memory', str(self.memory))
        config.set('EnableShapeMeasures', str(self.shape))
        config.set('T1SpaceProcessing', str(self.t1space))
        config.set('FSLRigid', str(self.fslrigid))
        config.set('SimRef', str(self.simref))
        config.set('RunDetrend', str(self.rundetrend))
        config.set('RunNSR', str(self.runnsr))

        with open('/config.ini', 'wb') as configfile:
            config.write(configfile)




