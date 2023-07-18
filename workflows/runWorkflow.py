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

from workflows.brainsuiteWorkflow import subjLevelProcessing
import os
import shutil

def runWorkflow(stages, t1ws, preprocspecs, atlas, cacheset, thread, layout, dwis, funcs,
            subject_label, args):
    '''
    This function is a wrapper that runs the appropriate pipelines in brainsuiteWorkflow.py.

    Authors: Yeun Kim, Jason Wong, Clayton Jerlow

    Copyright (C) 2022 The Regents of the University of California
    Authored by Yeun Kim, Jason Wong, Clayton Jerlow, David W. Shattuck, Ahmanson-Lovelace Brain Mapping Center
    Dept. of Neurology, David Geffen School of Medicine, UCLA.

    '''
    TR = preprocspecs.TR
    if args.TR:
        TR = args.TR
    BFP = {'func': [],
           'studydir': args.output_dir,
           'subjID': '',
           'TR': TR}


    assert (len(t1ws) > 0), "No T1w files found for subject %s!" % subject_label
    for i, t1 in enumerate(t1ws):
        stages_tmp = stages[:]
        subjectID = t1ws[i].split('/')[-1].split('_T1w')[0]
        if args.ignore_suffix:
            subjectID_tmp = [ tok for tok in subjectID.split('_') if not args.ignore_suffix in tok]
            subjectID = '_'.join(subjectID_tmp)
        outputdir = os.path.join(args.output_dir, subjectID)

        if not cacheset:
            cache = outputdir
        else:
            cache = args.cache + '/' + subjectID
        if not os.path.exists(cache):
            os.makedirs(cache)

        if 'QC' in stages:
            if args.QCdir:
                QCdir = os.path.join(args.QCdir, 'QC')
                WEBDIRsub = os.path.join(args.QCdir, 'QC', subjectID)
                WEBPATH = os.path.join(args.QCdir, 'QC', subjectID, subjectID)
            else:
                QCdir = os.path.join(args.output_dir, 'QC')
                WEBDIRsub = os.path.join(args.output_dir, 'QC', subjectID)
                WEBPATH = os.path.join(args.output_dir, 'QC', subjectID, subjectID)
            if not os.path.exists(WEBDIRsub):
                os.makedirs(WEBDIRsub)

        else:
            QCdir = None

        if 'BFP' in stages:
            sess_inputs = []
            fmris = []
            tasknames = layout.get_tasks()
            if args.preprocspec:
                tasknames = preprocspecs.taskname
                configini = '{0}/{1}/config.ini'.format(args.output_dir, subjectID)
            else:
                shutil.copyfile('/config.ini', '{0}/{1}/config.ini'.format(args.output_dir, subjectID))
                configini = '{0}/{1}/config.ini'.format(args.output_dir, subjectID)
            if args.fmri_task_name:
                tasknames = args.fmri_task_name
            BFP.update({'configini': configini})
            print('Will be running the following fMRI with task-names', tasknames)
            if (len(funcs) > 0):
                for f in range(0, len(funcs)):
                    taskname = funcs[f].split("task-")[1].split("_")[0]
                    if taskname in tasknames:
                        sess_inputs.append("task-" + taskname)
                        fmris.append(funcs[f])
                    else:
                        print('BFP will not run on {0} fmri data because the '
                              'task name was not found in the specs (i.e. in the preprocspec.json file).\n'.format(
                            taskname))
                if len(sess_inputs) > 0:
                    BFP.update({'func': fmris, 'sess': sess_inputs})
            else:
                if 'BFP' in stages_tmp:
                    print('No FMRI images found. Therefore, not running BFP. \n')
                    stages_tmp.remove('BFP')

        BFP.update({'subjID': subjectID})
        if 'BDP' not in stages or len(dwis) == 0:
            if len(dwis) == 0:
                print('No DWI images found. Therefore, not running BDP. \n')
            if 'BDP' in stages_tmp:
                stages_tmp.remove('BDP')
            print('Running the following stages: {0} \n\n'.format(stages_tmp))
            process = subjLevelProcessing(stages_tmp, specs=preprocspecs, CACHE=cache, SingleThread=thread,
                                          ATLAS=str(atlas), QCDIR=QCdir)
        else:
            bval = layout.get_bval(dwis[i])
            bvec = layout.get_bvec(dwis[i])
            print('\n\nRunning the following stages: {0} \n\n'.format(stages_tmp))
            process = subjLevelProcessing(stages_tmp, specs=preprocspecs, BDP=dwis[i].split('.')[0],
                                          BVAL=str(bval), BVEC=str(bvec), CACHE=cache, SingleThread=thread,
                                          ATLAS=str(atlas), QCDIR=QCdir)
        process.runWorkflow(subjectID, t1, outputdir, BFP)
