import subprocess
from bin.brainsuiteWorkflowNoQC import subjLevelProcessing
import os

def runWorkflow(stages, t1ws, preprocspecs, atlas, cacheset, thread, subjectID, outputdir, layout, dwis, funcs,
                subject_label, BFPpath, configini, args, session):
    if not cacheset:
        cache = outputdir
    else:
        cache = args.cache + '/' + subjectID
        if not os.path.exists(cache):
            os.makedirs(cache)
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    if 'BDP' not in stages:
        T1nums = len(t1ws)
        for i in range(0, T1nums):
            process = subjLevelProcessing(stages, specs=preprocspecs, CACHE=cache, SingleThread=thread,
                                          ATLAS=str(atlas))
            process.runWorkflow(subjectID, t1ws[i], outputdir)
    else:
        numOfPairs = min(len(t1ws), len(dwis))
        for i in range(0, numOfPairs):
            bval = layout.get_bval(dwis[i])
            bvec = layout.get_bvec(dwis[i])
            process = subjLevelProcessing(stages, specs=preprocspecs, BDP=dwis[i].split('.')[0],
                                          BVAL=str(bval), BVEC=str(bvec), CACHE=cache, SingleThread=thread,
                                          ATLAS=str(atlas))

            process.runWorkflow(subjectID, t1ws[i], outputdir)

        try:
            cmd = "rename 's/_T1w/_dwi/' {0}/*".format(os.path.join(args.output_dir, subjectID, 'dwi'))
            subprocess.call(cmd, shell=True)
        except:
            pass

    if 'BFP' in stages:
        for t1 in t1ws:
            if (len(funcs) < 1):
                print("No fMRI files found for subject %s!" % subject_label)
            else:
                for i in range(0, len(funcs)):
                    taskname = funcs[i].split("task-")[1].split("_")[0]

                    if taskname in preprocspecs.taskname:
                        sess_input = "task-" + taskname
                        cmd = '{BFPpath} {configini} {t1} {func} {studydir} {subjID} {sess} {TR} '.format(
                            BFPpath=BFPpath,
                            configini=configini,
                            t1=t1,
                            func=funcs[i],
                            studydir=args.output_dir,
                            subjID=subjectID,
                            sess=sess_input,
                            TR=args.TR
                        )
                        print(cmd)
                        subprocess.call(cmd, shell=True)
                        # run(cmd)
                    else:
                        print('BFP was not run on {0} fmri data because the '
                              'task name was not found in the specs.'.format(taskname))

    # if 'QC' in stages:
    #     QCdir = os.path.join(args.output_dir, 'QC')
    #     if not os.path.exists(QCdir):
    #         os.makedirs(QCdir)
    #     cmd = '{runQC} {WEBPATH} {data} {output} {ID} {fullID} {ses} '.format(
    #         runQC='/BrainSuite/QC/runQC.sh',
    #         WEBPATH=QCdir,
    #         data=args.bids_dir,
    #         output=args.output_dir,
    #         ID=subject_label,
    #         fullID=subjectID,
    #         ses=session
    #     )
    #     subprocess.call(cmd, shell=True)
