import subprocess
from bin.brainsuiteWorkflow import subjLevelProcessing
import os
import glob

def runWorkflow(stages, t1ws, preprocspecs, atlas, cacheset, thread, layout, dwis, funcs,
            subject_label, configini, args):
    # try:
    TR = preprocspecs.TR
    if args.TR:
        TR = args.TR
    BFP = {'configini': configini,
                       'func': [],
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
            # if os.environ['runJustQC'] == 'False':
            #     cmd = '/BrainSuite/QC/qcState.sh {0} {1}'.format(WEBPATH, 0)
            #     subprocess.call(cmd, shell=True)
        else:
            QCdir = None

        if 'BFP' in stages:
            sess_inputs = []
            fmris = []
            tasknames = layout.get_tasks()
            if args.preprocspec:
                tasknames = preprocspecs.taskname
            if args.fmri_task_name:
                tasknames = args.fmri_task_name
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
