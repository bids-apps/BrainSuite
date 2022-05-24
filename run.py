#!/usr/local/miniconda/bin/python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import argparse
import os
import subprocess
from glob import glob
from subprocess import Popen, PIPE

from bids.grabbids import BIDSLayout
# from bin.bfp_group_compare import bfp_group_compare
from builtins import str
import shutil

from bin.brainsuiteWorkflow import subjLevelProcessing
from bin.readPreprocSpec import preProcSpec
from bin.readSpec import bssrSpec
from bin.runBssr import *
from run_rmarkdown import run_rmarkdown
from bin.runWorkflow import runWorkflow

########################################################################
### Authored by https://github.com/BIDS-Apps/HCPPipelines/blob/master/run.py

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

parser = argparse.ArgumentParser(description='BrainSuite{0} BIDS-App (T1w, dMRI, rs-fMRI)'.format(BrainsuiteVersion))
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
parser.add_argument('--participant_label', help='The label of the participant that should be analyzed. The label '
                   'corresponds to sub-<participant_label> from the BIDS spec '
                   '(so it does not include "sub-"). If this parameter is not '
                   'provided all subjects should be analyzed. Multiple '
                   'participants can be specified with a space separated list.',
                   nargs="+")
parser.add_argument('--stages', help='Processing stage to be run. Space delimited list. Default is ALL '
                                     'which does not include WEBSERVER.',
                    nargs="+",
                    choices=['CSE', 'SVREG', 'BDP', 'BFP', 'QC', 'WEBSERVER','ALL'], default='ALL')
parser.add_argument('--atlas', help='Atlas that is to be used for labeling in SVReg. '
                                    'Default atlas: BCI-DNI. Options: BSA, BCI-DNI, USCBrain.',
                    choices=['BSA', 'BCI-DNI', 'USCBrain'], default='BCI-DNI', required=False)
parser.add_argument('--analysistype', help='Group analysis type: structural (T1 or DWI)'
                                           'or functional (fMRI). Options: STRUCT, FUNC, ALL.',
                    choices=['STRUCT', 'FUNC', 'ALL'], default='ALL')
parser.add_argument('--modelspec', help='Optional. Only for group analysis level.'
                                      'Path to JSON file that contains statistical model '
                                        'specifications.',
                    required=False)
parser.add_argument('--preprocspec', help='Optional. BrainSuite preprocessing parameters.'
                                      'Path to JSON file that contains preprocessing '
                                        'specifications.',
                    required=False)
parser.add_argument('--rmarkdown', help='Optional. Executable Rmarkdown file that uses bssr for'
                                        'group analysis stage. If this argument is specified, BrainSuite '
                                        'BIDS-App will run this Rmarkdown instead of using the content '
                                        'found in modelspec.json.'
                                      'Path to R Markdown file that contains bssr analysis commands.',
                    required=False)
parser.add_argument('--singleThread', help='Turns on single-thread mode for SVReg.'
                                           'This option can be useful when machines run into issues '
                                           'with the parallel processing tool from Matlab (Parpool).',
                    action='store_true', required=False)
parser.add_argument('--cache', help='Nipype cache output folder', required=False)
parser.add_argument('--TR', help='Repetition time of MRI (in seconds).', default=2, type=int)
parser.add_argument('--fmri_task_name', help='fMRI task name to be processed during BFP. The name should only contain'
                                             'the contents after "task-". E.g., restingstate.',
                    nargs="+")
parser.add_argument('--skipBSE', help='Skips BSE stage when running CSE. Please make sure '
                                      'there are sub-ID_T1w.mask.nii.gz files in the subject folders.',
                    action='store_true', required=False)
parser.add_argument('--ignoreSubjectConsistency', help='Reduces down the BIDS validator log and '
                                                       'the associated memory needs. This is often helpful for'
                                                       'large datasets.', action='store_true', required=False)
parser.add_argument('--bidsconfig', help='Configuration of the severity of errors for BIDS validator. '
                                     'If no path is specified, a default path of .bids-validator-config.json'
                                     '(relative to the input bids directory) file is used.', nargs='?', const='',
                    required=False)
parser.add_argument('--ignore_suffix', help='Optional. Users can define which suffix to ignore in the output '
                                            'folder. E.g., if input T1w is sub-01_ses-A_acq-highres_run-01_T1w.nii.gz,'
                                            'and user would like to ignore the "acq-highres" suffix portion, then user can '
                                            'type "--ignore_suffix acq", which will render sub-01_ses-A_run-01 output '
                                            'folders.',
                    required=False)
parser.add_argument('--QCdir', help='Designate directory for QC Dashboard.', default=None)
parser.add_argument('--QCsubjList', help='For QC purposes, optional subject list (txt format, individual subject ID separated '
                                         'by new lines; subject ID without "sub-" is required (i.e. 001). This is helpful'
                                         'in displaying only the thumbnails of the queued subjects when running on clusters/'
                                         'compute nodes.', required=False,
                    default=None)
parser.add_argument('--localWebserver', help='Launch local webserver for QC.', action='store_true')
parser.add_argument('--port', help='Port number for QC webserver.', default=8080)
parser.add_argument('--bindLocalHostOnly', help='When running local web server through this app, '
                                                'the server binds to all of the IPs on the machine. '
                                                'If you would like to only bind to the local host, '
                                                'please use this flag.', action='store_true', required=False)
parser.add_argument('-v', '--version', action='version',
                    version='BrainSuite{0} Pipelines BIDS App version {1}'.format(BrainsuiteVersion, __version__))


args = parser.parse_args()
if args.ignoreSubjectConsistency == True:
    ignoreSubjectConsistency = ' --ignoreSubjectConsistency '
else:
    ignoreSubjectConsistency = ''
if args.bidsconfig:
    bidsconfig = ' --config {0} '.format(args.bidsconfig)
else:
    bidsconfig = ''
run("bids-validator " + args.bids_dir + ignoreSubjectConsistency + bidsconfig, cwd=args.output_dir)

layout = BIDSLayout(args.bids_dir)
subjects_to_analyze = []

if not os.path.exists(args.output_dir):
    os.mkdir(args.output_dir)

# only for a subset of subjects
if args.participant_label:
    subjects_to_analyze = args.participant_label
elif args.QCsubjList:
    with open(args.QCsubjList, 'r') as f:
        for line in f.readlines():
            subjects_to_analyze.append(line.rstrip().lstrip())
else:
    subject_dirs = glob(os.path.join(args.bids_dir, "sub-*"))
    subjects_to_analyze = [subject_dir.split("-")[-1] for subject_dir in subject_dirs]

assert len(subjects_to_analyze) > 0

if args.singleThread:
    thread= True
else:
    thread=False

os.environ['runJustQC'] = 'False'
if args.skipBSE:
    stages = args.stages.append('noBSE')
if ('ALL' in args.stages):
    stages = ['CSE', 'SVREG', 'BDP', 'BFP','QC']
elif ('QC' in args.stages) & (len(args.stages) ==1):
    os.environ['runJustQC'] = 'True'
else:
    stages = args.stages

if ('WEBSERVER' in stages) and (not args.localWebserver):
    if args.QCdir is None:
        sys.stdout.write('If you would like not to launch a local webserver, please provide the directory where'
                            'you would like to store the QC data using --QCdir. E.g. --QCdir /home/yeun/public_html')

runProcessing = True
if 'WEBSERVER' in stages:
    if args.bindLocalHostOnly:
        bind = '--bind 127.0.0.1'
    else:
        bind = ''
    if args.QCdir:
        parentWEBDIR =args.QCdir
        WEBDIR = os.path.join(args.QCdir, 'QC')
    else:
        parentWEBDIR = args.output_dir
        WEBDIR = os.path.join(args.output_dir, 'QC')
    print('QC thumbnails will be generated in: ', WEBDIR)
    if not os.path.exists(WEBDIR):
        os.makedirs(WEBDIR)
    cmd = 'cp -r /BrainSuite/QC/web_essentials/* {0}'.format(parentWEBDIR)
    subprocess.call(cmd, shell=True)
    cmd = 'watch.sh {0} {1} & '.format(WEBDIR, args.output_dir)
    subprocess.call(cmd, shell=True)

atlases = { 'BCI-DNI' : '/opt/BrainSuite{0}/svreg/BCI-DNI_brain_atlas/BCI-DNI_brain'.format(BrainsuiteVersion),
            'BCI' : '/opt/BrainSuite{0}/svreg/BCI-DNI_brain_atlas/BCI-DNI_brain'.format(BrainsuiteVersion),
            'BSA' : '/opt/BrainSuite{0}/svreg/BrainSuiteAtlas1/mri'.format(BrainsuiteVersion),
            'USCBrain' : '/opt/BrainSuite{0}/svreg/USCBrain/USCBrain'.format(BrainsuiteVersion)}
atlas = atlases[str(args.atlas)]

if 'BFP' in stages:
    assert args.atlas != 'BSA'

if (args.analysis_level == "participant"):

    cacheset =False
    preprocspecs = preProcSpec(args.bids_dir, args.output_dir)
    if args.preprocspec:
        preprocspecs.read_preprocfile(args.preprocspec)
        atlas = atlases[str(preprocspecs.atlas)]
        cache = preprocspecs.cache
        thread = preprocspecs.singleThread
        if preprocspecs.cache:
            cacheset = True
            args.cache = preprocspecs.cache
        configini = '{0}/config.ini'.format(args.output_dir)
    else:
        shutil.copyfile('/config.ini', '{0}/config.ini'.format(args.output_dir))
        configini = '{0}/config.ini'.format(args.output_dir)

    allt1ws = []
    for subject_label in subjects_to_analyze:

        sessions = layout.get(target='session', return_type='id',
                              subject=subject_label, type='T1w', extensions=["nii.gz","nii"])
        if len(sessions) > 0:
            for ses in range(0, len(sessions)):
                runs = layout.get(target='run', return_type='id', session=sessions[ses],
                              subject=subject_label, type='T1w', extensions=["nii.gz","nii"])
                if len(runs) > 0:
                    for r in range(0, len(runs)):
                        t1ws = [f.filename for f in layout.get(subject=subject_label, run=runs[r],
                                                               type='T1w', session=sessions[ses],
                                                               extensions=["nii.gz", "nii"])]
                else:
                    t1ws = [f.filename for f in layout.get(subject=subject_label,
                                                           type='T1w', session=sessions[ses],
                                                           extensions=["nii.gz", "nii"])]
        else:
            runs = layout.get(target='run', return_type='id',
                              subject=subject_label, type='T1w', extensions=["nii.gz", "nii"])
            if len(runs) > 0:
                for r in range(0, len(runs)):
                    t1ws = [f.filename for f in layout.get(subject=subject_label, run=runs[r],
                                                           type='T1w', extensions=["nii.gz", "nii"])]
            else:
                t1ws = [f.filename for f in layout.get(subject=subject_label,
                                                       type='T1w', extensions=["nii.gz", "nii"])]
        allt1ws.extend(t1ws)
    dataset_description = None
    if os.path.exists(args.bids_dir + '/dataset_description.json'):
        dataset_description = args.bids_dir + '/dataset_description.json'
    # preprocspecs.write_preproc_params(args.output_dir, stages, dataset_description)
    if 'WEBSERVER' in stages:
        preprocspecs.write_subjectIDsJSON(allt1ws, args, WEBDIR)
        preprocspecs.write_preproc_params(WEBDIR, stages, dataset_description)
        if not os.path.exists(WEBDIR + '/brainsuite_dashboard_config.json'):
            shutil.copyfile('/BrainSuite/QC/sample_brainsuite_dashboard_config.json', '{0}/brainsuite_dashboard_config.json'.format(WEBDIR))
        if args.localWebserver:
            print("\nOpen web browser and navigate to 'http://127.0.0.1:{0}'\n".format(args.port))
            cmd = "cd {0} && python3 -m http.server {1} {2}".format(parentWEBDIR, args.port, bind)
            subprocess.call(cmd, shell=True)


    if not 'WEBSERVER' in stages:
        for subject_label in subjects_to_analyze:
            mcrCache = os.path.join(args.output_dir, '.mcrCache/{0}.mcrCache'.format(subject_label))
            if not os.path.exists(mcrCache):
                os.makedirs(mcrCache)
            os.environ['MCR_CACHE_ROOT']= mcrCache

            sessions = layout.get(target='session', return_type='id',
                                  subject=subject_label, type='T1w', extensions=["nii.gz","nii"])

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
                                        dwis, funcs, subject_label, configini, args, layout)

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
                                dwis, funcs, subject_label, configini, args, layout)
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
                                    dwis, funcs, subject_label, configini, args, layout)
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
                            dwis, funcs, subject_label, configini, args, layout)

if args.analysis_level == "group":

    analyses = []

    if args.analysistype == "ALL":
        analyses.append('STRUCT')
        analyses.append('FUNC')
    else:
        analyses.append(args.analysistype)

    if 'STRUCT' in analyses:
        if args.rmarkdown:
            run_rmarkdown(args.rmarkdown)
        else:
            specs = bssrSpec(args.modelspec, args.output_dir)
            specs.read_modelfile(args.modelspec)
            bss_data = load_bss_data(specs)
            bss_model = run_model(specs, bss_data)
            save_bss(bss_data, bss_model, specs.out_dir)
    if 'FUNC' in analyses:
        specs = bssrSpec(args.modelspec, args.output_dir)
        specs.read_bfp_modelfile(args.modelspec)
        ## convert tsv to csv
        basename = specs.tsv_fname.split(".")[0]
        cmd = "sed 's/\t/,/g' {0}.tsv > {0}.csv".format(basename)
        # print(cmd)
        subprocess.call(cmd, shell=True)
        exec(open("{BFPpath}/src/stats/bfp_run_stat.py".format(
            BFPpath=os.environ['BFP'])).read())
