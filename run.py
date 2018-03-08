#!/opt/conda/bin/python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function
from builtins import str
import argparse
import os
import shutil
import nibabel
from glob import glob
from subprocess import Popen, PIPE, check_output
from shutil import rmtree
import subprocess
from bids.grabbids import BIDSLayout
from shutil import copyfile
from bin.brainsuiteWorkflowNoQC import runWorkflow
from bin.readSpec import *
from bin.runBssr import *

def run(command, env={}, cwd=None):
    merged_env = os.environ
    merged_env.update(env)
    merged_env.pop("DEBUG", None)
    print(command)
    process = Popen(command, stdout=PIPE, stderr=subprocess.STDOUT,
                    shell=True, env=merged_env, cwd=cwd)
    while True:
        line = process.stdout.readline()
        line = str(line)[:-1]
        print(line)
        if line == '' and process.poll() != None:
            break
    if process.returncode != 0:
        raise Exception("Non zero return code: %d"%process.returncode)


__version__ = open('/BrainSuite/version').read()

parser = argparse.ArgumentParser(description='BrainSuite18a BIDS-App (T1w, dMRI)')
parser.add_argument('bids_dir', help='The directory with the input dataset '
                    'formatted according to the BIDS standard.')
parser.add_argument('output_dir', help='The directory where the output files '
                    'should be stored. If you are running group level analysis '
                    'this folder should be prepopulated with the results of the'
                    'participant level analysis.')
parser.add_argument('analysis_level', help='Level of the analysis that will be performed. '
                    'Multiple participant level analyses can be run independently '
                    '(in parallel) using the same output_dir.',
                    choices=['participant'])
parser.add_argument('--participant_label', help='The label of the participant that should be analyzed. The label '
                   'corresponds to sub-<participant_label> from the BIDS spec '
                   '(so it does not include "sub-"). If this parameter is not '
                   'provided all subjects should be analyzed. Multiple '
                   'participants can be specified with a space separated list.',
                   nargs="+")
parser.add_argument('--stages', help='Processing stage to be run. Space delimited list.', nargs="+",
                    choices=['CSE', 'SVREG', 'BDP'], default='ALL')
parser.add_argument('--atlas', help='Atlas that is to be used for labeling in SVReg. '
                                    'Default atlas: BCI-DNI. Options: BSA, BCI, USCBrain.',
                    choices=['BSA', 'BCI', 'USCBrain'], default='BCI', required=False)
parser.add_argument('--modelspec', help='Optional. Only for group analysis level.'
                                      'Path to JSON file that contains statistical model'
                                        'specifications. ',
                    required=False)
parser.add_argument('--singleThread', help='Turns on single-thread mode for SVReg.', action='store_true', required=False)
parser.add_argument('-v', '--version', action='version',
                    version='BrainSuite18a Pipelines BIDS App version {}'.format(__version__))


args = parser.parse_args()

run("bids-validator " + args.bids_dir, cwd=args.output_dir)

layout = BIDSLayout(args.bids_dir)
subjects_to_analyze = []

if not os.path.exists(args.output_dir):
    os.mkdir(args.output_dir)

# only for a subset of subjects
if args.participant_label:
    subjects_to_analyze = args.participant_label
else:
    subject_dirs = glob(os.path.join(args.bids_dir, "sub-*"))
    subjects_to_analyze = [subject_dir.split("-")[-1] for subject_dir in subject_dirs]

if args.singleThread:
    thread= str('ON')
else:
    thread= str('OFF')

atlases = { 'BCI' : '/opt/BrainSuite18a/svreg/BCI-DNI_brain_atlas/BCI-DNI_brain',
            'BSA' : '/opt/BrainSuite18a/svreg/BrainSuiteAtlas1/mri',
            'USCBrain' : '/opt/BrainSuite18a/svreg/USCBrain/BCI-DNI_brain'}
atlas = atlases[str(args.atlas)]


if args.analysis_level == "participant":
    # check stages argument info
    if all(stage in args.stages for stage in ['CSE', 'SVREG', 'BDP']):
        stages = 'ALL'
    elif 'CSE' in args.stages and 'BDP' in args.stages:
        stages = 'BDP'
    elif 'CSE' in args.stages and 'SVREG' in args.stages:
        stages = 'SVREG'
    else:
        stages = args.stages

    print('\nWill run: {0}'.format(args.stages))
    for subject_label in subjects_to_analyze:

            sessions = layout.get(target='session', return_type='id',
                                  subject=subject_label, type='T1w', extensions=["nii.gz","nii"])

            if len(sessions) > 0:
                for ses in range(0, len(sessions)):
                    # layout._get_nearest_helper(dwi, 'bval', type='dwi')
                    t1ws = [f.filename for f in layout.get(subject=subject_label,
                                                           type='T1w', session=sessions[ses],
                                                           extensions=["nii.gz", "nii"])]
                    assert (len(t1ws) > 0), "No T1w files found for subject %s!" % subject_label

                    dwis = [f.filename for f in layout.get(subject=subject_label,
                                                           type='dwi', session=sessions[ses],
                                                           extensions=["nii.gz", "nii"])]
                    subjectID = 'sub-{0}_ses-{1}'.format(subject_label, sessions[ses])
                    outputdir = str(args.output_dir + os.sep + subjectID)
                    if not os.path.exists(outputdir):
                        os.mkdir(outputdir)
                    if (len(dwis) > 0):
                        numOfPairs = min(len(t1ws), len(dwis))
                        for i in range(0, numOfPairs):
                            bval = layout.get_bval(dwis[i])
                            bvec = layout.get_bvec(dwis[i])
                            if 'ALL' in stages:
                                runWorkflow(subjectID, t1ws[i], outputdir, args.bids_dir, BDP=dwis[i].split('.')[0],
                                            BVAL=str(bval), BVEC=str(bvec), SVREG=True, SingleThread=thread, ATLAS=str(atlas))
                            if 'CSE' in stages:
                                runWorkflow(subjectID, t1ws[i], outputdir, args.bids_dir)
                            if 'BDP' in stages:
                                runWorkflow(subjectID, t1ws[i], outputdir, args.bids_dir, BDP=dwis[i].split('.')[0],
                                            BVAL=str(bval), BVEC=str(bvec))
                            if 'SVREG' in stages:
                                runWorkflow(subjectID, t1ws[i], outputdir, args.bids_dir, SVREG=True, SingleThread=thread,
                                            ATLAS=str(atlas))
                    else:
                        for t1 in t1ws:
                            if 'ALL' in stages:
                                runWorkflow(subjectID, t1, outputdir, args.bids_dir, SVREG=True,
                                            SingleThread=thread, ATLAS=str(atlas))
                            if 'CSE' in stages:
                                runWorkflow(subjectID, t1, outputdir, args.bids_dir)
                            if 'SVREG' in stages:
                                runWorkflow(subjectID, t1, outputdir, args.bids_dir, SVREG=True,
                                            SingleThread=thread, ATLAS=str(atlas))
                            if 'BDP' in stages:
                                print('\nNo DWI data found. Running CSE only.')
                                runWorkflow(subjectID, t1, outputdir, args.bids_dir)
            else:

                t1ws = [f.filename for f in layout.get(subject=subject_label,
                                                       type='T1w', extensions=["nii.gz", "nii"])]
                assert (len(t1ws) > 0), "No T1w files found for subject %s!" % subject_label

                dwis = [f.filename for f in layout.get(subject=subject_label,
                                                       type='dwi', extensions=["nii.gz", "nii"])]
                outputdir = str(args.output_dir + os.sep + 'sub-%s' % subject_label)
                if not os.path.exists(outputdir):
                    os.mkdir(outputdir)
                if (len(dwis) > 0):
                    numOfPairs = min(len(t1ws), len(dwis))
                    for i in range(0, numOfPairs):
                        bval = layout.get_bval(dwis[i])
                        bvec = layout.get_bvec(dwis[i])
                        if 'ALL' in stages:
                            runWorkflow('sub-%s' % subject_label, t1ws[i], outputdir, args.bids_dir,
                                        BDP=dwis[i].split('.')[0], BVAL=str(bval), BVEC=str(bvec), SVREG=True,
                                        SingleThread=thread, ATLAS=str(atlas))
                        if 'CSE' in stages:
                            runWorkflow('sub-%s' % subject_label, t1ws[i], outputdir, args.bids_dir)
                        if 'BDP' in stages:
                            runWorkflow('sub-%s' % subject_label, t1ws[i], outputdir, args.bids_dir,
                                        BDP=dwis[i].split('.')[0], BVAL=str(bval), BVEC=str(bvec))
                        if 'SVREG' in stages:
                            runWorkflow('sub-%s' % subject_label, t1ws[i], outputdir, args.bids_dir,
                                        SVREG=True, SingleThread=thread, ATLAS=str(atlas))
                else:
                    for t1 in t1ws:
                        if 'ALL' in stages:
                            runWorkflow('sub-%s' % subject_label, t1, outputdir, args.bids_dir, SVREG=True,
                                        SingleThread=thread, ATLAS=(atlas))
                        if 'CSE' in stages:
                            runWorkflow('sub-%s' % subject_label, t1, outputdir, args.bids_dir)
                        if 'SVREG' in stages:
                            runWorkflow('sub-%s' % subject_label, t1, outputdir, args.bids_dir, SVREG=True,
                                        SingleThread=thread, ATLAS=(atlas))
                        if 'BDP' in stages:
                            print('\nNo DWI data found. Running CSE only.')
                            runWorkflow('sub-%s' % subject_label, t1, outputdir, args.bids_dir)

if args.analysis_level == "group":
    specs = bssrSpec(args.modelspec, args.output_dir)
    bss_data = load_bss_data(specs)
    bss_model = run_model(specs, bss_data)
    save_bss(bss_data, bss_model, specs.resultdir)



