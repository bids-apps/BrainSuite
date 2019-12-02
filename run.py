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
from bin.bfp import bfp
from bin.readPreprocSpec import preProcSpec
from bin.readSpec import bssrSpec
from bin.groupDiff import runGroupDiff
from bin.bfp_linear_regr import bfp_linear_regr
from bin.bfp_linear_regr_pairwise import bfp_linear_regr_pairwise
from bin.bfp_group_compare import bfp_group_compare
from rpy2.robjects.packages import importr
import rpy2.robjects as ro
from run_rmarkdown import run_rmarkdown
import os


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

BFPpath= os.environ['BFP'] + '/bfp.sh'
def run_bfp(**args):
    args.update(os.environ)
    cmd = '{BFPpath} ' + \
        "{t1} " + \
        "{func} " + \
        "{studydir} " + \
        "{subjID} " + \
        "{sess} " + \
        "{TR} " + \
        "{cache} "
    cmd = cmd.format(**args)
    run(cmd, cwd=args['studydir'])

__version__ = open('/BrainSuite/version').read()
BrainsuiteVersion = os.environ['BrainSuiteVersion']

parser = argparse.ArgumentParser(description='BrainSuite{0} BIDS-App (T1w, dMRI)'.format(BrainsuiteVersion))
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
parser.add_argument('--stages', help='Processing stage to be run. Space delimited list.', nargs="+",
                    choices=['CSE', 'SVREG', 'BDP', 'BFP', 'ALL'], default='ALL')
parser.add_argument('--atlas', help='Atlas that is to be used for labeling in SVReg. '
                                    'Default atlas: BCI-DNI. Options: BSA, BCI, USCBrain.',
                    choices=['BSA', 'BCI', 'USCBrain'], default='BCI', required=False)
parser.add_argument('--analysistype', help='Group analysis type: structural (T1 or DWI)'
                                           'or functional (fMRI). Options: anat, func, all.',
                    choices=['ANAT', 'FUNC', 'ALL'], default='ALL')
parser.add_argument('--modelspec', help='Optional. Only for group analysis level.'
                                      'Path to JSON file that contains statistical model'
                                        'specifications. ',
                    required=False)
parser.add_argument('--preprocspec', help='Optional. BrainSuite preprocessing parameters.'
                                      'Path to JSON file that contains preprocessing'
                                        'specifications. ',
                    required=False)
parser.add_argument('--rmarkdown', help='Optional. Executable Rmarkdown file that uses bssr for'
                                        'group analysis stage.'
                                      'Path to Rmarkdown file that contains bssr analysis commands. ',
                    required=False)
parser.add_argument('--singleThread', help='Turns on single-thread mode for SVReg.', action='store_true', required=False)
parser.add_argument('--cache', help='Nipype cache output folder', required=False)
parser.add_argument('--TR', help='Repetition time of MRI', default='2')
parser.add_argument('-v', '--version', action='version',
                    version='BrainSuite{0} Pipelines BIDS App version {1}'.format(BrainsuiteVersion, __version__))


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

atlases = { 'BCI' : '/opt/BrainSuite{0}/svreg/BCI-DNI_brain_atlas/BCI-DNI_brain'.format(BrainsuiteVersion),
            'BSA' : '/opt/BrainSuite{0}/svreg/BrainSuiteAtlas1/mri'.format(BrainsuiteVersion),
            'USCBrain' : '/opt/BrainSuite{0}/svreg/USCBrain/BCI-DNI_brain'.format(BrainsuiteVersion)}
atlas = atlases[str(args.atlas)]

if args.cache:
    cache = args.cache

if args.analysis_level == "participant":
    # check stages argument info
    if all(stage in args.stages for stage in ['CSE', 'SVREG', 'BDP', 'BFP']):
        stages = 'ALL'
    elif 'CSE' in args.stages and 'BDP' in args.stages:
        stages = 'BDP'
    elif 'CSE' in args.stages and 'SVREG' in args.stages:
        stages = 'SVREG'
    else:
        stages = args.stages

    cacheset =False
    if args.preprocspec:
        preprocspecs = preProcSpec(args.preprocspec)
        atlas = atlases[str(preprocspecs.atlas)]
        cache = preprocspecs.cache
        thread = preprocspecs.singleThread
        cacheset = True

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
                    funcs = [f.filename for f in layout.get(subject=subject_label,
                                                            type='bold', session=sessions[ses],
                                                            extensions=["nii.gz", "nii"])]


                    subjectID = 'sub-{0}_ses-{1}'.format(subject_label, sessions[ses])
                    outputdir = os.path.join(args.output_dir, subjectID, 'anat') # str(args.output_dir + os.sep + subjectID + os.sep + 'anat')
                    if not cacheset:
                        cache = outputdir
                    if not os.path.exists(outputdir):
                        os.makedirs(outputdir)
                    if (len(dwis) > 0):
                        numOfPairs = min(len(t1ws), len(dwis))
                        for i in range(0, numOfPairs):
                            bval = layout.get_bval(dwis[i])
                            bvec = layout.get_bvec(dwis[i])
                            if 'ALL' in stages:
                                runWorkflow(subjectID, t1ws[i], outputdir, BDP=dwis[i].split('.')[0],
                                            BVAL=str(bval), BVEC=str(bvec), SVREG=True, SingleThread=thread,
                                            ATLAS=str(atlas), CACHE=cache)
                            if 'CSE' in stages:
                                runWorkflow(subjectID, t1ws[i], outputdir, CACHE=cache)
                            if 'BDP' in stages:
                                runWorkflow(subjectID, t1ws[i], outputdir, BDP=dwis[i].split('.')[0],
                                            BVAL=str(bval), BVEC=str(bvec), CACHE=cache)
                            if 'SVREG' in stages:
                                runWorkflow(subjectID, t1ws[i], outputdir, SVREG=True, SingleThread=thread,
                                            ATLAS=str(atlas), CACHE=cache)
                    else:
                        for t1 in t1ws:
                            if 'ALL' in stages:
                                runWorkflow(subjectID, t1, outputdir, SVREG=True,
                                            SingleThread=thread, ATLAS=str(atlas), CACHE=cache)
                            if 'CSE' in stages:
                                runWorkflow(subjectID, t1, outputdir, CACHE=cache)
                            if 'SVREG' in stages:
                                runWorkflow(subjectID, t1, outputdir, SVREG=True,
                                            SingleThread=thread, ATLAS=str(atlas), CACHE=cache)
                            if 'BDP' in stages:
                                print('\nNo DWI data found. Running CSE only.')
                                runWorkflow(subjectID, t1, outputdir, CACHE=cache)

                    for t1 in t1ws:
                        if 'BFP' or 'ALL' in stages:
                            if (len(funcs) < 1):
                                print("No fMRI files found for subject %s!" % subject_label)
                            else:
                                for i in range(0, len(funcs)):
                                    # sess_input = funcs[i][
                                    #              funcs[i].index(subjectID + '_') + len(subjectID + '_'): funcs[i].index(
                                    #                  '_bold')]
                                    taskname = funcs[i].split("task-")[1].split("_")[0]
                                    sess_input = "task-" + taskname
                                    # bfp('/config.ini', t1, funcs[i], args.output_dir, subjectID, sess_input,
                                    #     args.TR, cache)
                                    cmd = '{BFPpath} {configini} {t1} {func} {studydir} {subjID} {sess} {TR} '.format(
                                              BFPpath=BFPpath,
                                              configini= '/config.ini',
                                              t1=t1,
                                              func=funcs[i],
                                              studydir=args.output_dir,
                                              subjID=subjectID,
                                              sess=sess_input,
                                              TR=args.TR
                                          )
                                    print(cmd)
                                    subprocess.call(cmd, shell=True)
            else:

                t1ws = [f.filename for f in layout.get(subject=subject_label,
                                                       type='T1w', extensions=["nii.gz", "nii"])]
                assert (len(t1ws) > 0), "No T1w files found for subject %s!" % subject_label

                dwis = [f.filename for f in layout.get(subject=subject_label,
                                                       type='dwi', extensions=["nii.gz", "nii"])]
                outputdir = str(args.output_dir + os.sep + 'sub-%s' % subject_label + os.sep + 'anat')
                if not cache:
                    cache = outputdir
                if not os.path.exists(outputdir):
                    os.makedirs(outputdir)
                if (len(dwis) > 0):
                    numOfPairs = min(len(t1ws), len(dwis))
                    for i in range(0, numOfPairs):
                        bval = layout.get_bval(dwis[i])
                        bvec = layout.get_bvec(dwis[i])
                        if 'ALL' in stages:
                            runWorkflow('sub-%s' % subject_label, t1ws[i], outputdir,
                                        BDP=dwis[i].split('.')[0], BVAL=str(bval), BVEC=str(bvec), SVREG=True,
                                        SingleThread=thread, ATLAS=str(atlas), CACHE=cache)
                        if 'CSE' in stages:
                            runWorkflow('sub-%s' % subject_label, t1ws[i], outputdir, CACHE=cache)
                        if 'BDP' in stages:
                            runWorkflow('sub-%s' % subject_label, t1ws[i], outputdir,
                                        BDP=dwis[i].split('.')[0], BVAL=str(bval), BVEC=str(bvec), CACHE=cache)
                        if 'SVREG' in stages:
                            runWorkflow('sub-%s' % subject_label, t1ws[i], outputdir,
                                        SVREG=True, SingleThread=thread, ATLAS=str(atlas), CACHE=cache)
                else:
                    for t1 in t1ws:
                        if 'ALL' in stages:
                            runWorkflow('sub-%s' % subject_label, t1, outputdir, SVREG=True,
                                        SingleThread=thread, ATLAS=(atlas), CACHE=cache)
                        if 'CSE' in stages:
                            runWorkflow('sub-%s' % subject_label, t1, outputdir, CACHE=cache)
                        if 'SVREG' in stages:
                            runWorkflow('sub-%s' % subject_label, t1, outputdir, SVREG=True,
                                        SingleThread=thread, ATLAS=(atlas), CACHE=cache)
                        if 'BDP' in stages:
                            print('\nNo DWI data found. Running CSE only.')
                            runWorkflow('sub-%s' % subject_label, t1, outputdir, CACHE=cache)
                        # if 'BFP' in stages:

                        #     assert (len(funcs) > 0), "No fMRI files found for subject %s!" % subject_label
                        #
                        #     subjectID = 'sub-{}'.format(subject_label)
                        #
                        #     for i in range(0, len(funcs)):
                        #         sess_input = funcs[i][
                        #                      funcs[i].index(subjectID + '_') + len(subjectID + '_'): funcs[i].index(
                        #                          '_bold')]
                        #         bfp('/config.ini', t1ws[0], funcs[i], args.output_dir, subjectID, sess_input, args.TR)
                for t1 in t1ws:
                    if 'BFP' or 'ALL' in stages:
                        funcs = [f.filename for f in layout.get(subject=subject_label,
                                                                type='bold',
                                                                extensions=["nii.gz", "nii"])]
                        if (len(funcs) < 1):
                            print("No fMRI files found for subject %s!" % subject_label)
                        else:
                            for i in range(0, len(funcs)):
                                # sess_input = funcs[i][
                                #              funcs[i].index('sub-%s' % subject_label + '_') + len('sub-%s' % subject_label + '_'): funcs[i].index(
                                #                  '_bold')]
                                taskname = funcs[i].split("task-")[1].split("_")[0]
                                sess_input = "task-" + taskname
                                # bfp('/config.ini', t1, funcs[i], args.output_dir, 'sub-%s' % subject_label, sess_input,
                                #     args.TR, cache)
                                cmd = '{BFPpath} {configini} {t1} {func} {studydir} {subjID} {sess} {TR}'.format(
                                    BFPpath=BFPpath,
                                    configini='/config.ini',
                                    t1=t1,
                                    func=funcs[i],
                                    studydir=args.output_dir,
                                    subjID='sub-%s' % subject_label,
                                    sess=sess_input,
                                    TR=args.TR
                                )
                                subprocess.call(cmd, shell=True)

if args.analysis_level == "group":

    analyses = []

    if args.analysistype == "ALL":
        analyses.append('ANAT')
        analyses.append('FUNC')
    else:
        analyses.append(args.analysistype)

    if 'ANAT' in analyses:
        if args.rmarkdown:
            run_rmarkdown(args.rmarkdown)
        else:
            specs = bssrSpec(args.modelspec, args.output_dir)
            bss_data = load_bss_data(specs)
            bss_model = run_model(specs, bss_data)
            save_bss(bss_data, bss_model, specs.resultdir)
    if 'FUNC' in analyses:
        if not os.path.exists(os.path.join(args.output_dir, 'stats')):
            os.mkdir(os.path.join(args.output_dir, 'stats'))

        specs = bssrSpec(args.modelspec, args.output_dir)
        if specs.GOfolder != "":
            # TODO fix
            # runGroupDiff(specs, specs.GOfolder)
            if specs.bfptest == 'linreg':
                bfp_linear_regr(specs, specs.GOfolder)
            elif specs.bfptest == 'linreg_pairwise':
                bfp_linear_regr_pairwise(specs, specs.GOfolder)
            elif specs.bfptest == 'group_compare':
                bfp_group_compare(specs, specs.GOfolder)
        else:
            # bfp_linear_regr(specs, specs.outputdir)
            if specs.bfptest == 'linreg':
                bfp_linear_regr(specs, specs.outputdir)
            elif specs.bfptest == 'linreg_pairwise':
                bfp_linear_regr_pairwise(specs, specs.outputdir)
            elif specs.bfptest == 'group_compare':
                bfp_group_compare(specs, specs.outputdir)
            else:
                sys.stdout.writable("Please write a valid test type.")
        # else:
        #     with io.open(specs.tsv, newline='') as tsvfile:
        #         treader = csv.DictReader(tsvfile, delimiter=str(u'\t').encode('utf-8'),
        #                                  quotechar=str(u'"').encode('utf-8'))
        #         for row in treader:
        #             sub = row['participant_id']
        #             qc = row[specs.exclude]
        #             if int(qc) == 0:
        #                 fname = os.path.join(args.output_dir, sub, 'func', sub + specs.fileext)
        #                 newfname = os.path.join(args.output_dir, 'stats', sub + specs.fileext)
        #                 try:
        #                     copyfile(fname, newfname)
        #                 except:
        #                     print('{0} file does not exist.'.format(
        #                         os.path.join(args.output_dir, sub, 'func', sub + specs.fileext)))
        #     # runGroupDiff(specs, specs.statsdir)
        #     bfp_linear_regr(specs, specs.statsdir)


