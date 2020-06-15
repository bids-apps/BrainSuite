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
        self.sessionid = ''
        self.ndim = ''
        self.numtimepoints = ''
        self.filtered = False
        self.fileext = ''
        self.resultdir = ''
        self.controls = ''
        self.exclude = ''
        self.GOfolder = ''
        self.statsdir = os.path.join(outputdir, 'stats')
        self.sig_alpha = 0.05
        self.matcht = True

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
        self.test = specs['BrainSuite']['Structural']['test']
        # self.full_model = specs['full_model']
        # self.null_model = specs['null_model']

        self.mult_comp = specs['BrainSuite']['Structural']['mult_comp']
        self.measure = specs['BrainSuite']['Structural']['measure']
        self.main_effect = specs['BrainSuite']['Structural']['main_effect']
        # self.covariates = ['"' + item + '"' for item in specs['BrainSuite']['covariates']]
        self.corr_var = specs['BrainSuite']['Structural']['corr_var']
        self.covariates = specs['BrainSuite']['Structural']['covariates']
        self.group_var = specs['BrainSuite']['Structural']['group_var']
        self.paired = specs['BrainSuite']['Structural']['paired']
        self.smooth = specs['BrainSuite']['Structural']['smooth']
        # self.roi = ['"' + str(item) + '"' for item in specs['BrainSuite']['roiid']]
        self.roi = specs['BrainSuite']['Structural']['roiid'] # bssr roi read in list
        self.hemi = specs['BrainSuite']['Structural']['hemi']
        self.maskfile = specs['BrainSuite']['Structural']['maskfile']
        self.atlas = specs['BrainSuite']['Structural']['atlas']
        self.roimeas = specs['BrainSuite']['Structural']['roimeas']
        self.dbmmeas = specs['BrainSuite']['Structural']['dbmmeas']

        ## make bfp stats separate
        self.bfptest = specs['BrainSuite']['Functional']['test']
        self.groups = specs['BrainSuite']['Functional']['groups']
        self.exclude = specs['BrainSuite']['Functional']['exclude']
        self.ndim = specs['BrainSuite']['Functional']['ndim']
        # self.numtimepoints = specs['BrainSuite']['Functional']['num_timempoints']
        self.sessionid = "task-" + specs['BrainSuite']['Functional']['session_id']
        self.lentime = specs['BrainSuite']['Functional']['lentime']
        self.filtered = specs['BrainSuite']['Functional']['filtered']
        self.GOfolder = specs['BrainSuite']['Functional']['GOfolder']
        self.outname = specs['BrainSuite']['Functional']['outname']
        self.smooth_iter = specs['BrainSuite']['Functional']['smooth_iter']
        self.save_surfaces = specs['BrainSuite']['Functional']['save_surfaces']
        self.save_figures = specs['BrainSuite']['Functional']['save_figures']
        self.atlas_groupsync = specs['BrainSuite']['Functional']['atlas_groupsync']
        self.atlas_fname = specs['BrainSuite']['Functional']['atlas_fname']
        self.test_all = specs['BrainSuite']['Functional']['test_all']
        self.main = specs['BrainSuite']['Functional']['main']
        self.reg1 = specs['BrainSuite']['Functional']['reg1']
        self.reg2 = specs['BrainSuite']['Functional']['reg2']
        self.atlas = specs['BrainSuite']['Functional']['atlas']
        # self.sig_alpha = specs['BrainSuite']['Functional']['sig_alpha']


        self.resultdir = specs['BrainSuite']['results']


        ## TODO: add parameters for fmri group analysis

        if self.filtered == 'True':
            self.fileext = '_{0}_bold.32k.GOrd.filt.mat'.format(self.sessionid)
        elif self.filtered == 'False':
            self.fileext = '_{0}_bold.32k.GOrd.mat'.format(self.sessionid)
    # def create_subjectList(self):
        # if self.session:
        #     subjects = []
        #     for fname in os.listdir(self.outputdir):
        #         path = os.path.join(self.outputdir, fname)
        #         if os.path.isdir(path) and "ses-{0}".format(self.session) in fname:
        #             subjects.append(path)


