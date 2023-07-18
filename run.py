#!/usr/local/miniconda/bin/python
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

from __future__ import unicode_literals, print_function

import os
import sys
import subprocess
from glob import glob
from subprocess import Popen, PIPE
import traceback

import warnings
warnings.filterwarnings(action='ignore', category=FutureWarning)
from bids.grabbids import BIDSLayout
from builtins import str
import shutil

from readSpecs.readPreprocSpec import preProcSpec
from workflows.runWorkflow import runWorkflow
from QC.stageNumDict import stageNumDict

########################################################################
### Adapted from https://github.com/BIDS-Apps/HCPPipelines/blob/master/run.py

def run(command, env={}, cwd=None):
    merged_env = os.environ
    merged_env.update(env)
    merged_env.pop("DEBUG", None)
    print(command)
    process = Popen(command, stdout=PIPE, stderr=subprocess.STDOUT,
                    shell=True, env=merged_env, cwd=cwd,
                    universal_newlines=True)
    while True:
        line = process.stdout.readline()
        print(line.rstrip())
        line = str(line)[:-1]
        if line == '' and process.poll() != None:
            break
    if process.returncode != 0:
        raise Exception("Non zero return code: %d"%process.returncode)

########################################################################

BFPpath= os.environ['BFP'] + '/bfp.sh'

__version__ = open('/BrainSuite/version').read()
BrainsuiteVersion = os.environ['BrainSuiteVersion']

def parser():
    import argparse

    BrainsuiteVersion = '23a'

    parser = argparse.ArgumentParser(description='BrainSuite{0} BIDS-App (T1w, dMRI, rs-fMRI). '
                                                 'Copyright (C) 2022 The Regents of the University of California '
                                                'Dept. of Neurology, David Geffen School of Medicine, UCLA.'.format(BrainsuiteVersion))
    parser.add_argument('bids_dir', help='The directory with the input dataset '
                        'formatted according to the BIDS standard.')
    parser.add_argument('output_dir', help='The directory where the output files '
                        'should be stored. If you are running group level analysis '
                        'this folder should be prepopulated with the results of the'
                        'participant level analysis.')
    parser.add_argument('analysis_level', help='Level of the analysis that will be performed. '
                        'Multiple participant level analyses can be run independently '
                        '(in parallel) using the same output_dir. The group analysis '
                        'performs group statistical analysis.',
                        choices=['participant', 'group'])

    parser.add_argument('--stages',
                        help='Participant-level processing stage to be run. Space delimited list. Default is ALL '
                             'which does not include DASHBOARD. CSE runs Cortical Surface Extractor and cortical thickness computation, '
                             'which are the initial portions of the BrainSuite Anatomical Pipeline (BAP). SVREG runs Surface-constrained '
                             'Volumetric registration, which is the latter portion of BAP. BDP runs BrainSuite Diffusion Pipeline.'
                             ' BFP runs BrainSuite Functional Pipeline. DASHBOARD runs the real-time monitoring that is required for BrainSuite '
                             'Dashboard to update real-time. However, DASHBOARD can still be run after the participant-level processing has ended to '
                             'generate the browser-based BrainSuite Dashboard.',
                        nargs="+",
                        choices=['CSE', 'SVREG', 'BDP', 'BFP', 'DASHBOARD', 'ALL'], default='ALL')
    parser.add_argument('--preprocspec', help='Optional. BrainSuite preprocessing parameters.'
                                              'Path to JSON file that contains preprocessing '
                                              'specifications.',
                        required=False)

    dataselect = parser.add_argument_group('Options for selectively running specific datasets')
    dataselect.add_argument('--participant_label', help='The label of the participant that should be analyzed. The label '
                       'corresponds to sub-<participant_label> from the BIDS spec '
                       '(so it does not include "sub-"). If this parameter is not '
                       'provided, all subjects will be analyzed. Multiple '
                       'participants can be specified with a space separated list.',
                       nargs="+")
    dataselect.add_argument('--session', help='The session label of the participant that should be analyzed. The label '
                            'corresponds to ses-<session label> from the BIDS spec (so it does not include "ses-"). If this '
                            'parameter is not provided, all sessions will be analyzed. Multiple sessions can be specified '
                            'with a space separated list.', nargs="+")

    bap = parser.add_argument_group('Command line arguments for BrainSuite Anatomical Pipeline (BAP). For more parameter '
                                    'options, please edit the preprocspecs.json file')
    bap.add_argument('--skipBSE', help='Skips BSE stage when running CSE. Please make sure '
                                          'there are sub-ID_T1w.mask.nii.gz files in the subject folders.',
                        action='store_true', required=False)
    bap.add_argument('--atlas', help='Atlas that is to be used for labeling in SVReg. '
                                        'Default atlas: BCI-DNI. Options: BSA, BCI-DNI, USCBrain.',
                        choices=['BSA', 'BCI-DNI', 'USCBrain'], default='BCI-DNI', required=False)
    bap.add_argument('--singleThread', help='Turns on single-thread mode for SVReg.'
                                               'This option can be useful when machines run into issues '
                                               'with the parallel processing tool from Matlab (Parpool).',
                        action='store_true', required=False)

    bfp = parser.add_argument_group('Command line arguments for BrainSuite Functional Pipeline (BFP). For more parameter '
                                    'options, please edit the preprocspecs.json file')
    bfp.add_argument('--TR', help='Repetition time of MRI (in seconds).', default=2, type=int)
    bfp.add_argument('--fmri_task_name',
                            help='fMRI task name to be processed during BFP. The name should only contain'
                                 'the contents after "task-". E.g., restingstate.',
                            nargs="+")
    bfp.add_argument('--ignore_suffix', help='Optional. Users can define which suffix to ignore in the output '
                                                'folder. E.g., if input T1w is sub-01_ses-A_acq-highres_run-01_T1w.nii.gz,'
                                                'and user would like to ignore the "acq-highres" suffix portion, then user can '
                                                'type "--ignore_suffix acq", which will render sub-01_ses-A_run-01 output '
                                                'folders.',
                        required=False)

    qc = parser.add_argument_group('Options for BrainSuite QC and Dashboard')
    qc.add_argument('--QCdir', help='Designate directory for QC Dashboard.', default=None)
    qc.add_argument('--QCsubjList',
                        help='For QC purposes, optional subject list (txt format, individual subject ID separated '
                             'by new lines; subject ID without "sub-" is required (i.e. 001). This is helpful'
                             'in displaying only the thumbnails of the queued subjects when running on clusters/'
                             'compute nodes.', required=False,
                        default=None)
    qc.add_argument('--localWebserver', help='Launch local webserver for QC.', action='store_true')
    qc.add_argument('--port', help='Port number for QC local webserver. This defines the port number '
                                'inside the BrainSuite BIDS App container.'
                                ' If using Singularity version of BrainSuite BIDS App, this argument also defines the port number '
                                'of the local host.', default=9095)
    qc.add_argument('--bindLocalHostOnly', help='When running local web server through this app, '
                                                    'the server binds to all of the IPs on the machine. '
                                                    'If you would like to only bind to the local host, '
                                                    'please use this flag.', action='store_true', required=False)

    group = parser.add_argument_group('Arguments and options for group-level stage. --modelspec is required for group'
                                      'mode')
    group.add_argument('--modelspec', help='Optional. Only for group analysis level.'
                                            'Path to JSON file that contains statistical model '
                                            'specifications.',
                        required=False)
    group.add_argument('--analysistype', help='Group analysis type: structural (T1 or DWI)'
                                               'or functional (fMRI). Options: STRUCT, FUNC, ALL.',
                        choices=['STRUCT', 'FUNC', 'ALL'], default='ALL')
    group.add_argument('--rmarkdown', help='Optional. Executable Rmarkdown file that uses bstr for'
                                            'group analysis stage. If this argument is specified, BrainSuite '
                                            'BIDS-App will run this Rmarkdown instead of using the content '
                                            'found in modelspec.json.'
                                            'Path to R Markdown file that contains bstr analysis commands.',
                        required=False)

    bidsval = parser.add_argument_group('Options for bids-validator')
    bidsval.add_argument('--ignoreSubjectConsistency', help='Reduces down the BIDS validator log and '
                                                           'the associated memory needs. This is often helpful for'
                                                           'large datasets.', action='store_true', required=False)
    bidsval.add_argument('--bidsconfig', help='Configuration of the severity of errors for BIDS validator. If this argument is used with no path specification, '
                                             ' the bids-validator checks for a .bids-validator-config.json file at the top level of '
                                             ' the input BIDS directory.  However, if you would like to define the path of your '
                                             '.bids-validator-config.json file, then you can specify the path after this flag (i.e. --bidsconfig /path/to/file). '  
                                             'For more information '
                                             'on how to create this JSON file, please visit https://github.com/bids-standard/bids-validator#configuration.', nargs='?',
                        const='',
                        required=False)

    parser.add_argument_group('Miscellaneous options')
    parser.add_argument('--cache', help='Nipype cache output folder.', required=False)
    parser.add_argument('--ncpus', help='Number of cpus allocated for running subject-level processing.', required=False,
                        default=2)
    parser.add_argument('--maxmem', help='Maximum memory (in GB) that can be used at once.',
                        required=False,
                        default=16)
    parser.add_argument('-v', '--version', action='version',
                        version='BrainSuite{0} Pipelines BIDS App version {1}'.format(BrainsuiteVersion,BrainsuiteVersion))


    return parser

def main():
    args = parser().parse_args()
    
    # Configure bids validator args then run bids-validator
    ignoreSubjectConsistency = ''
    bidsconfig = ''
    if args.ignoreSubjectConsistency:
        ignoreSubjectConsistency = ' --ignoreSubjectConsistency '
    if args.bidsconfig:
        bidsconfig = ' --config {0} '.format(args.bidsconfig) 
    if not os.path.exists(args.output_dir):
        os.mkdir(args.output_dir)
    run("bids-validator " + args.bids_dir + ignoreSubjectConsistency + bidsconfig, cwd=args.output_dir)

    layout = BIDSLayout(args.bids_dir)
    subjects_to_analyze = []

    # Determine which subjects to run or QC
    if args.participant_label:
        subjects_to_analyze = args.participant_label
    elif args.QCsubjList:
        with open(args.QCsubjList, 'r') as f:
            for line in f.readlines():
                subjects_to_analyze.append(line.rstrip().lstrip())
    else:
        subject_dirs = glob(os.path.join(args.bids_dir, "sub-*"))
        subjects_to_analyze = [subject_dir.split("-")[-1] for subject_dir in subject_dirs]

    # Check to make sure there are valid subjects
    assert len(subjects_to_analyze) > 0

    # Grab single thread option for svreg (cli flags overwrites preprocspec file params)
    thread=False
    if args.singleThread:
        thread= True        

    # set variables for nipype multiproc plugin resources and total num for stages
    os.environ['NCPUS'] = str(args.ncpus)
    os.environ['MAXMEM'] = str(args.maxmem)
    os.environ["numstages"] = str(len(stageNumDict))
    stages = args.stages

    if ('ALL' in args.stages):
        stages = ['CSE', 'SVREG', 'BDP', 'BFP','QC']
    if args.skipBSE:
        stages.append('noBSE')
    if 'DASHBOARD' in stages and len(stages) > 1:
        sys.stdout.write('************ ERROR!!! ************\n'
                         'Dashboard must be run alone separately (i.e. --stages DASHBOARD).\n'
                         'Please start another BrainSuite BIDS App to run participant-level processing (i.e. --stages CSE BDP SVREG BFP).\n')
        sys.exit(2)

    if ('DASHBOARD' in stages) and (not args.localWebserver):
        if args.QCdir is None:
            sys.stdout.write('If you would like not to launch a local webserver, please provide the directory where'
                                'you would like to store the QC data using --QCdir. E.g. --QCdir /home/yeun/public_html')
            sys.exit(2)

    if 'DASHBOARD' in stages:
        bind = ''
        if args.bindLocalHostOnly:
            bind = '--bind 127.0.0.1'
        # create web and qc directories
        if args.QCdir:
            parentWEBDIR =args.QCdir
            WEBDIR = os.path.join(args.QCdir, 'QC')
        else:
            parentWEBDIR = args.output_dir
            WEBDIR = os.path.join(args.output_dir, 'QC')
        print('QC thumbnails will be generated in: ', WEBDIR)
        if not os.path.exists(WEBDIR):
            os.makedirs(WEBDIR)
        # copy web essentials files over to the web directory
        cmd = 'cp -r /BrainSuite/QC/web_essentials/* {0}'.format(parentWEBDIR)
        subprocess.call(cmd, shell=True)

    # set atlas for svreg. if bfp is selected to run, atlas cannot be bsa
    atlases = { 'BCI-DNI' : '/opt/BrainSuite{0}/svreg/BCI-DNI_brain_atlas/BCI-DNI_brain'.format(BrainsuiteVersion),
                'BCI' : '/opt/BrainSuite{0}/svreg/BCI-DNI_brain_atlas/BCI-DNI_brain'.format(BrainsuiteVersion),
                'BSA' : '/opt/BrainSuite{0}/svreg/BrainSuiteAtlas1/mri'.format(BrainsuiteVersion),
                'USCBrain' : '/opt/BrainSuite{0}/svreg/USCBrain/USCBrain'.format(BrainsuiteVersion)}
    atlas = atlases[str(args.atlas)]

    if 'BFP' in stages:
        assert args.atlas != 'BSA'

    if args.session:
        print("Running only session: ", args.session)

    if (args.analysis_level == "participant"):

        cacheset =False
        # initialize preprocessing parameters
        preprocspecs = preProcSpec(args.bids_dir, args.output_dir)
        # pre-grab subject IDs and write necessary sidecar files
        allt1ws = []
        for subject_label in subjects_to_analyze:

            if args.session:
                t1ws = [f.filename for f in layout.get(subject=subject_label, session=args.session,
                                                   type='T1w', extensions=["nii.gz", "nii"])]
            else:
                t1ws = [f.filename for f in layout.get(subject=subject_label,
                                                   type='T1w', extensions=["nii.gz", "nii"])]

            for t1w in t1ws:
                subjectID = t1w.split('/')[-1].split('_T1w')[0]
                if not os.path.exists('{0}/{1}/'.format(args.output_dir, subjectID)):
                    os.makedirs('{0}/{1}/'.format(args.output_dir, subjectID))
                if args.preprocspec:
                    preprocspecs.read_preprocfile(args.preprocspec, subjectID)
                    atlas = atlases[str(preprocspecs.atlas)]
                    thread = preprocspecs.singleThread
                    if preprocspecs.cache:
                        cacheset = True
                        args.cache = preprocspecs.cache
            allt1ws.extend(t1ws)
        dataset_description = None
        if os.path.exists(args.bids_dir + '/dataset_description.json'):
            dataset_description = args.bids_dir + '/dataset_description.json'
        if 'DASHBOARD' in stages:
            # write subjectIDs json file which will be read by watch.sh to monitor these subjects
            preprocspecs.write_subjectIDsJSON(allt1ws, args, WEBDIR)
            preprocspecs.write_preproc_params(WEBDIR, stages, dataset_description)
            if not os.path.exists(WEBDIR + '/brainsuite_dashboard_config.json'):
                shutil.copyfile('/BrainSuite/templates/sample_brainsuite_dashboard_config.json', '{0}/brainsuite_dashboard_config.json'.format(WEBDIR))
            # now launch monitoring
            if args.localWebserver:
                # if web server is selected to launch, then run watch.sh in the background with pid echoed
                cmd = 'watch.sh {0} {1} & echo $!'.format(WEBDIR, args.output_dir)
                subprocess.call(cmd, shell=True)
                # run python's web server
                print("\nOpen web browser and navigate to 'http://127.0.0.1:{0}' . If you have changed the port number while "
                     "calling the docker images, please make sure that port number you have defined matches this web address.\n".format(args.port))
                cmd = "cd {0} && python3 -m http.server {1} {2}".format(parentWEBDIR, args.port, bind)
                subprocess.call(cmd, shell=True)
            else:
                cmd = 'watch.sh {0} {1} '.format(WEBDIR, args.output_dir)
                subprocess.call(cmd, shell=True)
            


        elif not 'DASHBOARD' in stages:
            # qc is automatically added into the stages for now
            if 'QC' not in stages:
                stages.append('QC')
            for subject_label in subjects_to_analyze:
                mcrCache = os.path.join(args.output_dir, '.mcrCache/{0}.mcrCache'.format(subject_label))
                if not os.path.exists(mcrCache):
                    os.makedirs(mcrCache)
                os.environ['MCR_CACHE_ROOT']= mcrCache

                sessions = layout.get(target='session', return_type='id',
                                      subject=subject_label, type='T1w', extensions=["nii.gz","nii"])
                if args.session:
                    sessions = args.session
                # determine which files to run the runWorkflow
                if len(sessions) > 0:                    
                    for ses in range(0, len(sessions)):
                        runs = layout.get(target='run', return_type='id', session=sessions[ses],
                                      subject=subject_label, type='T1w', extensions=["nii.gz","nii"])
                        if len(runs) > 0:
                            for r in range(0, len(runs)):
                                t1ws = [f.filename for f in layout.get(subject=subject_label, run=runs[r],
                                                                       type='T1w', session=sessions[ses],
                                                                       extensions=["nii.gz", "nii"])]
                                dwis = [f.filename for f in layout.get(subject=subject_label, run=runs[r],
                                                                       type='dwi', session=sessions[ses],
                                                                       extensions=["nii.gz", "nii"])]
                                funcs = [f.filename for f in layout.get(subject=subject_label, run=runs[r],
                                                                        type='bold', session=sessions[ses],
                                                                        extensions=["nii.gz", "nii"])]
                                runWorkflow(stages, t1ws, preprocspecs, atlas, cacheset, thread, layout,
                                            dwis, funcs, subject_label, args)

                        else:
                            t1ws = [f.filename for f in layout.get(subject=subject_label,
                                                                   type='T1w', session=sessions[ses],
                                                                   extensions=["nii.gz", "nii"])]
                            dwis = [f.filename for f in layout.get(subject=subject_label,
                                                                   type='dwi', session=sessions[ses],
                                                                   extensions=["nii.gz", "nii"])]
                            funcs = [f.filename for f in layout.get(subject=subject_label,
                                                                    type='bold', session=sessions[ses],
                                                                    extensions=["nii.gz", "nii"])]
                            runWorkflow(stages, t1ws, preprocspecs, atlas, cacheset, thread, layout,
                                    dwis, funcs, subject_label, args)
                else:
                    runs = layout.get(target='run', return_type='id',
                                      subject=subject_label, type='T1w', extensions=["nii.gz", "nii"])
                    if len(runs) > 0:
                        for r in range(0, len(runs)):
                            t1ws = [f.filename for f in layout.get(subject=subject_label, run=runs[r],
                                                                   type='T1w',
                                                                   extensions=["nii.gz", "nii"])]
                            dwis = [f.filename for f in layout.get(subject=subject_label, run=runs[r],
                                                                   type='dwi',
                                                                   extensions=["nii.gz", "nii"])]
                            funcs = [f.filename for f in layout.get(subject=subject_label, run=runs[r],
                                                                    type='bold',
                                                                    extensions=["nii.gz", "nii"])]
                            runWorkflow(stages, t1ws, preprocspecs, atlas, cacheset, thread, layout,
                                        dwis, funcs, subject_label, args)
                    else:
                        t1ws = [f.filename for f in layout.get(subject=subject_label,
                                                               type='T1w', extensions=["nii.gz", "nii"])]
                        # assert (len(t1ws) > 0), "No T1w files found for subject %s!" % subject_label

                        dwis = [f.filename for f in layout.get(subject=subject_label,
                                                               type='dwi', extensions=["nii.gz", "nii"])]

                        funcs = [f.filename for f in layout.get(subject=subject_label,
                                                                type='bold',
                                                                extensions=["nii.gz", "nii"])]
                        runWorkflow(stages, t1ws, preprocspecs, atlas, cacheset, thread, layout,
                                dwis, funcs, subject_label, args)

    if args.analysis_level == "group":
        from readSpecs.readModelSpec import bstrSpec
        from workflows.runBstr import load_bstr_data, run_model, save_bstr
        from run_rmarkdown import run_rmarkdown
        from datetime import datetime
        import json
        
        analyses = []

        if args.analysistype == "ALL":
            analyses.append('STRUCT')
            analyses.append('FUNC')
        else:
            analyses.append(args.analysistype)
        # read model spec file
        if not args.modelspec:
            sys.stdout.write('************ ERROR!!! ************ \n'
                            'A model specification JSON file is required to run group analyses.\n'
                             'For information on how to create this file, please visit brainsuite.org/BIDS/modgroup.html.\n')
            sys.exit(2)
        specs = bstrSpec(args.modelspec, args.output_dir)
        
        if 'STRUCT' in analyses:
            CT = datetime.now()
            CTstring = 'Y{0}M{1}D{2}H{3}M{4}S{5}ms{6}'.format(CT.year,CT.month,CT.day,CT.hour, CT.minute,CT.second,CT.microsecond)
            structStatsDir = specs.specs['BrainSuite']['Structural']['out_dir']
            if not os.path.exists(structStatsDir):
                os.mkdir(structStatsDir)
            specs_out = os.path.join(structStatsDir, 'modelspec_struct_analysis_{0}.json'.format(CTstring))
            try:
                if args.rmarkdown:
                    run_rmarkdown(args.rmarkdown)
                else:
                    # read structural analysis model specs
                    specs.read_struct_modelfile()
                    # load in appropriate output data
                    bstr_data = load_bstr_data(specs)
                    # run statistical model
                    bstr_model = run_model(specs, bstr_data)
                    # save out results
                    save_bstr(bstr_data, bstr_model, specs.out_dir)
                specs.specs['BrainSuite']['Structural']['run_success']='True'
                with open(specs_out, 'w') as f:
                    json.dump(specs.specs['BrainSuite']['Structural'], f)
            except Exception as e:
                specs.specs['BrainSuite']['Structural']['run_success']='False'
                exceptionType, exception, tb = sys.exc_info()
                tb_msg = ' '.join(traceback.format_tb(tb))
                specs.specs['BrainSuite']['Structural']['ErrorInfo']= {'ErrorType': str(exceptionType),
                                                                 'ErrorMsg': str(exception),
                                                                 'TraceBack': tb_msg}
                with open(specs_out, 'w') as f:
                    json.dump(specs.specs['BrainSuite']['Structural'], f)
                raise e
                
        if 'FUNC' in analyses:
            CT = datetime.now()
            CTstring = 'Y{0}M{1}D{2}H{3}M{4}S{5}ms{6}'.format(CT.year,CT.month,CT.day,CT.hour, CT.minute,CT.second,CT.microsecond)
            funcStatsDir = specs.specs['BrainSuite']['Functional']['out_dir']
            if not os.path.exists(funcStatsDir):
                os.mkdir(funcStatsDir)
            specs_out = os.path.join(funcStatsDir, 'modelspec_func_analysis_{0}.json'.format(CTstring))
            try:
                # read functional analysis model specs
                specs.read_func_modelfile()
                ## convert tsv to csv for fc analyses
                basename = specs.tsv_fname.split(".")[0]
                cmd = "sed 's/\t/,/g' {0}.tsv > {0}.csv".format(basename)
                subprocess.call(cmd, shell=True)
                # run fc statistical models
                exec(open("{BFPpath}/src/stats/bfp_run_stat.py".format(
                    BFPpath=os.environ['BFP'])).read())
                specs.specs['BrainSuite']['Functional']['run_success']='True'
                with open(specs_out, 'w') as f:
                    json.dump(specs.specs['BrainSuite']['Functional'], f)
            except Exception as e:
                specs.specs['BrainSuite']['Functional']['run_success']='False'
                exceptionType, exception, tb = sys.exc_info()
                tb_msg = ' '.join(traceback.format_tb(tb))
                specs.specs['BrainSuite']['Functional']['ErrorInfo']= {'ErrorType': str(exceptionType),
                                                                 'ErrorMsg': str(exception),
                                                                 'TraceBack': tb_msg}
                with open(specs_out, 'w') as f:
                    json.dump(specs.specs['BrainSuite']['Functional'], f)
                raise e

if __name__ == '__main__':
    main()
