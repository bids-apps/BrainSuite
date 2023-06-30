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

class bstrSpec(object):

    def __init__(self, modelfile, outputdir):
        self.outputdir = outputdir
        
        if not os.path.isfile(modelfile):
            sys.stdout.write('##############################################\n'
                            '************ ERROR!!! ************ \n'
                            'Model specification file {0} not found.\n'
                             'If running Docker-based BrainSuite BIDS App, '
                             'please make sure that the path follows the filesystem of the container.\n'.format(modelfile)
                             )
            sys.exit(2)

        try:
            self.specs = json.load(open(modelfile))
        except SyntaxError as e:
            raise Exception('##############################################\n'
                            '************ ERROR!!! ************ \n'
                            "There was an error reading the model specification file."
                                "\nPlease check that the format of the file is JSON.") from e


    def read_struct_modelfile(self):

        self.tsv = self.specs['BrainSuite']['Structural']['tsv_fname']
        self.test = self.specs['BrainSuite']['Structural']['test']
        self.mult_comp = self.specs['BrainSuite']['Structural']['mult_comp']
        self.niter = self.specs['BrainSuite']['Structural']['niter']
        self.measure = self.specs['BrainSuite']['Structural']['measure']
        self.main_effect = self.specs['BrainSuite']['Structural']['main_effect']
        self.corr_var = self.specs['BrainSuite']['Structural']['corr_var']
        self.covariates = self.specs['BrainSuite']['Structural']['covariates']
        self.group_var = self.specs['BrainSuite']['Structural']['group_var']
        self.paired = bool(self.specs['BrainSuite']['Structural']['paired'])
        self.smooth = self.specs['BrainSuite']['Structural']['smooth']
        self.roi = self.specs['BrainSuite']['Structural']['roiid'] 
        self.hemi = self.specs['BrainSuite']['Structural']['hemi']
        self.maskfile = self.specs['BrainSuite']['Structural']['maskfile']
        self.atlas = self.specs['BrainSuite']['Structural']['atlas']
        self.roimeas = self.specs['BrainSuite']['Structural']['roimeas']
        self.dbameas = self.specs['BrainSuite']['Structural']['dbameas']
        self.out_dir = self.specs['BrainSuite']['Structural']['out_dir']
        self.exclude_col = self.specs['BrainSuite']['Structural']['exclude_col']
        self.pvalue = self.specs['BrainSuite']['Structural']['pvalue']



    def read_func_modelfile(self):

        self.file_ext = self.specs['BrainSuite']['Functional']['file_ext']
        self.lentime = self.specs['BrainSuite']['Functional']['lentime']
        self.matchT= str(bool(self.specs['BrainSuite']['Functional']['matchT']))
        self.stat_test = self.specs['BrainSuite']['Functional']['stat_test']
        self.bfp_out_dir= self.specs['BrainSuite']['Functional']['out_dir']
        self.outname = self.specs['BrainSuite']['Functional']['outname']
        self.smooth_iter= self.specs['BrainSuite']['Functional']['smooth_iter']
        self.save_surfaces = str(bool(self.specs['BrainSuite']['Functional']['save_surfaces']))
        self.save_figures = str(bool(self.specs['BrainSuite']['Functional']['save_figures']))
        self.sig_alpha= self.specs['BrainSuite']['Functional']['sig_alpha']
        self.atlas_groupsync = str(bool(self.specs['BrainSuite']['Functional']['atlas_groupsync']))
        self.atlas_fname = self.specs['BrainSuite']['Functional']['atlas_fname']
        self.test_all = str(bool(self.specs['BrainSuite']['Functional']['test_all']))
        self.tsv_fname = self.specs['BrainSuite']['Functional']['tsv_fname']
        self.colvar_main = self.specs['BrainSuite']['Functional']['colvar_main']
        self.colvar_reg1 = self.specs['BrainSuite']['Functional']['colvar_reg1']
        self.colvar_reg2 = self.specs['BrainSuite']['Functional']['colvar_reg2']
        self.colvar_exclude = self.specs['BrainSuite']['Functional']['colvar_exclude']
        self.colvar_atlas = self.specs['BrainSuite']['Functional']['colvar_atlas']
        self.pw_pairs = self.specs['BrainSuite']['Functional']['pw_pairs']
        self.pw_fdr = str(bool(self.specs['BrainSuite']['Functional']['pw_fdr']))
        self.pw_perm =self.specs['BrainSuite']['Functional']['pw_perm']


        config = configparser.ConfigParser()
        config.read('/bfp_config_stats.ini')
        config.set('inputs', 'file_ext', str(self.file_ext))
        config.set('inputs', 'data_dir', str(self.outputdir))
        config.set('inputs', 'lentime', str(self.lentime))
        config.set('inputs', 'matchT', str(self.matchT))
        config.set('inputs', 'stat_test', str(self.stat_test))
        config.set('pairwise testing', 'pw_pairs', str(self.pw_pairs))
        config.set('pairwise testing', 'pw_fdr', str(self.pw_fdr))
        config.set('pairwise testing', 'pw_perm', str(self.pw_perm))
        config.set('outputs', 'out_dir', str(self.bfp_out_dir))
        config.set('outputs', 'outname', str(self.outname))
        config.set('outputs', 'smooth_iter', str(self.smooth_iter))
        config.set('outputs', 'save_surfaces', str(self.save_surfaces))
        config.set('outputs', 'save_figures', str(self.save_figures))
        config.set('outputs', 'sig_alpha', str(self.sig_alpha))
        config.set('parameters', 'atlas_groupsync', str(self.atlas_groupsync))
        config.set('parameters', 'atlas_fname', str(self.atlas_fname))
        config.set('outputs', 'test_all', str(self.test_all))
        config.set('demographics', 'csv_fname', str(self.tsv_fname.split('.')[0]+'.csv'))
        config.set('demographics', 'colvar_main', str(self.colvar_main))
        config.set('demographics', 'colvar_reg1', str(self.colvar_reg1))
        config.set('demographics', 'colvar_reg2', str(self.colvar_reg2))
        config.set('demographics', 'colvar_exclude', str(self.colvar_exclude))
        config.set('demographics', 'colvar_atlas', str(self.colvar_atlas))

        os.environ['CONFIG_FILE'] = '{0}/bfp_config_stats.ini'.format(self.outputdir)
        with open('{0}/bfp_config_stats.ini'.format(self.outputdir), 'w') as configfile:
            config.write(configfile)



