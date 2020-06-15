# -*- coding: utf-8 -*-

import os
import subprocess
import sys
from math import isnan
from subprocess import Popen, PIPE

import configparser

# from brainsuiteStructural import runStructuralProcessing
from bin.brainsuiteWorkflowNoQC import runWorkflow
from bin.deprecated.func_preproc import func_preproc


# import nipype.pipeline.engine as pe
# import nipype.interfaces.brainsuite as bs
# import nipype.interfaces.io as io


## TODO: error catching

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
        # traceback.print_exc()
        sys.exit('Non zero return code. Processing pipeline errored.')
        # raise Exception("Non zero return code: %d" % process.returncode)

def bfp(configfile, t1, fmri, studydir, subid, sessionid, TR, cache):
    subdir = os.path.join(studydir, subid)
    anatDir = os.path.join(subdir, 'anat')
    funcDir = os.path.join(subdir, 'func')
    subbasename = os.path.join(anatDir,'{}_T1w'.format(subid))

    print('fMRI: {}'.format(fmri))
    print('Session ID: {}'.format(sessionid))

    ## Read configuration file and set up environment variables
    print('# Starting BFP Run')
    if not os.path.exists(configfile):
        sys.exit('Config file: {} does not exist'.format(configfile))

    print('## Reading config file')
    config = configparser.ConfigParser()
    config.read(configfile)
    print(' done')

    print('## Setting up the environment')
    os.environ['PATH'] = os.environ['PATH']+':'+config.get('main', 'FSLPATH')+':'+os.path.join(config.get('main', 'FSLPATH'),'bin')
    os.environ['PATH'] = os.environ['PATH']+':'+config.get('main', 'AFNIPATH')+':'+os.path.join(config.get('main', 'AFNIPATH'),'bin')
    os.environ['FSLOUTPUTTYPE'] = config.get('main', 'FSLOUTPUTTYPE')
    os.environ['FSLDIR'] = config.get('main', 'FSLPATH')
    os.environ['BrainSuiteDir'] = config.get('main', 'BrainSuitePath')
    os.environ['LD_LIBRARY_PATH'] = config.get('main', 'LD_LIBRARY_PATH')
    os.environ['AFNI_NIFTI_TYPE_WARN'] = 'NO'

    BrainSuitePath = config.get('main', 'BrainSuitePath')
    BFPPATH = config.get('main', 'BFPPATH')
    bst_exe = os.path.join(BFPPATH,'supp_data','cortical_extraction_nobse.sh')
    svreg_exe = os.path.join(BrainSuitePath,'svreg','bin','svreg.sh')
    thicknessPVC_exe = os.path.join(BrainSuitePath,'svreg','bin','thicknessPVC.sh')

    nii2int16_exe = os.path.join(BFPPATH, 'nii2int16.sh')
    func_preproc_script = os.path.join(BFPPATH, 'supp_data', 'func_preproc.sh')
    resample2surf_exe = os.path.join(BFPPATH, 'resample2surf.sh')
    generateSurfGOrdfMRI_exe = os.path.join(BFPPATH, 'generateSurfGOrdfMRI.sh')
    generateVolGOrdfMRI_exe = os.path.join(BFPPATH, 'generateVolGOrdfMRI.sh')
    combineSurfVolGOrdfMRI_exe = os.path.join(BFPPATH, 'combineSurfVolGOrdfMRI.sh')
    tNLMPDFGOrdfMRI_exe = os.path.join(BFPPATH, 'tNLMPDFGOrdfMRI.sh')
    generateGOrdSCT_exe = os.path.join(BFPPATH, 'generateGOrdSCT.sh')

    BCIbasename = os.path.join(BrainSuitePath,'svreg','BCI-DNI_brain_atlas','BCI-DNI_brain')
    ATLAS = os.path.join(BrainSuitePath,'svreg','BCI-DNI_brain_atlas','BCI-DNI_brain.bfc.nii.gz')
    GOrdSurfIndFile = os.path.join(BFPPATH,'supp_data','bci_grayordinates_surf_ind.mat')
    GOrdVolIndFile = os.path.join(BFPPATH,'supp_data','bci_grayordinates_vol_ind.mat')
    nuisance_template = os.path.join(BFPPATH,'supp_data','nuisance.fsf')
    fwhm = config.get('main', 'FWHM')
    hp = config.get('main', 'HIGHPASS')
    lp = config.get('main', 'LOWPASS')
    continueRun = float(config.get('main', 'CONTINUERUN'))
    FSLRigid = config.get('main', 'FSLRigid')

    if hasattr(config, 'MultiThreading'):
        config.set('main', 'MultiThreading', float(config.get('main', 'MultiThreading')))
        if isnan(config.get('main', 'MultiThreading')):
            config.set('main', 'MultiThreading','0')
    else:
        config.set('main', 'MultiThreading', '1')

    if hasattr(config, 'T1SpaceProcessing'):
        config.set('main', 'T1SpaceProcessing', float(config.get('main', 'T1SpaceProcessing')))
        if isnan(config.get('main', 'T1SpaceProcessing')):
            config.set('main', 'T1SpaceProcessing', '0')
    else:
        config.set('main', 'T1SpaceProcessing', '1')

    if hasattr(config, 'EnabletNLMPdfFiltering'):
        config.set('main', 'EnabletNLMPdfFiltering', float(config.get('main', 'EnabletNLMPdfFiltering')))
        if isnan(config.get('main', 'EnabletNLMPdfFiltering')):
            config.set('main', 'EnabletNLMPdfFiltering', '0')
    else:
        config.set('main', 'EnabletNLMPdfFiltering', '1')

    if hasattr(config, 'EnableShapeMeasures'):
        config.set('main', 'EnableShapeMeasures', float(config.get('main', 'EnableShapeMeasures')))
        if isnan(config.get('main', 'EnableShapeMeasures')):
            config.set('main', 'EnableShapeMeasures', '0')
    else:
        config.set('main', 'EnableShapeMeasures', '1')

    if hasattr(config, 'FSLRigid'):
        config.set('main', 'FSLRigid', float(config.get('main', 'FSLRigid')))
        if isnan(config.get('main', 'FSLRigid')):
            config.set('main', 'FSLRigid', '0')
    else:
        config.set('main', 'FSLRigid', '1')
    print(' done')


    ## Create Directory Structure
    # This directory structure is in BIDS format
    ##
    print('## Creating Directory Structure')
    if (os.path.exists(subdir) and continueRun==0):
        sys.exit('The subject directory {} already exists!\n Please check that directory for previous runs and delete it if necessary'.format(subdir))
    if not os.path.exists(subdir):
        cmd = ' '.join(['mkdir', subdir])
        run(cmd, cwd=subdir)
        # subprocess.call(['mkdir', subdir])

    print('Creating Directory: {}'.format(anatDir))
    if not os.path.exists(anatDir):
        cmd = ' '.join(['mkdir', anatDir])
        run(cmd, cwd=subdir)
        # subprocess.call(['mkdir', anatDir])

    t1hires = os.path.join(anatDir, '{}_T1w.orig.hires.nii.gz'.format(subid))
    t1ds = os.path.join(anatDir, '{}_T1w.ds.orig.nii.gz'.format(subid))

    if int(config.get('main', 'T1SpaceProcessing')) == 1:
        ATLAS=t1hires

    if not os.path.exists(t1hires):
        # subprocess.call(['cp', t1, t1hires])
        run(' '.join(['cp', t1, t1hires]), cwd=subdir)

    print('Creating Directory: {}'.format(funcDir))
    if not os.path.exists(funcDir):
        cmd = ' '.join(['mkdir', funcDir])
        run(cmd, cwd=subdir)
        # subprocess.call(['mkdir', funcDir])

    print('Copying fMRI files')
    if not os.path.exists(os.path.join(funcDir, '{}_{}_bold.nii.gz'.format(subid, sessionid))):
        cmd = ' '.join(['cp', fmri, os.path.join(funcDir, '{}_{}_bold.nii.gz'.format(subid, sessionid))])
        run(cmd, cwd=subdir)
        # subprocess.call(['cp', fmri, os.path.join(funcDir, '{}_{}_bold.nii.gz'.format(subid, sessionid))])
    else:
        print('Subject={} Session={} : Already'.format(subid, sessionid))

    print('done')


    ## Generate 1mm BCI-DNI_brain brain as a standard template
    # This is used a template for anatomical T1 data
    ##
    if not (int(config.get('main', 'T1SpaceProcessing')) == 1):
        ATLAS_DS = os.path.join(anatDir, 'standard1mm.nii.gz')
        cmd = ['flirt', '-ref', ATLAS, '-in', ATLAS, '-out', ATLAS_DS, '-applyisoxfm', '1']

        print('Creating 1mm isotropic standard brain')
    else:
        ATLAS_DS = os.path.join(anatDir, 'standard.nii.gz')
        cmd = ['cp', ATLAS, ATLAS_DS]
        print('Creating a copy of the t1 image to be used as the standard brain')

    if not os.path.exists(ATLAS_DS): # subprocess.call(cmd)
        run(' '.join(cmd), cwd=subdir)
    else:
        print('Already ')
    print('done')


    ## Resample T1w image to 1mm cubic resolution
    # BrainSuite works best at this resolution
    ##
    if not (int(config.get('main', 'T1SpaceProcessing')) == 1):
        print('## Resample T1w image to 1mm cubic resolution ')
        cmd = ['flirt', 'in', t1hires, '-ref', t1hires, '-out', t1ds, '-applyisoxfm', '1']
    else:
        t1ds = t1hires

    if not os.path.exists(t1ds):
        # subprocess.call(cmd)
        # subprocess.call([nii2int16_exe, t1ds, t1ds])
        run(' '.join(cmd), cwd= subdir)
        run(' '.join([nii2int16_exe, t1ds, t1ds]), cwd=subdir)
    else:
        print('Already ')
    print('done')


    ## Skull Strip MRI
    ## run bse workflow
    ## TODO: do nipype

    print('## Performing Skull Extraction\n')
    bse = os.path.join(BrainSuitePath, 'bin', 'bse')
    #
    if (int(config.get('main', 'T1SpaceProcessing')) == 1):
        bseout = os.path.join(anatDir, '{}_T1w.orig.bse.nii.gz'.format(subid))
    else:
        bseout = os.path.join(anatDir, '{}_T1w.ds.orig.bse.nii.gz'.format(subid))
    #
    # cmd = [bse, '--auto', '--trim', '-i', t1ds, '-o', bseout]
    if not os.path.exists(bseout):
        # subprocess.call(cmd)
        # run(' '.join(cmd), cwd=subdir)
        runWorkflow(subid, t1ds, anatDir, SVREG=True, BSEONLY=True, CACHE=cache)
    else:
        print('Already ')
    print('done')


    ## Coregister t1 to BCI-DNI Space
    ##
    print('## Coregister t1 to BCI-DNI Space')
    bsenew = os.path.join(anatDir, '{}_T1w.nii.gz'.format(subid))

    if (int(config.get('main', 'T1SpaceProcessing')) == 1):
        cmd = ['cp', t1, bsenew]
    else:
        cmd = ['flirt', '-ref', ATLAS_DS, '-in', bseout, '-out', bsenew]

    if not os.path.exists(bsenew):
        # subprocess.call(cmd)
        # subprocess.call([nii2int16_exe, bsenew, bsenew, '0'])
        run(' '.join(cmd), cwd=subdir)
        run(' '.join([nii2int16_exe, bsenew, bsenew, '0']), cwd=subdir)

    bsenew2 = os.path.join(anatDir, '{}_T1w.bse.nii.gz'.format(subid))

    if not os.path.exists(bsenew2):
        if (int(config.get('main', 'T1SpaceProcessing')) == 1):
            cmd = ['cp', bseout, bsenew2]
            # subprocess.call(['cp', bseout, bsenew2])
            # subprocess.call([nii2int16_exe, bsenew2, bsenew2, '0'])
            run(' '.join(cmd), cwd=subdir)
            run(' '.join([nii2int16_exe, bsenew2, bsenew2, '0']), cwd=subdir)
        else:
            # subprocess.call(['cp', bsenew, bsenew2])
            run(' '.join(cmd), cwd=subdir)
    else:
        print('Already ')
    print('done')

    bsemask = os.path.join(anatDir, '{}_T1w.mask.nii.gz'.format(subid))
    cmd = ['fslmaths', bsenew2, '-thr', '0', '-bin', '-mul', '255', bsemask, '-odt', 'char']
    if not os.path.exists(bsemask):
        # subprocess.call(cmd)
        run(' '.join(cmd), cwd=subdir)


    ## Run BrainSuite and SVReg
    ## TODO: check if it re-runs
    print('## Running BrainSuite CSE')
    # cmd = [bst_exe, subbasename]

    if (int(config.get('main', 'MultiThreading')) == 1):
        singleThread = 'ON'
    else:
        singleThread = 'OFF'
    # runStructuralProcessing(t1ds, anatDir, subid, singleThread=singleThread)
    runWorkflow(subid, t1ds, anatDir, SVREG=True,
                SingleThread=singleThread, CACHE=cache)
    print('Running BrainSuite CSE and SVReg')

    # if not os.path.exists(subbasename+'.right.pial.cortex.dfs'):
    #     subprocess.call(cmd)
    #
    #     runStructuralProcessing(t1ds, anatDir, subid, singleThread=singleThread)
    #     print('Running BrainSuite CSE and SVReg')
    #
    # print('Running SVReg')
    # if (int(config.get('main', 'MultiThreading')) == 1):
    #     cmd = [svreg_exe, subbasename, BCIbasename]
    # else:
    #     cmd = [svreg_exe, subbasename, BCIbasename, 'U']
    #
    # if not os.path.exists(subbasename+'.svreg.label.nii.gz'):
    #     subprocess.call(cmd)
    # else:
    #     print('Already ')
    print('done')


    ## Generate 3mm BCI-DNI_brain brain as a standard template
    # This is used a template for fMRI data
    ##
    if (int(config.get('main', 'T1SpaceProcessing')) == 1):
        ATLAS = os.path.join(anatDir, '{}_T1w.bfc.nii.gz'.format(subid))

    cmd = ['flirt', '-ref', ATLAS, '-in', ATLAS, '-out', os.path.join(funcDir, 'standard.nii.gz'), '-applyisoxfm', '3']
    print('Creating 3mm isotropic standard brain')
    if not os.path.exists(os.path.join(funcDir, 'standard.nii.gz')):
        # subprocess.call(cmd)
        run(' '.join(cmd), cwd=subdir)
    else:
        print('Already ')
    print('done')


    ## Run Batch_Process Pipeline for fMRI
    ##
    print('## Run fmri preprocessing script')
    fmribasename = os.path.join(funcDir, '{}_{}_bold'.format(subid, sessionid))
    if not os.path.exists(subbasename+'_res2standard.nii.gz'):
        func_preproc(subbasename, fmribasename, funcDir, TR, nuisance_template, fwhm, hp, lp, int(FSLRigid))
    else:
        print('fMRI {}: Already '.format(fmribasename))
    print('done')


    ## Grayordinate representation
    # Transfer data to surface and then to USCBrain atlas surface and produce surface
    # grayordinates and then Transfer data to volumetric grayordinates.
    #
    # The Grayordinate data is in the same format as HCP data on 32k surfaces.
    ## The filename of grayordinate data is fmri_bold.32k.GOrd.nii.gz
    print('## Transferring data from subject to atlas...')
    fmri2surfFile = os.path.join(funcDir, '{}_{}_bold2surf.mat'.format(subid, sessionid))
    GOrdSurfFile = os.path.join(funcDir, '{}_{}_bold2surf_GOrd.mat'.format(subid, sessionid))
    fmri2standard = os.path.join(funcDir, '{}_{}_bold_res2standard.nii.gz'.format(subid, sessionid))
    GOrdVolFile = os.path.join(funcDir, '{}_{}_bold2Vol_GOrd.mat'.format(subid, sessionid))
    GOrdFile = os.path.join(funcDir, '{}_{}_bold.32k.GOrd.mat'.format(subid, sessionid))
    print('Resampling fMRI to surface')
    if ((not os.path.exists(fmri2surfFile)) and (not os.path.exists(GOrdSurfFile)) and (not os.path.exists(GOrdFile))):
        cmd= [resample2surf_exe, subbasename, fmri2standard, fmri2surfFile, str(int(config.get('main', 'MultiThreading')))]
        # subprocess.call([resample2surf_exe, subbasename, fmri2standard, fmri2surfFile, str(int(config.get('main', 'MultiThreading')))])
        run(' '.join(cmd), cwd=subdir)
    else:
        print('Already ')
    print('done')

    print('Generating Surface Grayordinates')
    if ((not os.path.exists(GOrdSurfFile)) and (not os.path.exists(GOrdFile))):
        cmd = [generateSurfGOrdfMRI_exe, GOrdSurfIndFile, fmri2surfFile, GOrdSurfFile]
        # subprocess.call([generateSurfGOrdfMRI_exe, GOrdSurfIndFile, fmri2surfFile, GOrdSurfFile])
        run(' '.join(cmd), cwd=subdir)
        # The surf file is very large, deleting to save space
        # subprocess.call(['rm', fmri2surfFile])
        run(' '.join(['rm', fmri2surfFile]), cwd=subdir)
    else:
        print('Already ')
    print('done')

    print('Generating Volume Grayordinates')
    if ((not os.path.exists(GOrdVolFile)) and (not os.path.exists(GOrdFile))):
        # subprocess.call([generateVolGOrdfMRI_exe, GOrdVolIndFile, subbasename, fmri2standard, GOrdVolFile])
        cmd=[generateVolGOrdfMRI_exe, GOrdVolIndFile, subbasename, fmri2standard, GOrdVolFile]
        run(' '.join(cmd), cwd=subdir)
    else:
        print('Already ')
    print('done')

    print('Combining Surface and Volume Grayordinates')
    if not os.path.exists(GOrdFile):
        cmd = [combineSurfVolGOrdfMRI_exe, GOrdSurfFile, GOrdVolFile, GOrdFile]
        # subprocess.call([combineSurfVolGOrdfMRI_exe, GOrdSurfFile, GOrdVolFile, GOrdFile])
        # subprocess.call(['rm', GOrdSurfFile])
        # subprocess.call(['rm', GOrdVolFile])
        run(' '.join(cmd), cwd=subdir)
        run(' '.join(['rm', GOrdSurfFile, GOrdVolFile]), cwd=subdir)
    else:
        print('Already ')
    print('done')
    print('The grayordinates file is: {}'.format(GOrdFile))


    ## tNLMPDF
    # This part of the code takes grayordinate data generated by the previous pipeline
    # and performs tNLMPdf filtering.
    #
    # The output is stored in <fmri fmri>.32k.GOrd.filt.nii.gz
    ##
    if (int(config.get('main', 'EnabletNLMPdfFiltering')) == 1):
        GOrdFile = os.path.join(funcDir, '{}_{}_bold.32k.GOrd.mat'.format(subid, sessionid))
        GOrdFiltFile = os.path.join(funcDir, '{}_{}_bold.32k.GOrd.filt.mat'.format(subid, sessionid))
        print('tNLMPdf filtering for subject = {} session = {}'.format(subid, sessionid))
        if not os.path.exists(GOrdFiltFile):
            cmd = [tNLMPDFGOrdfMRI_exe, GOrdFile, GOrdFiltFile, str(float(config.get('main', 'fpr'))), str(float(config.get('main', 'memory'))),
                   str(float(config.get('main', 'MultiThreading'))), config.get('main', 'scbPath')]
            # subprocess.call([tNLMPDFGOrdfMRI_exe, GOrdFile, GOrdFiltFile, str(float(config.get('main', 'fpr'))), str(float(config.get('main', 'memory'))), config.get('main', 'scbPath')])
            run(' '.join(cmd), cwd=subdir)
        else:
            print('Already ')
        print('done')
        print('The tNLMPDF filtered grayordinates files are ready !! \n Good Night!')


    if (int(config.get('main', 'EnableShapeMeasures')) == 1):
        # print('Running thicknessPVC')
        # cmd = [thicknessPVC_exe, subbasename]
        # if not os.path.exists(os.path.join(subbasename, 'atlas.pvc-thickness_0-6mm.right.mid.cortex.dfs')):
        #     subprocess.call(cmd)
        # else:
        #     print('Already computed thicknessPVC')

        # runStructuralProcessing(t1ds, anatDir, subid, singleThread=singleThread, THICKPVC=True)

        if not os.path.exists(subbasename+'.SCT.GOrd.mat'):
            cmd=[generateGOrdSCT_exe, subbasename, GOrdSurfIndFile]
            # subprocess.call([generateGOrdSCT_exe, subbasename, GOrdSurfIndFile])
            run(' '.join(cmd), cwd=subdir)
        else:
            print('Already done SCT')
        print('done')

    print('All done!')
