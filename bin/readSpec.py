#!/opt/conda/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import json

class bssrSpec(object):

    def __init__(self, modelfile, outputdir):
        self.outputdir = outputdir
        # self.session = ''
        self.tsv = ''
        self.subjects = []
        # self.dependent_variable = ''
        # self.model = ''
        # self.explanatory_variable = ''
        self.measure = ''
        self.test = ''
        # self.full_model = ''
        # self.null_model = ''
        self.main_effect = ''
        self.corr_var = ''
        self.group_var =''
        self.paired = ''
        self.mult_comp = ''
        self.roi = []
        self.smooth = ''
        self.hemi =''
        self.maskfile = ''
        self.atlas = ''
        self.roimeas = ''
        self.dbmmeas = ''
        self.resultdir=''

        self.read_success = True
        self.read_modelfile(modelfile)

        if self.read_success == False:
            return

        # self.create_subjectList()

    def read_modelfile(self, modelfile):
        if not os.path.isfile(modelfile):
            sys.stdout.write('Model specification file not found.\n')
            self.read_success = False
            return

        try:
            specs = json.load(open(modelfile))
        except:
            sys.stdout.writable("There was an error reading the model specification file."
                                "\nPlease check that the format of the file is JSON.")
            return

        # self.session = specs['level']
        self.tsv = os.path.join(self.outputdir, specs['BrainSuite']['tsv'])
        self.test = specs['BrainSuite']['test']
        # self.full_model = specs['full_model']
        # self.null_model = specs['null_model']
        self.mult_comp = specs['BrainSuite']['mult_comp']
        self.measure = specs['BrainSuite']['measure']
        self.main_effect = specs['BrainSuite']['main_effect']
        self.covariates = ['"' + item + '"' for item in specs['BrainSuite']['covariates']]
        self.corr_var = specs['BrainSuite']['corr_var']
        self.group_var = specs['BrainSuite']['group_var']
        self.paired = specs['BrainSuite']['paired']
        self.smooth = specs['BrainSuite']['smooth']
        self.roi = ['"' + item + '"' for item in specs['BrainSuite']['roiid']]
        self.hemi = specs['BrainSuite']['hemi']
        self.maskfile = specs['BrainSuite']['maskfile']
        self.atlas = specs['BrainSuite']['atlas']
        self.roimeas = specs['BrainSuite']['roimeas']
        self.dbmmeas = specs['BrainSuite']['dbmmeas']
        self.resultdir = specs['BrainSuite']['results']

    # def create_subjectList(self):
        # if self.session:
        #     subjects = []
        #     for fname in os.listdir(self.outputdir):
        #         path = os.path.join(self.outputdir, fname)
        #         if os.path.isdir(path) and "ses-{0}".format(self.session) in fname:
        #             subjects.append(path)


