# -*- coding: utf-8 -*-
'''
Copyright (C) 2023 The Regents of the University of California

Created by Yeun Kim, Jason Wong, Clayton Jerlow

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
import subprocess
from nipype import config #Set configuration before importing nipype pipeline
cfg = dict(execution={'remove_unnecessary_outputs' : False}) #We do not want nipype to remove unnecessary outputs
config.update_config(cfg)
import sys
import nipype.pipeline.engine as pe
import nipype.interfaces.brainsuite as bs
import nipype.interfaces.io as io
from nipype.interfaces.utility import Function, Merge
from nipype import Node
from shutil import copyfile
import os
import errno
from QC.stageNumDict import stageNumDict
import fnmatch

BRAINSUITE_VERSION= os.environ['BrainSuiteVersion']
ATLAS_MRI_SUFFIX = 'brainsuite.icbm452.lpi.v08a.img'
ATLAS_LABEL_SUFFIX = 'brainsuite.icbm452.v15a.label.img'
WORKFLOW_NAME = 'BrainSuite'
BRAINSUITE_ATLAS_DIRECTORY = "/opt/BrainSuite{0}/atlas/".format(BRAINSUITE_VERSION)
BRAINSUITE_LABEL_DIRECTORY = "/opt/BrainSuite{0}/labeldesc/".format(BRAINSUITE_VERSION)
LABEL_SUFFIX = 'brainsuite_labeldescriptions_30March2018.xml'
completed = 'C'
launched = 'L'
unqueued = 'N'
queued = 'Q'
errored = 'E'
QCSTATE = '/BrainSuite/QC/qcState.sh'

class subjLevelProcessing(object):
    """
    Nipype workflows for BrainSuite pipelines participant-level processing.

    """
    def __init__(self,STAGES, specs, **keyword_parameters):
        self.specs = specs
        self.stages = STAGES

        #bse
        self.autoParameters = specs.autoParameters
        self.diffusionIterations = specs.diffusionIterations
        self.diffusionConstant = specs.diffusionConstant
        self.edgeDetectionConstant = specs.edgeDetectionConstant
        # bfc
        self.iterativeMode = specs.iterativeMode
        # pvc
        self.spatialPrior = specs.spatialPrior
        # cerebro
        self.costFunction = specs.costFunction
        self.useCentroids = specs.useCentroids
        self.linearConvergence = specs.linearConvergence
        self.warpConvergence = specs.warpConvergence
        self.warpLevel = specs.warpLevel
        # inner cortical mask
        self.tissueFractionThreshold = specs.tissueFractionThreshold

        # bdp
        self.skipDistortionCorr = specs.skipDistortionCorr
        self.phaseEncodingDirection = specs.phaseEncodingDirection
        self.estimateODF_3DShore = specs.estimateODF_3DShore
        self.estimateODF_GQI = specs.estimateODF_GQI
        self.estimateODF_ERFO = specs.estimateODF_ERFO
        self.sigma_GQI = specs.sigma_GQI
        self.ERFO_SNR = specs.ERFO_SNR

        self.echoSpacing = specs.echoSpacing
        self.fieldmapCorrection = specs.fieldmapCorrection
        self.diffusion_time_ms = specs.diffusion_time_ms

        self.epit1corr = specs.epit1corr

        self.bdponly = False

        # svreg
        atlases = {'BCI': '/opt/BrainSuite{0}/svreg/BCI-DNI_brain_atlas/BCI-DNI_brain'.format(BRAINSUITE_VERSION),
                   'BCI-DNI': '/opt/BrainSuite{0}/svreg/BCI-DNI_brain_atlas/BCI-DNI_brain'.format(BRAINSUITE_VERSION),
                   'BSA': '/opt/BrainSuite{0}/svreg/BrainSuiteAtlas1/mri'.format(BRAINSUITE_VERSION),
                   'USCBrain': '/opt/BrainSuite{0}/svreg/USCBrain/USCBrain'.format(BRAINSUITE_VERSION)}
        self.atlas = atlases[str(specs.atlas)]
        self.singleThread = specs.singleThread

        # smoothing
        self.smoothvol = specs.smoothvol
        self.smoothsurf = specs.smoothsurf

        self.cachedir = specs.cache
        
        # bfp
        self.runNSR = specs.runnsr
        self.EnabletNLMPdfFiltering = specs.tnlmpdf

        # svreg
        if keyword_parameters['ATLAS']:
            self.atlas = keyword_parameters['ATLAS']
        self.singleThread = False
        if 'SingleThread' in keyword_parameters:
            if keyword_parameters['SingleThread'] is True:
                self.singleThread = True

        if keyword_parameters['QCDIR']:
            self.QCdir = keyword_parameters['QCDIR']
        else:
            self.QCdir = self.specs.outputdir

        self.cachedir = keyword_parameters['CACHE']

        if 'BDP' in STAGES:
            self.bdpfiles = keyword_parameters['BDP']
            self.BVecBValPair = [keyword_parameters['BVEC'], keyword_parameters['BVAL']]

    def runWorkflow(self, SUBJECT_ID, INPUT_MRI_FILE, WORKFLOW_BASE_DIRECTORY, BFP):
        STAGES = self.stages
        anat = WORKFLOW_BASE_DIRECTORY + '/anat/'
        dwi = WORKFLOW_BASE_DIRECTORY + '/dwi/'
        func = WORKFLOW_BASE_DIRECTORY + '/func/'
        brainsuite_workflow = pe.Workflow(name=WORKFLOW_NAME)
        CACHE_DIRECTORY = self.cachedir
        if self.specs.read_file:
            CACHE_DIRECTORY = self.cachedir + '/' + SUBJECT_ID
            if not os.path.exists(CACHE_DIRECTORY):
                os.makedirs(CACHE_DIRECTORY)
        brainsuite_workflow.base_dir = CACHE_DIRECTORY
        brainsuite_workflow.config['execution']['crashdump_dir'] = CACHE_DIRECTORY + '/' + WORKFLOW_NAME
        brainsuite_workflow.config['execution']['crashfile_format'] = 'txt'

        if 'QC' in self.stages:
            WEBPATH = os.path.join(self.QCdir, SUBJECT_ID)
            if not os.path.exists(WEBPATH):
                os.makedirs(WEBPATH)
            subjstate = os.path.join(WEBPATH, SUBJECT_ID)
            statesDir = os.path.join(subjstate, 'states')
            if not os.path.exists(statesDir):
                os.makedirs(statesDir)
            stagenums = list(stageNumDict.items())
            for stages in range(0, len(stageNumDict)):
                cmd = [QCSTATE, statesDir, str(stagenums[stages][1]), queued]
                subprocess.call(' '.join(cmd), shell=True)
            if 'noBSE' in STAGES:
                cmd = [QCSTATE, statesDir, str(stageNumDict['BSE']), unqueued]
                subprocess.call(' '.join(cmd), shell=True)
            if not 'CSE' in STAGES:
                for stages in range(0, 12):
                    cmd = [QCSTATE, statesDir, str(stagenums[stages][1]), unqueued]
                    subprocess.call(' '.join(cmd), shell=True)
            if not 'BDP' in STAGES:
                cmd = [QCSTATE, statesDir, str(stageNumDict['BDP']), unqueued]
                subprocess.call(' '.join(cmd), shell=True)
            if not 'SVREG' in STAGES:
                for stages in range(12, 16):
                    cmd = [QCSTATE, statesDir, str(stagenums[stages][1]), unqueued]
                    subprocess.call(' '.join(cmd), shell=True)
            if (not 'BDP' in STAGES) or (not 'SVREG' in STAGES):
                for stages in range(16, 29):
                    cmd = [QCSTATE, statesDir, str(stagenums[stages][1]), unqueued]
                    subprocess.call(' '.join(cmd), shell=True)
            if not 'BFP' in STAGES:
                cmd = [QCSTATE, statesDir, str(stageNumDict['BFP']), unqueued]
                subprocess.call(' '.join(cmd), shell=True)
            stagesRun = {}

            qcstateInitObj = pe.Node(interface=bs.QCState(), name='qcstateInitObj')
            qcstateInitObj.inputs.prefix = statesDir
            qcstateInitObj.inputs.state = launched

        t1 = os.path.basename(INPUT_MRI_FILE)

        labeldesc = BRAINSUITE_LABEL_DIRECTORY + LABEL_SUFFIX
        smoothVolStd = '{0} {0} {0}'.format(self.smoothvol)

        ### *--- Copy over T1w file ---* ###
        if 'CSE' in STAGES:
            if not os.path.exists(anat):
                os.makedirs(anat)
            try:
                copyfile(INPUT_MRI_FILE, os.path.join(anat, t1))
            except OSError as e:
                if e.errno == errno.EEXIST:
                    print("No need to copy original T1w file into output directory. Moving on.")
                else:
                    raise

            # ====CSE Inputs and Parameters====
            bseObj = pe.Node(interface=bs.Bse(), name='BSE')
            bseObj.inputs.inputMRIFile = os.path.join(anat, t1)
            bseObj.inputs.diffusionIterations = self.diffusionIterations
            bseObj.inputs.diffusionConstant = self.diffusionConstant  # -d
            bseObj.inputs.edgeDetectionConstant = self.edgeDetectionConstant  # -s
            bseObj.inputs.autoParameters = self.autoParameters

            bfcObj = pe.Node(interface=bs.Bfc(), name='BFC')
            pvcObj = pe.Node(interface=bs.Pvc(), name='PVC')
            cerebroObj = pe.Node(interface=bs.Cerebro(), name='CEREBRO')
            cortexObj = pe.Node(interface=bs.Cortex(), name='CORTEX')
            scrubmaskObj = pe.Node(interface=bs.Scrubmask(), name='SCRUBMASK')
            tcaObj = pe.Node(interface=bs.Tca(), name='TCA')
            dewispObj = pe.Node(interface=bs.Dewisp(), name='DEWISP')
            dfsObj = pe.Node(interface=bs.Dfs(), name='DFS')
            pialmeshObj = pe.Node(interface=bs.Pialmesh(), name='PIALMESH')
            hemisplitObj = pe.Node(interface=bs.Hemisplit(), name='HEMISPLIT')

            bfcObj.inputs.iterativeMode = self.iterativeMode
            cerebroObj.inputs.inputAtlasMRIFile = (BRAINSUITE_ATLAS_DIRECTORY + ATLAS_MRI_SUFFIX)
            cerebroObj.inputs.inputAtlasLabelFile = (BRAINSUITE_ATLAS_DIRECTORY + ATLAS_LABEL_SUFFIX)
            pvcObj.inputs.spatialPrior = self.spatialPrior
            cerebroObj.inputs.useCentroids = self.useCentroids
            cerebroObj.inputs.costFunction = self.costFunction
            cerebroObj.inputs.linearConvergence = self.linearConvergence
            cerebroObj.inputs.warpConvergence = self.warpConvergence
            cerebroObj.inputs.warpLevel = self.warpLevel
            cerebroObj.inputs.inputBrainMaskFile = os.path.join(anat, SUBJECT_ID + '_T1w.mask.nii.gz')
            cortexObj.inputs.tissueFractionThreshold = self.tissueFractionThreshold
            pialmeshObj.inputs.tissueThreshold = 1.05
            tcaObj.inputs.minCorrectionSize = 2500
            tcaObj.inputs.foregroundDelta = 20

            # ====Connect====
            if 'noBSE' not in STAGES:
                brainsuite_workflow.connect(bseObj, 'outputMRIVolume', bfcObj, 'inputMRIFile')
            elif 'noBSE' in STAGES:
                bfcObj.inputs.inputMRIFile = os.path.join(anat, SUBJECT_ID + '_T1w.bse.nii.gz')
                
            brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', pvcObj, 'inputMRIFile')
            brainsuite_workflow.connect(pvcObj, 'outputTissueFractionFile', cortexObj, 'inputTissueFractionFile')

            brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', cerebroObj, 'inputMRIFile')
            brainsuite_workflow.connect(cerebroObj, 'outputLabelVolumeFile', cortexObj, 'inputHemisphereLabelFile')

            brainsuite_workflow.connect(cortexObj, 'outputCerebrumMask', scrubmaskObj, 'inputMaskFile')
            brainsuite_workflow.connect(scrubmaskObj, 'outputMaskFile', tcaObj, 'inputMaskFile')
            brainsuite_workflow.connect(tcaObj, 'outputMaskFile', dewispObj, 'inputMaskFile')
            brainsuite_workflow.connect(dewispObj, 'outputMaskFile', dfsObj, 'inputVolumeFile')
            brainsuite_workflow.connect(dfsObj, 'outputSurfaceFile', pialmeshObj, 'inputSurfaceFile')

            brainsuite_workflow.connect(pvcObj, 'outputTissueFractionFile', pialmeshObj, 'inputTissueFractionFile')
            brainsuite_workflow.connect(cerebroObj, 'outputCerebrumMaskFile', pialmeshObj, 'inputMaskFile')
            brainsuite_workflow.connect(pialmeshObj, 'outputSurfaceFile', hemisplitObj, 'pialSurfaceFile')

            brainsuite_workflow.connect(dfsObj, 'outputSurfaceFile', hemisplitObj, 'inputSurfaceFile')
            brainsuite_workflow.connect(cerebroObj, 'outputLabelVolumeFile', hemisplitObj, 'inputHemisphereLabelFile')

            ds = pe.Node(io.DataSink(), name='HemiSplitDataSink')
            ds.inputs.base_directory = anat

            thickPVCObj = pe.Node(interface=bs.ThicknessPVC(), name='ThickPVC')
            thickPVCInputBase = anat + os.sep + SUBJECT_ID + '_T1w'
            thickPVCObj.inputs.subjectFilePrefix = thickPVCInputBase

            brainsuite_workflow.connect(hemisplitObj, 'outputRightPialHemisphere', ds, '@')
            brainsuite_workflow.connect(hemisplitObj, 'outputLeftPialHemisphere', ds, '@1')
            brainsuite_workflow.connect(ds, 'out_file', thickPVCObj, 'dataSinkDelay')

            if 'QC' in STAGES:
                origT1 = os.path.join(anat, t1)
                bfc = os.path.join(anat, SUBJECT_ID + '_T1w.bfc.nii.gz')
                pvclabel = os.path.join(anat, SUBJECT_ID + '_T1w.pvc.label.nii.gz')
                cerebro = os.path.join(anat, SUBJECT_ID + '_T1w.cerebrum.mask.nii.gz')
                hemilabel = os.path.join(anat, SUBJECT_ID + '_T1w.hemi.label.nii.gz')
                dewisp = os.path.join(anat, SUBJECT_ID + '_T1w.cortex.dewisp.mask.nii.gz')
                dfs = os.path.join(anat, SUBJECT_ID + '_T1w.inner.cortex.dfs')
                Thickdfs = anat + os.sep + SUBJECT_ID + '_T1w.pvc-thickness_0-6mm.left.mid.cortex.dfs ' + \
                           anat + os.sep + SUBJECT_ID + '_T1w.pvc-thickness_0-6mm.right.mid.cortex.dfs'
                pialmesh = os.path.join(anat, SUBJECT_ID + '_T1w.pial.cortex.dfs')
                hemisplit = anat + os.sep + SUBJECT_ID + '_T1w.left.pial.cortex.dfs ' + \
                           anat + os.sep + SUBJECT_ID + '_T1w.right.pial.cortex.dfs'

                if 'noBSE' not in STAGES:
                    volbendbseObj = pe.Node(interface=bs.Volslice(), name='volblendbse')
                    volbendbseObj.inputs.inFile = origT1
                    volbendbseObj.inputs.outFile = '{0}/bse.png'.format(WEBPATH)
                    volbendbseObj.inputs.view = 3 # sagittal

                volbendbfcObj = pe.Node(interface=bs.Volslice(), name='volblendbfc')
                volbendbfcObj.inputs.inFile = bfc
                volbendbfcObj.inputs.outFile = '{0}/bfc.png'.format(WEBPATH)
                volbendbfcObj.inputs.view = 1

                volbendpvcObj = pe.Node(interface=bs.Volslice(), name='volblendpvc')
                volbendpvcObj.inputs.inFile = bfc
                volbendpvcObj.inputs.outFile = '{0}/pvc.png'.format(WEBPATH)
                volbendpvcObj.inputs.labelDesc = labeldesc
                volbendpvcObj.inputs.view = 1 # axial

                volbendHemilabelObj = pe.Node(interface=bs.Volslice(), name='volblendHemilabel')
                volbendHemilabelObj.inputs.inFile = origT1
                volbendHemilabelObj.inputs.outFile = '{0}/hemilabel.png'.format(WEBPATH)
                volbendHemilabelObj.inputs.labelDesc = labeldesc
                volbendHemilabelObj.inputs.view = 2

                volbendcerebroObj = pe.Node(interface=bs.Volslice(), name='volblendcerebro')
                volbendcerebroObj.inputs.inFile = origT1
                volbendcerebroObj.inputs.outFile = '{0}/cerebro.png'.format(WEBPATH)
                volbendcerebroObj.inputs.maskFile = cerebro
                volbendcerebroObj.inputs.view = 3

                volbenddewispObj = pe.Node(interface=bs.Volslice(), name='volblenddewisp')
                volbenddewispObj.inputs.inFile = bfc
                volbenddewispObj.inputs.outFile = '{0}/dewisp.png'.format(WEBPATH)
                volbenddewispObj.inputs.view = 1

                volbenddewispCorObj = pe.Node(interface=bs.Volslice(), name='volblenddewispCor')
                volbenddewispCorObj.inputs.inFile = bfc
                volbenddewispCorObj.inputs.outFile = '{0}/dewispCor.png'.format(WEBPATH)
                volbenddewispCorObj.inputs.view = 2

                dfsrenderdfsLeftObj = pe.Node(interface=bs.RenderDfs(), name='dfsrenderdfsLeft')
                dfsrenderdfsLeftObj.inputs.Surfaces = dfs
                dfsrenderdfsLeftObj.inputs.OutFile = '{0}/dfsLeft.png'.format(WEBPATH)
                dfsrenderdfsLeftObj.inputs.Left = True
                dfsrenderdfsLeftObj.inputs.Zoom = 0.6
                dfsrenderdfsLeftObj.inputs.CenterVol = bfc

                dfsrenderdfsRightObj = pe.Node(interface=bs.RenderDfs(), name='dfsrenderdfsRight')
                dfsrenderdfsRightObj.inputs.Surfaces = dfs
                dfsrenderdfsRightObj.inputs.OutFile = '{0}/dfsRight.png'.format(WEBPATH)
                dfsrenderdfsRightObj.inputs.Right = True
                dfsrenderdfsRightObj.inputs.Zoom = 0.6
                dfsrenderdfsRightObj.inputs.CenterVol = bfc

                dfsrenderdfsSupObj = pe.Node(interface=bs.RenderDfs(), name='dfsrenderdfsSup')
                dfsrenderdfsSupObj.inputs.Surfaces = dfs
                dfsrenderdfsSupObj.inputs.OutFile = '{0}/dfsSup.png'.format(WEBPATH)
                dfsrenderdfsSupObj.inputs.Sup = True
                dfsrenderdfsSupObj.inputs.Zoom = 0.6
                dfsrenderdfsSupObj.inputs.CenterVol = bfc

                dfsrenderdfsInfObj = pe.Node(interface=bs.RenderDfs(), name='dfsrenderdfsInf')
                dfsrenderdfsInfObj.inputs.Surfaces = dfs
                dfsrenderdfsInfObj.inputs.OutFile = '{0}/dfsInf.png'.format(WEBPATH)
                dfsrenderdfsInfObj.inputs.Inf = True
                dfsrenderdfsInfObj.inputs.Zoom = 0.6
                dfsrenderdfsInfObj.inputs.CenterVol = bfc

                dfsrenderhemisplitObj = pe.Node(interface=bs.RenderDfs(), name='dfsrenderhemisplit')
                dfsrenderhemisplitObj.inputs.Surfaces = hemisplit
                dfsrenderhemisplitObj.inputs.OutFile = '{0}/hemisplit.png'.format(WEBPATH)
                dfsrenderhemisplitObj.inputs.Sup = True
                dfsrenderhemisplitObj.inputs.Zoom = 0.6
                dfsrenderhemisplitObj.inputs.CenterVol = bfc
                dfsrenderhemisplitObj.inputs.UseColors = '0 0.5 0.75 1 0.5 0.25'

                dfsrenderThickLeftObj = pe.Node(interface=bs.RenderDfs(), name='dfsrenderThickLeft')
                dfsrenderThickLeftObj.inputs.Surfaces = Thickdfs
                dfsrenderThickLeftObj.inputs.OutFile = '{0}/ThickdfsLeft.png'.format(WEBPATH)
                dfsrenderThickLeftObj.inputs.Left = True
                dfsrenderThickLeftObj.inputs.Zoom = 0.6
                dfsrenderThickLeftObj.inputs.CenterVol = bfc

                dfsrenderThickRightObj = pe.Node(interface=bs.RenderDfs(), name='dfsrenderThickRight')
                dfsrenderThickRightObj.inputs.Surfaces = Thickdfs
                dfsrenderThickRightObj.inputs.OutFile = '{0}/ThickdfsRight.png'.format(WEBPATH)
                dfsrenderThickRightObj.inputs.Right = True
                dfsrenderThickRightObj.inputs.Zoom = 0.6
                dfsrenderThickRightObj.inputs.CenterVol = bfc

                dfsrenderThickSupObj = pe.Node(interface=bs.RenderDfs(), name='dfsrenderThickSup')
                dfsrenderThickSupObj.inputs.Surfaces = Thickdfs
                dfsrenderThickSupObj.inputs.OutFile = '{0}/ThickdfsSup.png'.format(WEBPATH)
                dfsrenderThickSupObj.inputs.Sup = True
                dfsrenderThickSupObj.inputs.Zoom = 0.6
                dfsrenderThickSupObj.inputs.CenterVol = bfc

                dfsrenderThickInfObj = pe.Node(interface=bs.RenderDfs(), name='dfsrenderThickInf')
                dfsrenderThickInfObj.inputs.Surfaces = Thickdfs
                dfsrenderThickInfObj.inputs.OutFile = '{0}/ThickdfsInf.png'.format(WEBPATH)
                dfsrenderThickInfObj.inputs.Inf = True
                dfsrenderThickInfObj.inputs.Zoom = 0.6
                dfsrenderThickInfObj.inputs.CenterVol = bfc

                qcstatevolbendbseObj = pe.Node(interface=bs.QCState(), name='qcstatevolbendbseObj')
                qcstatevolbendbseObj.inputs.prefix = statesDir
                qcstatevolbendbseObj.inputs.stagenum = stageNumDict['BSE']
                qcstatevolbendbseObj.inputs.state = completed

                qcstatevolbendbfcObj = pe.Node(interface=bs.QCState(), name='qcstatevolbendbfcObj')
                qcstatevolbendbfcObj.inputs.prefix = statesDir
                qcstatevolbendbfcObj.inputs.stagenum = stageNumDict['BFC']
                qcstatevolbendbfcObj.inputs.state = completed

                qcstatevolbendpvcObj = pe.Node(interface=bs.QCState(), name='qcstatevolbendpvcObj')
                qcstatevolbendpvcObj.inputs.prefix = statesDir
                qcstatevolbendpvcObj.inputs.stagenum = stageNumDict['PVC']
                qcstatevolbendpvcObj.inputs.state = completed

                qcstatevolbendcerebroObj = pe.Node(interface=bs.QCState(), name='qcstatevolbendcerebroObj')
                qcstatevolbendcerebroObj.inputs.prefix = statesDir
                qcstatevolbendcerebroObj.inputs.stagenum= stageNumDict['CEREBRO']
                qcstatevolbendcerebroObj.inputs.state = completed

                qcstatevolbendcortexObj = pe.Node(interface=bs.QCState(), name='qcstatevolbendcortexObj')
                qcstatevolbendcortexObj.inputs.prefix = statesDir
                qcstatevolbendcortexObj.inputs.stagenum = stageNumDict['CORTEX']
                qcstatevolbendcortexObj.inputs.state = completed

                qcstatevolbendscrubmaskObj = pe.Node(interface=bs.QCState(), name='qcstatevolbendscrubmaskObj')
                qcstatevolbendscrubmaskObj.inputs.prefix = statesDir
                qcstatevolbendscrubmaskObj.inputs.stagenum = stageNumDict['SCRUBMASK']
                qcstatevolbendscrubmaskObj.inputs.state = completed

                qcstatevolbendtcaObj = pe.Node(interface=bs.QCState(), name='qcstatevolbendtcaObj')
                qcstatevolbendtcaObj.inputs.prefix = statesDir
                qcstatevolbendtcaObj.inputs.stagenum = stageNumDict['TCA']
                qcstatevolbendtcaObj.inputs.state = completed

                qcstatevolbenddewispObj = pe.Node(interface=bs.QCState(), name='qcstatevolbenddewispObj')
                qcstatevolbenddewispObj.inputs.prefix = statesDir
                qcstatevolbenddewispObj.inputs.stagenum = stageNumDict['DEWISP']
                qcstatevolbenddewispObj.inputs.state = completed

                qcstatedfsrenderdfsObj = pe.Node(interface=bs.QCState(), name='qcstatedfsrenderdfsObj')
                qcstatedfsrenderdfsObj.inputs.prefix = statesDir
                qcstatedfsrenderdfsObj.inputs.stagenum= stageNumDict['DFS']
                qcstatedfsrenderdfsObj.inputs.state = completed

                qcstatedfsrenderpialmeshObj = pe.Node(interface=bs.QCState(), name='qcstatedfsrenderpialmeshObj')
                qcstatedfsrenderpialmeshObj.inputs.prefix = statesDir
                qcstatedfsrenderpialmeshObj.inputs.stagenum = stageNumDict['PIALMESH']
                qcstatedfsrenderpialmeshObj.inputs.state = completed

                qcstatedfsrenderhemisplitObj = pe.Node(interface=bs.QCState(), name='qcstatedfsrenderhemisplitObj')
                qcstatedfsrenderhemisplitObj.inputs.prefix = statesDir
                qcstatedfsrenderhemisplitObj.inputs.stagenum = stageNumDict['HEMISPLIT']
                qcstatedfsrenderhemisplitObj.inputs.state = completed

                # Connect QC nodes
                if 'noBSE' not in STAGES:
                    brainsuite_workflow.connect(bseObj, 'outputMaskFile', volbendbseObj, 'maskFile')
                    qcbfcLaunch = pe.Node(interface=bs.QCState(), name='qcbfcLaunch')
                    qcbfcLaunch.inputs.prefix = statesDir
                    qcbfcLaunch.inputs.stagenum = stageNumDict['BFC']
                    qcbfcLaunch.inputs.state = launched
                    brainsuite_workflow.connect(bseObj, 'outputMRIVolume', qcbfcLaunch, 'Run')


                brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', volbendbfcObj, 'inFile')
                brainsuite_workflow.connect(pvcObj, 'outputLabelFile', volbendpvcObj, 'labelFile')
                brainsuite_workflow.connect(cerebroObj, 'outputCerebrumMaskFile', volbendcerebroObj, 'maskFile')
                brainsuite_workflow.connect(cerebroObj, 'outputLabelVolumeFile', volbendHemilabelObj, 'labelFile')
                brainsuite_workflow.connect(dewispObj, 'outputMaskFile', volbenddewispObj, 'maskFile')
                brainsuite_workflow.connect(dewispObj, 'outputMaskFile', volbenddewispCorObj, 'maskFile')
                brainsuite_workflow.connect(dfsObj, 'outputSurfaceFile', dfsrenderdfsLeftObj, 'Surfaces')
                brainsuite_workflow.connect(dfsObj, 'outputSurfaceFile', dfsrenderdfsRightObj, 'Surfaces')
                brainsuite_workflow.connect(dfsObj, 'outputSurfaceFile', dfsrenderdfsSupObj, 'Surfaces')
                brainsuite_workflow.connect(dfsObj, 'outputSurfaceFile', dfsrenderdfsInfObj, 'Surfaces')
                brainsuite_workflow.connect(ds, 'out_file', dfsrenderhemisplitObj, 'Surfbilateral')

                qcthickPVCLaunch = pe.Node(interface=bs.QCState(), name='qcthickPVCLaunch')
                qcthickPVCLaunch.inputs.prefix = statesDir
                qcthickPVCLaunch.inputs.stagenum = stageNumDict['THICKPVC']
                qcthickPVCLaunch.inputs.state = launched
                brainsuite_workflow.connect(ds, 'out_file', qcthickPVCLaunch, 'Run')

                dsQCThick = pe.Node(io.DataSink(), name='DATASINK_QCTHICK')
                brainsuite_workflow.connect(thickPVCObj, 'atlasSurfLeftFile', dsQCThick, '@1')
                brainsuite_workflow.connect(thickPVCObj, 'atlasSurfRightFile', dsQCThick, '@2')
                brainsuite_workflow.connect(dsQCThick, 'out_file', dfsrenderThickLeftObj, 'Surfbilateral')
                brainsuite_workflow.connect(dsQCThick, 'out_file', dfsrenderThickRightObj, 'Surfbilateral')
                brainsuite_workflow.connect(dsQCThick, 'out_file', dfsrenderThickSupObj, 'Surfbilateral')
                brainsuite_workflow.connect(dsQCThick, 'out_file', dfsrenderThickInfObj, 'Surfbilateral')

                qcthickPVC = pe.Node(interface=bs.QCState(), name='qcthickPVC')
                qcthickPVC.inputs.prefix = statesDir
                qcthickPVC.inputs.stagenum = stageNumDict['THICKPVC']
                qcthickPVC.inputs.state = completed
                
                brainsuite_workflow.connect(dsQCThick, 'out_file', qcthickPVC, 'Run')


                ###### Connect QC states with the steps ############
                if 'noBSE' not in STAGES:
                    qcstateInitObj.inputs.stagenum = stageNumDict['BSE']
                    brainsuite_workflow.connect(qcstateInitObj, 'OutStateFile', bseObj, 'dummy')
                    brainsuite_workflow.connect(bseObj, 'outputMRIVolume', qcstatevolbendbseObj, 'Run')
                else:
                    qcstateInitObj.inputs.stagenum = stageNumDict['BFC']
                    brainsuite_workflow.connect(qcstateInitObj, 'OutStateFile', bfcObj, 'dummy')
                brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', qcstatevolbendbfcObj, 'Run')
                brainsuite_workflow.connect(pvcObj, 'outputLabelFile', qcstatevolbendpvcObj, 'Run')
                brainsuite_workflow.connect(cerebroObj, 'outputCerebrumMaskFile', qcstatevolbendcerebroObj, 'Run')
                brainsuite_workflow.connect(cortexObj, 'outputCerebrumMask', qcstatevolbendcortexObj, 'Run')
                brainsuite_workflow.connect(scrubmaskObj, 'outputMaskFile', qcstatevolbendscrubmaskObj, 'Run')
                brainsuite_workflow.connect(tcaObj, 'outputMaskFile', qcstatevolbendtcaObj, 'Run')
                brainsuite_workflow.connect(dewispObj, 'outputMaskFile', qcstatevolbenddewispObj, 'Run')
                brainsuite_workflow.connect(dfsObj, 'outputSurfaceFile', qcstatedfsrenderdfsObj, 'Run')
                brainsuite_workflow.connect(pialmeshObj, 'outputSurfaceFile', qcstatedfsrenderpialmeshObj, 'Run')
                brainsuite_workflow.connect(ds, 'out_file', qcstatedfsrenderhemisplitObj, 'Run')

                qcpvcLaunch = pe.Node(interface=bs.QCState(), name='qcpvcLaunch')
                qcpvcLaunch.inputs.prefix = statesDir
                qcpvcLaunch.inputs.stagenum = stageNumDict['PVC']
                qcpvcLaunch.inputs.state = launched
                brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', qcpvcLaunch, 'Run')
                qccerebroLaunch = pe.Node(interface=bs.QCState(), name='qccerebroLaunch')
                qccerebroLaunch.inputs.prefix = statesDir
                qccerebroLaunch.inputs.stagenum = stageNumDict['CEREBRO']
                qccerebroLaunch.inputs.state = launched
                brainsuite_workflow.connect(pvcObj, 'outputLabelFile', qccerebroLaunch, 'Run')
                qccortexLaunch = pe.Node(interface=bs.QCState(), name='qccortexLaunch')
                qccortexLaunch.inputs.prefix = statesDir
                qccortexLaunch.inputs.stagenum = stageNumDict['CORTEX']
                qccortexLaunch.inputs.state = launched
                brainsuite_workflow.connect(cerebroObj, 'outputCerebrumMaskFile', qccortexLaunch, 'Run')
                qcscrubmaskLaunch = pe.Node(interface=bs.QCState(), name='qcscrubmaskLaunch')
                qcscrubmaskLaunch.inputs.prefix = statesDir
                qcscrubmaskLaunch.inputs.stagenum = stageNumDict['SCRUBMASK']
                qcscrubmaskLaunch.inputs.state = launched
                brainsuite_workflow.connect(cortexObj, 'outputCerebrumMask', qcscrubmaskLaunch, 'Run')
                qctcaLaunch = pe.Node(interface=bs.QCState(), name='qctcaLaunch')
                qctcaLaunch.inputs.prefix = statesDir
                qctcaLaunch.inputs.stagenum = stageNumDict['TCA']
                qctcaLaunch.inputs.state = launched
                brainsuite_workflow.connect(scrubmaskObj, 'outputMaskFile', qctcaLaunch, 'Run')
                qcdewispLaunch = pe.Node(interface=bs.QCState(), name='qcdewispLaunch')
                qcdewispLaunch.inputs.prefix = statesDir
                qcdewispLaunch.inputs.stagenum = stageNumDict['DEWISP']
                qcdewispLaunch.inputs.state = launched
                brainsuite_workflow.connect(tcaObj, 'outputMaskFile', qcdewispLaunch, 'Run')
                qcdfsLaunch = pe.Node(interface=bs.QCState(), name='qcdfsLaunch')
                qcdfsLaunch.inputs.prefix = statesDir
                qcdfsLaunch.inputs.stagenum = stageNumDict['DFS']
                qcdfsLaunch.inputs.state = launched
                brainsuite_workflow.connect(dewispObj, 'outputMaskFile', qcdfsLaunch, 'Run')
                qcpialmeshLaunch = pe.Node(interface=bs.QCState(), name='qcpialmeshLaunch')
                qcpialmeshLaunch.inputs.prefix = statesDir
                qcpialmeshLaunch.inputs.stagenum = stageNumDict['PIALMESH']
                qcpialmeshLaunch.inputs.state = launched
                brainsuite_workflow.connect(dfsObj, 'outputSurfaceFile', qcpialmeshLaunch, 'Run')
                qchemisplitLaunch = pe.Node(interface=bs.QCState(), name='qchemisplitLaunch')
                qchemisplitLaunch.inputs.prefix = statesDir
                qchemisplitLaunch.inputs.stagenum = stageNumDict['HEMISPLIT']
                qchemisplitLaunch.inputs.state = launched
                brainsuite_workflow.connect(pialmeshObj, 'outputSurfaceFile', qchemisplitLaunch, 'Run')

                if 'noBSE' not in STAGES:
                    stagesRun.update({
                       'BSE': stageNumDict['BSE']
                    })
                stagesRun.update({
                    'BFC': stageNumDict['BFC'],
                    'PVC': stageNumDict['PVC'],
                    'CEREBRO':stageNumDict['CEREBRO'],
                    'CORTEX':stageNumDict['CORTEX'],
                    'SCRUBMASK':stageNumDict['SCRUBMASK'],
                    'TCA': stageNumDict['TCA'],
                    'DEWISP':stageNumDict['DEWISP'],
                    'DFS': stageNumDict['DFS'],
                    'PIALMESH':stageNumDict['PIALMESH'],
                    'HEMISPLIT':stageNumDict['HEMISPLIT'],
                    'THICKPVC': stageNumDict['THICKPVC']
                })

        if 'BDP' in STAGES:              
            bdpInputBase = dwi + os.sep + SUBJECT_ID + '_dwi'
            
            # If only bdp is set to run, check the bfc file exists
            if not 'CSE' in STAGES:
                if not os.path.exists(anat + os.sep + SUBJECT_ID + '_T1w' + '.bfc.nii.gz'):
                    sys.stdout.write(
                        '*********************************************************************************\n'
                        '*************************** Please run CSE before BDP.***************************\n'
                        '*********************************************************************************\n\n')
                    sys.exit(1)

            if not os.path.exists(dwi):
                os.makedirs(dwi)

            INPUT_DWI_BASE = self.bdpfiles
            bdpObj = pe.Node(interface=bs.BDP(), name='BDP')

            # bdp inputs that will be created. We delay execution of BDP until BFC is done
            bdpObj.inputs.bfcFile = bdpInputBase + '.bfc.nii.gz'
            bdpObj.inputs.inputDiffusionData = INPUT_DWI_BASE + '.nii.gz'
            bdpObj.inputs.BVecBValPair = self.BVecBValPair
            bdpObj.inputs.estimateTensors = True
            bdpObj.inputs.estimateODF_FRACT = True
            bdpObj.inputs.estimateODF_FRT = True
            bdpObj.inputs.skipDistortionCorr = self.skipDistortionCorr
            bdpObj.inputs.phaseEncodingDirection = self.phaseEncodingDirection
            bdpObj.inputs.estimateODF_3DShore = self.estimateODF_3DShore
            bdpObj.inputs.estimateODF_GQI = self.estimateODF_GQI
            bdpObj.inputs.estimateODF_ERFO = self.estimateODF_ERFO
            if self.estimateODF_ERFO or self.estimateODF_3DShore or self.estimateODF_GQI:
                bdpObj.inputs.diffusion_time_ms = self.diffusion_time_ms
            bdpObj.inputs.echoSpacing = self.echoSpacing
            if self.fieldmapCorrection:
                bdpObj.inputs.fieldmapCorrection = bdpInputBase +  self.fieldmapCorrection
            bdpObj.inputs.sigma_GQI = self.sigma_GQI
            bdpObj.inputs.ERFO_SNR = self.ERFO_SNR

            copyBFCtoDWI = pe.Node(interface=bs.copyFile(), name='copyBFCtoDWI')
            copyBFCtoDWI.inputs.inFile = anat + os.sep + SUBJECT_ID + '_T1w.bfc.nii.gz'
            copyBFCtoDWI.inputs.outFile = bdpInputBase + '.bfc.nii.gz'
            copyBSEMasktoDWI = pe.Node(interface=bs.copyFile(), name='copyBSEMasktoDWI')
            copyBSEMasktoDWI.inputs.inFile = anat + os.sep + SUBJECT_ID + '_T1w.mask.nii.gz'
            copyBSEMasktoDWI.inputs.outFile = bdpInputBase + '.mask.nii.gz'
            
            if 'CSE' in STAGES:
                brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', copyBFCtoDWI, 'inFile')
                brainsuite_workflow.connect(bseObj, 'outputMaskFile', copyBSEMasktoDWI, 'inFile')

            brainsuite_workflow.connect(copyBFCtoDWI, 'OutFile', bdpObj, 'bfcFile')
            brainsuite_workflow.connect(copyBSEMasktoDWI, 'OutFile', bdpObj, 'dataSinkDelay')

            if 'QC' in STAGES:
                qcbdpLaunch= pe.Node(interface=bs.QCState(), name='qcbdpLaunch')
                qcbdpLaunch.inputs.prefix = statesDir
                qcbdpLaunch.inputs.stagenum = stageNumDict['BDP']
                qcbdpLaunch.inputs.state = launched
                if not 'CSE' in STAGES:
                    brainsuite_workflow.connect(copyBFCtoDWI, 'OutFile', qcbdpLaunch, 'Run')
                else:
                    brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', qcbdpLaunch, 'Run')

                distcorr = "correct."
                if self.skipDistortionCorr:
                    distcorr = ""
                FA = bdpInputBase + '.dwi.RAS.{0}FA.T1_coord.nii.gz'.format(distcorr)
                bseMask = bdpInputBase + '.D_coord.mask.nii.gz'
                pvcLabel = anat + SUBJECT_ID + '_T1w.pvc.label.nii.gz'

                makeMaskObj = pe.Node(bs.makeMask(), name='makeMaskDWI')
                makeMaskObj.inputs.fileNameAndROIs =' '.join([pvcLabel,"1","2","4","5","6"])
                brainsuite_workflow.connect(bdpObj, 'tensor_coord', makeMaskObj, "Run")

                # FA PVC
                volbendFApvcObj = pe.Node(interface=bs.Volslice(), name='volblendFApvc')
                volbendFApvcObj.inputs.inFile = FA
                volbendFApvcObj.inputs.outFile = '{0}/FApvc.png'.format(WEBPATH)
                volbendFApvcObj.inputs.view = 1  # axial

                # FA axial
                volbendFAObj = pe.Node(interface=bs.Volslice(), name='volblendFA')
                volbendFAObj.inputs.outFile = '{0}/FA.png'.format(WEBPATH)
                volbendFAObj.inputs.view = 1  # axial

                # color FA axial
                volbendColorFAObj = pe.Node(interface=bs.Volslice(), name='volblendColorFA')
                volbendColorFAObj.inputs.outFile = '{0}/colorFA.png'.format(WEBPATH)
                volbendColorFAObj.inputs.view = 1  # axial

                # color mADC axial
                volbendMADCObj = pe.Node(interface=bs.Volslice(), name='volblendMADC')
                volbendMADCObj.inputs.outFile = '{0}/mADC.png'.format(WEBPATH)
                volbendMADCObj.inputs.view = 1  # axial

                # precorr axial
                volbendPreCorrDWIObj = pe.Node(interface=bs.Volslice(), name='volblendPreCorrDWI')
                volbendPreCorrDWIObj.inputs.outFile = '{0}/PreCorrDWI.png'.format(WEBPATH)
                volbendPreCorrDWIObj.inputs.view = 1  # axial
                volbendPreCorrDWIObj.inputs.maskFile = bseMask

                # precorr sag
                volbendPreCorrDWIsagObj = pe.Node(interface=bs.Volslice(), name='volblendPreCorrDWIsag')
                volbendPreCorrDWIsagObj.inputs.outFile = '{0}/PreCorrDWIsag.png'.format(WEBPATH)
                volbendPreCorrDWIsagObj.inputs.view = 3  # axial
                volbendPreCorrDWIsagObj.inputs.maskFile = bseMask

                ### Connect rendering to bdp ####
                brainsuite_workflow.connect(makeMaskObj, 'OutFile', volbendFApvcObj, 'maskFile')
                if self.skipDistortionCorr:
                    brainsuite_workflow.connect(bdpObj, 'FA', volbendFAObj, 'inFile')
                    brainsuite_workflow.connect(bdpObj, 'ColorFA', volbendColorFAObj, 'inFile')
                    brainsuite_workflow.connect(bdpObj, 'MADC', volbendMADCObj, 'inFile')
                else:
                    brainsuite_workflow.connect(bdpObj, 'corrFA', volbendFAObj, 'inFile')
                    brainsuite_workflow.connect(bdpObj, 'corrColorFA', volbendColorFAObj, 'inFile')
                    brainsuite_workflow.connect(bdpObj, 'corrMADC', volbendMADCObj, 'inFile')
                    # postcorr axial
                    volbendPostCorrDWIObj = pe.Node(interface=bs.Volslice(), name='volblendPostCorrDWI')
                    volbendPostCorrDWIObj.inputs.outFile = '{0}/PostCorrDWI.png'.format(WEBPATH)
                    volbendPostCorrDWIObj.inputs.view = 1  # axial
                    volbendPostCorrDWIObj.inputs.maskFile = bseMask
                    # postcorr sag
                    volbendPostCorrDWIsagObj = pe.Node(interface=bs.Volslice(), name='volblendPostCorrDWIsag')
                    volbendPostCorrDWIsagObj.inputs.outFile = '{0}/PostCorrDWIsag.png'.format(WEBPATH)
                    volbendPostCorrDWIsagObj.inputs.view = 3  # axial
                    volbendPostCorrDWIsagObj.inputs.maskFile = bseMask

                    brainsuite_workflow.connect(bdpObj, 'PostCorrDWI', volbendPostCorrDWIObj, 'inFile')
                    brainsuite_workflow.connect(bdpObj, 'PostCorrDWI', volbendPostCorrDWIsagObj, 'inFile')
                brainsuite_workflow.connect(bdpObj, 'PreCorrDWI', volbendPreCorrDWIObj, 'inFile')
                brainsuite_workflow.connect(bdpObj, 'PreCorrDWI', volbendPreCorrDWIsagObj, 'inFile')

                ###### Connect QC states with the steps ############
                qcstateBDP = pe.Node(interface=bs.QCState(), name='qcstateBDP')
                qcstateBDP.inputs.prefix = statesDir
                qcstateBDP.inputs.stagenum = stageNumDict['BDP']
                qcstateBDP.inputs.state = completed

                stagesRun.update({
                    'BDP': stageNumDict['BDP'],
                })

                brainsuite_workflow.connect(bdpObj, 'tensor_coord', qcstateBDP, 'Run')

        if 'SVREG' in STAGES:
            svregInputBase = anat + os.sep + SUBJECT_ID + '_T1w'
            
            if not 'CSE' in STAGES:
                if not os.path.exists(svregInputBase + '.bfc.nii.gz'):
                    sys.stdout.write('**********************************************************************************\n'
                                     '*************************** Please run CSE before SVREG.**************************\n'
                                     '**********************************************************************************\n')
                    sys.exit(1)
            if 'CSE' in STAGES:
                ds0_thick = pe.Node(io.DataSink(), name='DATASINK0THICK')
                brainsuite_workflow.connect(thickPVCObj, 'atlasSurfLeftFile', ds0_thick, '@')
                brainsuite_workflow.connect(thickPVCObj, 'atlasSurfRightFile', ds0_thick, '@1')
                svregObj = pe.Node(interface=bs.SVReg(), name='SVREG')

                # svreg inputs that will be created. We delay execution of SVReg until all CSE and datasink are done
                svregObj.inputs.subjectFilePrefix = svregInputBase
                svregObj.inputs.atlasFilePrefix = self.atlas
                svregObj.inputs.useSingleThreading = self.singleThread

                brainsuite_workflow.connect(ds0_thick, 'out_file', svregObj, 'dataSinkDelay')
            else:
                svregObj = pe.Node(interface=bs.SVReg(), name='SVREG')
                svregObj.inputs.subjectFilePrefix = svregInputBase
                svregObj.inputs.atlasFilePrefix = self.atlas
                svregObj.inputs.useSingleThreading = self.singleThread

            thick2atlasObj = pe.Node(interface=bs.Thickness2Atlas(), name='THICK2ATLAS')
            thick2atlasObj.inputs.subjectFilePrefix = svregInputBase

            brainsuite_workflow.connect(svregObj, 'outputLabelFile', thick2atlasObj, 'dataSinkDelay')

            ds3 = pe.Node(io.DataSink(), name='DATASINK3')
            ds3.inputs.base_directory = anat

            brainsuite_workflow.connect(thick2atlasObj, 'atlasSurfLeftFile', ds3, '@')
            brainsuite_workflow.connect(thick2atlasObj, 'atlasSurfRightFile', ds3, '@1')

            generateXls = pe.Node(interface=bs.GenerateXls(), name='GenXls')
            generateXls.inputs.subjectFilePrefix = svregInputBase
            brainsuite_workflow.connect(ds3, 'out_file', generateXls, 'dataSinkDelay')
            
            #### smooth surface files
            smoothSurfInputBase = anat + os.sep + 'atlas.pvc-thickness_0-6mm'

            smoothSurfLeftObj = pe.Node(interface=bs.SVRegSmoothSurf(), name='SMOOTHSURFLEFT')
            smoothSurfLeftObj.inputs.funcFile = smoothSurfInputBase + '.left.mid.cortex.dfs'
            smoothSurfLeftObj.inputs.outSurface = smoothSurfInputBase + '.smooth{0}mm.left.mid.cortex.dfs'.format(str(self.smoothsurf))
            smoothSurfLeftObj.inputs.param = self.smoothsurf

            smoothSurfRightObj = pe.Node(interface=bs.SVRegSmoothSurf(), name='SMOOTHSURFRIGHT')
            smoothSurfRightObj.inputs.funcFile = smoothSurfInputBase + '.right.mid.cortex.dfs'
            smoothSurfRightObj.inputs.outSurface = smoothSurfInputBase + '.smooth{0}mm.right.mid.cortex.dfs'.format(str(self.smoothsurf))
            smoothSurfRightObj.inputs.param = self.smoothsurf

            smoothVolJacObj = pe.Node(interface=bs.GSmooth(), name='SMOOTHVOL_MAP')
            smoothVolJacObj.inputs.sigma = smoothVolStd
            smoothVolJacObj.inputs.outFile = svregInputBase + '.svreg.inv.jacobian.smooth{0}mm.nii.gz'.format(
                str(self.smoothvol))

            brainsuite_workflow.connect(thick2atlasObj, 'atlasSurfLeftFile', smoothSurfLeftObj, 'inputSurface')
            brainsuite_workflow.connect(thick2atlasObj, 'atlasSurfRightFile', smoothSurfRightObj, 'inputSurface')
            brainsuite_workflow.connect(svregObj, 'JacDetFile', smoothVolJacObj, 'inFile')

            if 'QC' in STAGES:
                if not 'CSE' in STAGES:
                    if 'QC' in STAGES:
                        qcstateInitObj.inputs.stagenum = stageNumDict['SVREG']
                        brainsuite_workflow.connect(qcstateInitObj, 'OutStateFile', svregObj, 'dataSinkDelay')

                if 'CSE' in STAGES:
                    qcsvregLaunch = pe.Node(interface=bs.QCState(), name='qcsvregLaunch')
                    qcsvregLaunch.inputs.prefix = statesDir
                    qcsvregLaunch.inputs.stagenum = stageNumDict['SVREG']
                    qcsvregLaunch.inputs.state = launched
                    brainsuite_workflow.connect(ds0_thick, 'out_file', qcsvregLaunch, 'Run')

                svregLabel = svregInputBase + '.svreg.label.nii.gz'
                SVREGdfs = svregInputBase + '.left.mid.cortex.svreg.dfs' + ' ' + \
                           svregInputBase + '.right.mid.cortex.svreg.dfs'
                bfc = svregInputBase + '.bfc.nii.gz'

                volbendSVRegLabelObj = pe.Node(interface=bs.Volslice(), name='volblendSVRegLabel')
                volbendSVRegLabelObj.inputs.inFile = bfc
                volbendSVRegLabelObj.inputs.outFile = '{0}/svregLabel.png'.format(WEBPATH)
                volbendSVRegLabelObj.inputs.labelDesc = labeldesc
                volbendSVRegLabelObj.inputs.view = 1 # axial

                volbendSVRegLabelCorObj = pe.Node(interface=bs.Volslice(), name='volblendSVRegLabelCor')
                volbendSVRegLabelCorObj.inputs.inFile = bfc
                volbendSVRegLabelCorObj.inputs.outFile = '{0}/svregLabelCor.png'.format(WEBPATH)
                volbendSVRegLabelCorObj.inputs.labelDesc = labeldesc
                volbendSVRegLabelCorObj.inputs.view = 2  # coronal

                volbendSVRegLabelSagObj = pe.Node(interface=bs.Volslice(), name='volblendSVRegLabelSag')
                volbendSVRegLabelSagObj.inputs.inFile = bfc
                volbendSVRegLabelSagObj.inputs.outFile = '{0}/svregLabelSag.png'.format(WEBPATH)
                volbendSVRegLabelSagObj.inputs.labelDesc = labeldesc
                volbendSVRegLabelSagObj.inputs.view = 3  # saggittal

                dfsrenderSVREGdfsLeftObj = pe.Node(interface=bs.RenderDfs(), name='dfsrenderSVREGdfsLeft')
                dfsrenderSVREGdfsLeftObj.inputs.Surfaces = SVREGdfs
                dfsrenderSVREGdfsLeftObj.inputs.OutFile = '{0}/SVREGdfsLeft.png'.format(WEBPATH)
                dfsrenderSVREGdfsLeftObj.inputs.Left = True
                dfsrenderSVREGdfsLeftObj.inputs.Zoom = 0.6
                dfsrenderSVREGdfsLeftObj.inputs.CenterVol = bfc

                dfsrenderSVREGdfsRightObj = pe.Node(interface=bs.RenderDfs(), name='dfsrenderSVREGdfsRight')
                dfsrenderSVREGdfsRightObj.inputs.Surfaces = SVREGdfs
                dfsrenderSVREGdfsRightObj.inputs.OutFile = '{0}/SVREGdfsRight.png'.format(WEBPATH)
                dfsrenderSVREGdfsRightObj.inputs.Right = True
                dfsrenderSVREGdfsRightObj.inputs.Zoom = 0.6
                dfsrenderSVREGdfsRightObj.inputs.CenterVol = bfc

                dfsrenderSVREGdfsInfObj = pe.Node(interface=bs.RenderDfs(), name='dfsrenderSVREGdfsInf')
                dfsrenderSVREGdfsInfObj.inputs.Surfaces = SVREGdfs
                dfsrenderSVREGdfsInfObj.inputs.OutFile = '{0}/SVREGdfsInf.png'.format(WEBPATH)
                dfsrenderSVREGdfsInfObj.inputs.Inf = True
                dfsrenderSVREGdfsInfObj.inputs.Zoom = 0.6
                dfsrenderSVREGdfsInfObj.inputs.CenterVol = bfc

                dfsrenderSVREGdfsSupObj = pe.Node(interface=bs.RenderDfs(), name='dfsrenderSVREGdfsSup')
                dfsrenderSVREGdfsSupObj.inputs.Surfaces = SVREGdfs
                dfsrenderSVREGdfsSupObj.inputs.OutFile = '{0}/SVREGdfsSup.png'.format(WEBPATH)
                dfsrenderSVREGdfsSupObj.inputs.Sup = True
                dfsrenderSVREGdfsSupObj.inputs.Zoom = 0.6
                dfsrenderSVREGdfsSupObj.inputs.CenterVol = bfc

                dfsrenderSVREGdfsAntObj = pe.Node(interface=bs.RenderDfs(), name='dfsrenderSVREGdfsAnt')
                dfsrenderSVREGdfsAntObj.inputs.Surfaces = SVREGdfs
                dfsrenderSVREGdfsAntObj.inputs.OutFile = '{0}/SVREGdfsAnt.png'.format(WEBPATH)
                dfsrenderSVREGdfsAntObj.inputs.Ant = True
                dfsrenderSVREGdfsAntObj.inputs.Zoom = 0.6
                dfsrenderSVREGdfsAntObj.inputs.CenterVol = bfc

                dfsrenderSVREGdfsPosObj = pe.Node(interface=bs.RenderDfs(), name='dfsrenderSVREGdfsPos')
                dfsrenderSVREGdfsPosObj.inputs.Surfaces = SVREGdfs
                dfsrenderSVREGdfsPosObj.inputs.OutFile = '{0}/SVREGdfsPos.png'.format(WEBPATH)
                dfsrenderSVREGdfsPosObj.inputs.Pos = True
                dfsrenderSVREGdfsPosObj.inputs.Zoom = 0.6
                dfsrenderSVREGdfsPosObj.inputs.CenterVol = bfc

                qcstateSVREG = pe.Node(interface=bs.QCState(), name='qcstateSVREG')
                qcstateSVREG.inputs.prefix = statesDir
                qcstateSVREG.inputs.stagenum= stageNumDict['SVREG']
                qcstateSVREG.inputs.state = completed

                ### Connect rendering to SVREG ####
                brainsuite_workflow.connect(svregObj, 'outputLabelFile', volbendSVRegLabelObj, 'labelFile')
                brainsuite_workflow.connect(svregObj, 'outputLabelFile', volbendSVRegLabelCorObj, 'labelFile')
                brainsuite_workflow.connect(svregObj, 'outputLabelFile', volbendSVRegLabelSagObj, 'labelFile')
                brainsuite_workflow.connect(svregObj, 'outputLabelFile', dfsrenderSVREGdfsLeftObj, 'dataSinkDelay')
                brainsuite_workflow.connect(svregObj, 'outputLabelFile', dfsrenderSVREGdfsRightObj, 'dataSinkDelay')
                brainsuite_workflow.connect(svregObj, 'outputLabelFile', dfsrenderSVREGdfsInfObj, 'dataSinkDelay')
                brainsuite_workflow.connect(svregObj, 'outputLabelFile', dfsrenderSVREGdfsSupObj, 'dataSinkDelay')
                brainsuite_workflow.connect(svregObj, 'outputLabelFile', dfsrenderSVREGdfsAntObj, 'dataSinkDelay')
                brainsuite_workflow.connect(svregObj, 'outputLabelFile', dfsrenderSVREGdfsPosObj, 'dataSinkDelay')

                ### Connect QC to SVREG ####
                brainsuite_workflow.connect(generateXls, 'roiwisestats', qcstateSVREG, 'Run')

                qcSurfLeftLaunch = pe.Node(interface=bs.QCState(), name='qcSurfLeftLaunch')
                qcSurfLeftLaunch.inputs.prefix = statesDir
                qcSurfLeftLaunch.inputs.stagenum = stageNumDict['SMOOTHSURFLEFT']
                qcSurfLeftLaunch.inputs.state = launched
                brainsuite_workflow.connect(ds3, 'out_file', qcSurfLeftLaunch, 'Run')
                qcSurfRightLaunch = pe.Node(interface=bs.QCState(), name='qcSurfRightLaunch')
                qcSurfRightLaunch.inputs.prefix = statesDir
                qcSurfRightLaunch.inputs.stagenum = stageNumDict['SMOOTHSURFRIGHT']
                qcSurfRightLaunch.inputs.state = launched
                brainsuite_workflow.connect(ds3, 'out_file', qcSurfRightLaunch, 'Run')
                qcsmoothVolJacLaunch = pe.Node(interface=bs.QCState(), name='qcsmoothVolJacLaunch')
                qcsmoothVolJacLaunch.inputs.prefix = statesDir
                qcsmoothVolJacLaunch.inputs.stagenum = stageNumDict['SMOOTHVOLJAC']
                qcsmoothVolJacLaunch.inputs.state = launched
                brainsuite_workflow.connect(ds3, 'out_file', qcsmoothVolJacLaunch, 'Run')

                qcsmoothSurfLeft = pe.Node(interface=bs.QCState(), name='qcsmoothSurfLeft')
                qcsmoothSurfLeft.inputs.prefix = statesDir
                qcsmoothSurfLeft.inputs.stagenum = stageNumDict['SMOOTHSURFLEFT']
                qcsmoothSurfLeft.inputs.state = completed
                qcsmoothSurfRight = pe.Node(interface=bs.QCState(), name='qcsmoothSurfRight')
                qcsmoothSurfRight.inputs.prefix = statesDir
                qcsmoothSurfRight.inputs.stagenum = stageNumDict['SMOOTHSURFRIGHT']
                qcsmoothSurfRight.inputs.state = completed
                qcsmoothVolJac = pe.Node(interface=bs.QCState(), name='qcsmoothVolJac')
                qcsmoothVolJac.inputs.prefix = statesDir
                qcsmoothVolJac.inputs.stagenum = stageNumDict['SMOOTHVOLJAC']
                qcsmoothVolJac.inputs.state = completed

                brainsuite_workflow.connect(smoothSurfLeftObj, 'smoothSurfFile', qcsmoothSurfLeft, 'Run')
                brainsuite_workflow.connect(smoothSurfRightObj, 'smoothSurfFile', qcsmoothSurfRight, 'Run')
                brainsuite_workflow.connect(smoothVolJacObj, 'smoothFile', qcsmoothVolJac, 'Run')

            stagesRun.update({
                'SVREG': stageNumDict['SVREG'],
                'SMOOTHSURFLEFT': stageNumDict['SMOOTHSURFLEFT'],
                'SMOOTHSURFRIGHT': stageNumDict['SMOOTHSURFRIGHT'],
                'SMOOTHVOLJAC': stageNumDict['SMOOTHVOLJAC']
            })

        if 'SVREG' in STAGES and 'BDP' in STAGES:
            atlasFilePrefix = self.atlas

            ######## Apply Map ########
            applyMapInputBase = dwi + os.sep + SUBJECT_ID + '_dwi'
            applyMapInputBaseSVReg = anat + os.sep + SUBJECT_ID + '_T1w'
            applyMapMapFile = applyMapInputBaseSVReg + '.svreg.inv.map.nii.gz'
            applyMapTargetFile = atlasFilePrefix + '.bfc.nii.gz'
            
            distcorr = "correct."
            distcorrOutput = "corr"
            if self.skipDistortionCorr:
                distcorr = ""
                distcorrOutput = ""

            applyMapFAObj = pe.Node(interface=bs.SVRegApplyMap(), name='APPLYMAPFA')
            applyMapFAObj.inputs.outFile = applyMapInputBase + '.dwi.RAS.{0}atlas.FA.nii.gz'.format(distcorr)
            applyMapFAObj.inputs.targetFile = applyMapTargetFile

            applyMapMDObj = pe.Node(interface=bs.SVRegApplyMap(), name='APPLYMAPMD')
            applyMapMDObj.inputs.outFile = applyMapInputBase + '.dwi.RAS.{0}atlas.MD.nii.gz'.format(distcorr)
            applyMapMDObj.inputs.targetFile = applyMapTargetFile

            applyMapAxialObj = pe.Node(interface=bs.SVRegApplyMap(), name='APPLYMAPAXIAL')
            applyMapAxialObj.inputs.outFile = applyMapInputBase + '.dwi.RAS.{0}atlas.axial.nii.gz'.format(distcorr)
            applyMapAxialObj.inputs.targetFile = applyMapTargetFile

            applyMapRadialObj = pe.Node(interface=bs.SVRegApplyMap(), name='APPLYMAPRADIAL')
            applyMapRadialObj.inputs.outFile = applyMapInputBase + '.dwi.RAS.{0}atlas.radial.nii.gz'.format(distcorr)
            applyMapRadialObj.inputs.targetFile = applyMapTargetFile

            applyMapmADCObj = pe.Node(interface=bs.SVRegApplyMap(), name='APPLYMAPmADC')
            applyMapmADCObj.inputs.outFile = applyMapInputBase + '.dwi.RAS.{0}atlas.mADC.nii.gz'.format(distcorr)
            applyMapmADCObj.inputs.targetFile = applyMapTargetFile

            applyMapFRT_GFAObj = pe.Node(interface=bs.SVRegApplyMap(), name='APPLYMAPFRTGFA')
            applyMapFRT_GFAObj.inputs.outFile = applyMapInputBase + '.dwi.RAS.{0}atlas.FRT_GFA.nii.gz'.format(distcorr)
            applyMapFRT_GFAObj.inputs.targetFile = applyMapTargetFile

            ds5 = pe.Node(io.DataSink(), name='DATASINK5')
            ds5.inputs.base_directory = anat
            
            brainsuite_workflow.connect(svregObj, 'InvMapFile', applyMapFAObj, 'mapFile')
            brainsuite_workflow.connect(svregObj, 'InvMapFile', applyMapMDObj, 'mapFile')
            brainsuite_workflow.connect(svregObj, 'InvMapFile', applyMapAxialObj, 'mapFile')
            brainsuite_workflow.connect(svregObj, 'InvMapFile', applyMapRadialObj, 'mapFile')
            brainsuite_workflow.connect(svregObj, 'InvMapFile', applyMapmADCObj, 'mapFile')
            brainsuite_workflow.connect(svregObj, 'InvMapFile', applyMapFRT_GFAObj, 'mapFile')
                        
            brainsuite_workflow.connect(bdpObj, '%sFA' % distcorrOutput, applyMapFAObj, 'dataFile')
            brainsuite_workflow.connect(bdpObj, '%sMD' % distcorrOutput, applyMapMDObj, 'dataFile')
            brainsuite_workflow.connect(bdpObj, '%sAxial' % distcorrOutput, applyMapAxialObj, 'dataFile')
            brainsuite_workflow.connect(bdpObj, '%sRadial' % distcorrOutput, applyMapRadialObj, 'dataFile')
            brainsuite_workflow.connect(bdpObj, '%sMADC' % distcorrOutput, applyMapmADCObj, 'dataFile')
            brainsuite_workflow.connect(bdpObj, '%sFRTGFA' % distcorrOutput, applyMapFRT_GFAObj, 'dataFile')

            ####### Smooth Vol #######
            smoothVolInputBase = dwi + os.sep + SUBJECT_ID  + '_dwi' + '.dwi.RAS.{0}atlas.'.format(distcorr)

            smoothVolFAObj = pe.Node(interface=bs.GSmooth(), name='SMOOTHVOLFA')
            smoothVolFAObj.inputs.sigma = smoothVolStd
            smoothVolFAObj.inputs.outFile = smoothVolInputBase + 'FA.smooth{0}mm.nii.gz'.format(str(self.smoothvol))

            smoothVolMDObj = pe.Node(interface=bs.GSmooth(), name='SMOOTHVOLMD')
            smoothVolMDObj.inputs.sigma = smoothVolStd
            smoothVolMDObj.inputs.outFile = smoothVolInputBase + 'MD.smooth{0}mm.nii.gz'.format(str(self.smoothvol))

            smoothVolAxialObj = pe.Node(interface=bs.GSmooth(), name='SMOOTHVOLAXIAL')
            smoothVolAxialObj.inputs.sigma = smoothVolStd
            smoothVolAxialObj.inputs.outFile = smoothVolInputBase + 'axial.smooth{0}mm.nii.gz'.format(str(self.smoothvol))

            smoothVolRadialObj = pe.Node(interface=bs.GSmooth(), name='SMOOTHVOLRADIAL')
            smoothVolRadialObj.inputs.sigma = smoothVolStd
            smoothVolRadialObj.inputs.outFile = smoothVolInputBase + 'radial.smooth{0}mm.nii.gz'.format(str(self.smoothvol))

            smoothVolmADCObj = pe.Node(interface=bs.GSmooth(), name='SMOOTHVOLMADC')
            smoothVolmADCObj.inputs.sigma = smoothVolStd
            smoothVolmADCObj.inputs.outFile = smoothVolInputBase + 'mADC.smooth{0}mm.nii.gz'.format(str(self.smoothvol))

            smoothVolFRT_GFAObj = pe.Node(interface=bs.GSmooth(), name='SMOOTHVOLFRTGFA')
            smoothVolFRT_GFAObj.inputs.sigma = smoothVolStd
            smoothVolFRT_GFAObj.inputs.outFile = smoothVolInputBase + 'FRT_GFA.smooth{0}mm.nii.gz'.format(str(self.smoothvol))
            
            brainsuite_workflow.connect(applyMapFAObj, 'mappedFile', smoothVolFAObj, 'inFile')
            brainsuite_workflow.connect(applyMapMDObj, 'mappedFile', smoothVolMDObj, 'inFile')
            brainsuite_workflow.connect(applyMapAxialObj, 'mappedFile', smoothVolAxialObj, 'inFile')
            brainsuite_workflow.connect(applyMapRadialObj, 'mappedFile', smoothVolRadialObj, 'inFile')
            brainsuite_workflow.connect(applyMapmADCObj, 'mappedFile', smoothVolmADCObj, 'inFile')
            brainsuite_workflow.connect(applyMapFRT_GFAObj, 'mappedFile', smoothVolFRT_GFAObj, 'inFile')

            if 'QC' in STAGES:
                qcapplyMapFA = pe.Node(interface=bs.QCState(), name='qcapplyMapFA')
                qcapplyMapFA.inputs.prefix = statesDir
                qcapplyMapFA.inputs.stagenum = stageNumDict['APPLYMAPFA']
                qcapplyMapFA.inputs.state = completed
                
                qcapplyMapMD = pe.Node(interface=bs.QCState(), name='qcapplyMapMD')
                qcapplyMapMD.inputs.prefix = statesDir
                qcapplyMapMD.inputs.stagenum = stageNumDict['APPLYMAPMD']
                qcapplyMapMD.inputs.state = completed
                
                qcapplyMapAxial = pe.Node(interface=bs.QCState(), name='qcapplyMapAxial')
                qcapplyMapAxial.inputs.prefix = statesDir
                qcapplyMapAxial.inputs.stagenum = stageNumDict['APPLYMAPAXIAL']
                qcapplyMapAxial.inputs.state = completed
                
                qcapplyMapRadial = pe.Node(interface=bs.QCState(), name='qcapplyMapRadial')
                qcapplyMapRadial.inputs.prefix = statesDir
                qcapplyMapRadial.inputs.stagenum = stageNumDict['APPLYMAPRADIAL']
                qcapplyMapRadial.inputs.state = completed
                
                qcapplyMapmADC = pe.Node(interface=bs.QCState(), name='qcapplyMapmADC')
                qcapplyMapmADC.inputs.prefix = statesDir
                qcapplyMapmADC.inputs.stagenum = stageNumDict['APPLYMAPMADC']
                qcapplyMapmADC.inputs.state = completed
                
                qcapplyMapFRT_GFA = pe.Node(interface=bs.QCState(), name='qcapplyMapFRT_GFA')
                qcapplyMapFRT_GFA.inputs.prefix = statesDir
                qcapplyMapFRT_GFA.inputs.stagenum = stageNumDict['APPLYMAPFRTGFA']
                qcapplyMapFRT_GFA.inputs.state = completed
                
                brainsuite_workflow.connect(applyMapFAObj, 'mappedFile', qcapplyMapFA, 'Run')
                brainsuite_workflow.connect(applyMapMDObj, 'mappedFile', qcapplyMapMD, 'Run')
                brainsuite_workflow.connect(applyMapAxialObj, 'mappedFile', qcapplyMapAxial, 'Run')
                brainsuite_workflow.connect(applyMapRadialObj, 'mappedFile', qcapplyMapRadial, 'Run')
                brainsuite_workflow.connect(applyMapmADCObj, 'mappedFile', qcapplyMapmADC, 'Run')
                brainsuite_workflow.connect(applyMapFRT_GFAObj, 'mappedFile', qcapplyMapFRT_GFA, 'Run')

                qcapplyMapFALaunch = pe.Node(interface=bs.QCState(), name='qcapplyMapFALaunch')
                qcapplyMapFALaunch.inputs.prefix = statesDir
                qcapplyMapFALaunch.inputs.stagenum = stageNumDict['APPLYMAPFA']
                qcapplyMapFALaunch.inputs.state = launched
                
                qcapplyMapMDLaunch = pe.Node(interface=bs.QCState(), name='qcapplyMapMDLaunch')
                qcapplyMapMDLaunch.inputs.prefix = statesDir
                qcapplyMapMDLaunch.inputs.stagenum = stageNumDict['APPLYMAPMD']
                qcapplyMapMDLaunch.inputs.state = launched
                
                qcapplyMapAxialLaunch = pe.Node(interface=bs.QCState(), name='qcapplyMapAxialLaunch')
                qcapplyMapAxialLaunch.inputs.prefix = statesDir
                qcapplyMapAxialLaunch.inputs.stagenum = stageNumDict['APPLYMAPAXIAL']
                qcapplyMapAxialLaunch.inputs.state = launched
                
                qcapplyMapRadialLaunch = pe.Node(interface=bs.QCState(), name='qcapplyMapRadialLaunch')
                qcapplyMapRadialLaunch.inputs.prefix = statesDir
                qcapplyMapRadialLaunch.inputs.stagenum = stageNumDict['APPLYMAPRADIAL']
                qcapplyMapRadialLaunch.inputs.state = launched
                
                qcapplyMapmADCLaunch = pe.Node(interface=bs.QCState(), name='qcapplyMapmADCLaunch')
                qcapplyMapmADCLaunch.inputs.prefix = statesDir
                qcapplyMapmADCLaunch.inputs.stagenum = stageNumDict['APPLYMAPMADC']
                qcapplyMapmADCLaunch.inputs.state = launched
                
                qcapplyMapFRT_GFALaunch = pe.Node(interface=bs.QCState(), name='qcapplyMapFRT_GFALaunch')
                qcapplyMapFRT_GFALaunch.inputs.prefix = statesDir
                qcapplyMapFRT_GFALaunch.inputs.stagenum = stageNumDict['APPLYMAPFRTGFA']
                qcapplyMapFRT_GFALaunch.inputs.state = launched
                
                ds2 = pe.Node(io.DataSink(), name='DATASINK2')
                ds2.inputs.base_directory = anat
                
                brainsuite_workflow.connect(svregObj, 'InvMapFile', ds2, '@0')
                        
                brainsuite_workflow.connect(bdpObj, '%sFA' % distcorrOutput, ds2, '@')
                brainsuite_workflow.connect(bdpObj, '%sMD' % distcorrOutput, ds2, '@1')
                brainsuite_workflow.connect(bdpObj, '%sAxial' % distcorrOutput, ds2, '@2')
                brainsuite_workflow.connect(bdpObj, '%sRadial' % distcorrOutput, ds2, '@3')
                brainsuite_workflow.connect(bdpObj, '%sMADC' % distcorrOutput, ds2, '@4')
                brainsuite_workflow.connect(bdpObj, '%sFRTGFA' % distcorrOutput, ds2, '@5')
                
                brainsuite_workflow.connect(ds2, 'out_file', qcapplyMapFALaunch, 'Run')
                brainsuite_workflow.connect(ds2, 'out_file', qcapplyMapMDLaunch, 'Run')
                brainsuite_workflow.connect(ds2, 'out_file', qcapplyMapAxialLaunch, 'Run')
                brainsuite_workflow.connect(ds2, 'out_file', qcapplyMapRadialLaunch, 'Run')
                brainsuite_workflow.connect(ds2, 'out_file', qcapplyMapmADCLaunch, 'Run')
                brainsuite_workflow.connect(ds2, 'out_file', qcapplyMapFRT_GFALaunch, 'Run')

                qcsmoothVolFALaunch = pe.Node(interface=bs.QCState(), name='qcsmoothVolFALaunch')
                qcsmoothVolFALaunch.inputs.prefix = statesDir
                qcsmoothVolFALaunch.inputs.stagenum = stageNumDict['SMOOTHVOLFA']
                qcsmoothVolFALaunch.inputs.state = launched
                
                qcsmoothVolMDLaunch = pe.Node(interface=bs.QCState(), name='qcsmoothVolMDLaunch')
                qcsmoothVolMDLaunch.inputs.prefix = statesDir
                qcsmoothVolMDLaunch.inputs.stagenum = stageNumDict['SMOOTHVOLMD']
                qcsmoothVolMDLaunch.inputs.state = launched
                
                qcsmoothVolAxialLaunch = pe.Node(interface=bs.QCState(), name='qcsmoothVolAxialLaunch')
                qcsmoothVolAxialLaunch.inputs.prefix = statesDir
                qcsmoothVolAxialLaunch.inputs.stagenum = stageNumDict['SMOOTHVOLAXIAL']
                qcsmoothVolAxialLaunch.inputs.state = launched
                
                qcsmoothVolRadialLaunch = pe.Node(interface=bs.QCState(), name='qcsmoothVolRadialLaunch')
                qcsmoothVolRadialLaunch.inputs.prefix = statesDir
                qcsmoothVolRadialLaunch.inputs.stagenum = stageNumDict['SMOOTHVOLRADIAL']
                qcsmoothVolRadialLaunch.inputs.state = launched
                
                qcsmoothVolmADCLaunch = pe.Node(interface=bs.QCState(), name='qcsmoothVolmADCLaunch')
                qcsmoothVolmADCLaunch.inputs.prefix = statesDir
                qcsmoothVolmADCLaunch.inputs.stagenum = stageNumDict['SMOOTHVOLMADC']
                qcsmoothVolmADCLaunch.inputs.state = launched
                
                qcsmoothVolFRT_GFALaunch = pe.Node(interface=bs.QCState(), name='qcsmoothVolFRT_GFALaunch')
                qcsmoothVolFRT_GFALaunch.inputs.prefix = statesDir
                qcsmoothVolFRT_GFALaunch.inputs.stagenum = stageNumDict['SMOOTHVOLFRTGFA']
                qcsmoothVolFRT_GFALaunch.inputs.state = launched
                
                brainsuite_workflow.connect(applyMapFAObj, 'mappedFile', qcsmoothVolFALaunch, 'Run')
                brainsuite_workflow.connect(applyMapMDObj, 'mappedFile', qcsmoothVolMDLaunch, 'Run')
                brainsuite_workflow.connect(applyMapAxialObj, 'mappedFile', qcsmoothVolAxialLaunch, 'Run')
                brainsuite_workflow.connect(applyMapRadialObj, 'mappedFile', qcsmoothVolRadialLaunch, 'Run')
                brainsuite_workflow.connect(applyMapmADCObj, 'mappedFile', qcsmoothVolmADCLaunch, 'Run')
                brainsuite_workflow.connect(applyMapFRT_GFAObj, 'mappedFile', qcsmoothVolFRT_GFALaunch, 'Run')

                qcsmoothVolFA = pe.Node(interface=bs.QCState(), name='qcsmoothVolFA')
                qcsmoothVolFA.inputs.prefix = statesDir
                qcsmoothVolFA.inputs.stagenum = stageNumDict['SMOOTHVOLFA']
                qcsmoothVolFA.inputs.state = completed
                
                qcsmoothVolMD = pe.Node(interface=bs.QCState(), name='qcsmoothVolMD')
                qcsmoothVolMD.inputs.prefix = statesDir
                qcsmoothVolMD.inputs.stagenum = stageNumDict['SMOOTHVOLMD']
                qcsmoothVolMD.inputs.state = completed
                
                qcsmoothVolAxial = pe.Node(interface=bs.QCState(), name='qcsmoothVolAxial')
                qcsmoothVolAxial.inputs.prefix = statesDir
                qcsmoothVolAxial.inputs.stagenum = stageNumDict['SMOOTHVOLAXIAL']
                qcsmoothVolAxial.inputs.state = completed
                
                qcsmoothVolRadial = pe.Node(interface=bs.QCState(), name='qcsmoothVolRadial')
                qcsmoothVolRadial.inputs.prefix = statesDir
                qcsmoothVolRadial.inputs.stagenum = stageNumDict['SMOOTHVOLRADIAL']
                qcsmoothVolRadial.inputs.state = completed
                
                qcsmoothVolmADC = pe.Node(interface=bs.QCState(), name='qcsmoothVolmADC')
                qcsmoothVolmADC.inputs.prefix = statesDir
                qcsmoothVolmADC.inputs.stagenum = stageNumDict['SMOOTHVOLMADC']
                qcsmoothVolmADC.inputs.state = completed
                
                qcsmoothVolFRT_GFA = pe.Node(interface=bs.QCState(), name='qcsmoothVolFRT_GFA')
                qcsmoothVolFRT_GFA.inputs.prefix = statesDir
                qcsmoothVolFRT_GFA.inputs.stagenum = stageNumDict['SMOOTHVOLFRTGFA']
                qcsmoothVolFRT_GFA.inputs.state = completed
                
                brainsuite_workflow.connect(smoothVolFAObj, 'smoothFile', qcsmoothVolFA, 'Run')
                brainsuite_workflow.connect(smoothVolMDObj, 'smoothFile', qcsmoothVolMD, 'Run')
                brainsuite_workflow.connect(smoothVolAxialObj, 'smoothFile', qcsmoothVolAxial, 'Run')
                brainsuite_workflow.connect(smoothVolRadialObj, 'smoothFile', qcsmoothVolRadial, 'Run')
                brainsuite_workflow.connect(smoothVolmADCObj, 'smoothFile', qcsmoothVolmADC, 'Run')
                brainsuite_workflow.connect(smoothVolFRT_GFAObj, 'smoothFile', qcsmoothVolFRT_GFA, 'Run')

                stagesRun.update({
                    'APPLYMAPFA' :stageNumDict['APPLYMAPFA'],
                    'APPLYMAPMD' :stageNumDict['APPLYMAPMD'],
                    'APPLYMAPAXIAL' :stageNumDict['APPLYMAPAXIAL'],
                    'APPLYMAPRADIAL':stageNumDict['APPLYMAPRADIAL'],
                    'APPLYMAPMADC':stageNumDict['APPLYMAPMADC'],
                    'APPLYMAPFRTGFA':stageNumDict['APPLYMAPFRTGFA'],
                    'SMOOTHVOLFA':stageNumDict['SMOOTHVOLFA'],
                    'SMOOTHVOLMD':stageNumDict['SMOOTHVOLMD'],
                    'SMOOTHVOLAXIAL':stageNumDict['SMOOTHVOLAXIAL'],
                    'SMOOTHVOLRADIAL':stageNumDict['SMOOTHVOLRADIAL'],
                    'SMOOTHVOLMADC':stageNumDict['SMOOTHVOLMADC'],
                    'SMOOTHVOLFRTGFA':stageNumDict['SMOOTHVOLFRTGFA']
                })

        if 'BFP' in STAGES:
            bfpInputBase = anat + os.sep + SUBJECT_ID + '_T1w'
            BFPoutput = 'GOrdFiltmat'
            if not self.EnabletNLMPdfFiltering:
                BFPoutput = 'GOrdmat'
            
            if not 'CSE' in STAGES or not 'SVREG' in STAGES:
                if not os.path.exists(bfpInputBase + '.bfc.nii.gz') or not os.path.exists(bfpInputBase + '.svreg.label.nii.gz'):
                    sys.stdout.write(
                        '*********************************************************************************\n'
                        '********************* Please run CSE and SVREG before BFP.***********************\n'
                        '*********************************************************************************\n\n')
                    sys.exit(1)
            if not os.path.exists(func):
                os.makedirs(func)

            BFPObjs = []
            for task in range(len(BFP['sess'])):
                BFPObjs.append(pe.Node(interface=bs.BFP(), name='BFP_{0}'.format(BFP['sess'][task])))
                BFPObjs[task].inputs.configini = str(BFP['configini'])
                BFPObjs[task].inputs.t1file = os.path.join(anat, t1)
                BFPObjs[task].inputs.fmrifile = BFP['func'][task]
                BFPObjs[task].inputs.studydir = BFP['studydir']
                BFPObjs[task].inputs.subjID = BFP['subjID']
                BFPObjs[task].inputs.session = BFP['sess'][task]
                BFPObjs[task].inputs.TR = BFP['TR']

            if len(BFP['sess']) > 1:
                for task in range(len(BFP['func'])-1):
                    brainsuite_workflow.connect(BFPObjs[task], BFPoutput, BFPObjs[int(task+1)], 'dataSinkDelay')

            if 'QC' in STAGES:
                pvcLabel = anat + SUBJECT_ID + '_T1w.pvc.label.nii.gz'
                makeMaskBFPpvcObj = pe.Node(bs.makeMask(), name='makeMaskBFPpvc')
                makeMaskBFPpvcObj.inputs.fileNameAndROIs = ' '.join([pvcLabel, "1", "2", "4", "5", "6"])
                
                if 'SVREG' in STAGES:
                    qcBFPLaunch = pe.Node(interface=bs.QCState(), name='qcBFPLaunch')
                    qcBFPLaunch.inputs.prefix = statesDir
                    qcBFPLaunch.inputs.stagenum = stageNumDict['BFP']
                    qcBFPLaunch.inputs.state = launched
                    brainsuite_workflow.connect(thick2atlasObj, 'atlasSurfRightFile', qcBFPLaunch, 'Run')
                    brainsuite_workflow.connect(thick2atlasObj, 'atlasSurfRightFile', makeMaskBFPpvcObj, "Run")
                elif 'CSE' in STAGES:
                    brainsuite_workflow.connect(pvcObj, 'outputLabelFile', makeMaskBFPpvcObj, "Run")
                else:
                    qcstateInitObj.inputs.stagenum = stageNumDict['BFP']
                    brainsuite_workflow.connect(qcstateInitObj, 'OutStateFile', makeMaskBFPpvcObj, "Run")

                brainsuite_workflow.connect(makeMaskBFPpvcObj, 'OutFile', BFPObjs[0], 'dataSinkDelay')

                copySSIMObjs = []
                copyMCOObjs = []
                volbendFunc2T1Objs = []
                
                for task in range(len(BFP['sess'])):
                    BFPQCPrefix = func + BFP['subjID'] + '_' + BFP['sess'][task] + "_bold"

                    ## Copy png files
                    copySSIMObjs.append(pe.Node(interface=bs.copyFile(), name='CopyMCSSIM_{0}'.format(BFP['sess'][task])))
                    copySSIMObjs[task].inputs.outFile = '{0}/ssim{1}.png'.format(WEBPATH, task)

                    copyMCOObjs.append(pe.Node(interface=bs.copyFile(), name='CopyMCO_{0}'.format(BFP['sess'][task])))
                    copyMCOObjs[task].inputs.outFile = '{0}/mco{1}.png'.format(WEBPATH,task)

                    brainsuite_workflow.connect(BFPObjs[task], 'SSIMpng', copySSIMObjs[task], "inFile")
                    brainsuite_workflow.connect(BFPObjs[task], 'MCOpng', copyMCOObjs[task], "inFile")

                    # Func2T1 with PVC label mask
                    volbendFunc2T1Objs.append(pe.Node(interface=bs.Volslice(), name='volblendFunc2T1_{0}'.format(BFP['sess'][task])))
                    volbendFunc2T1Objs[task].inputs.outFile = '{0}/Func2T1{1}.png'.format(WEBPATH, task)
                    volbendFunc2T1Objs[task].inputs.view = 1  # axial
                    
                    ### Connect rendering to BFP ####
                    brainsuite_workflow.connect(makeMaskBFPpvcObj, 'OutFile', volbendFunc2T1Objs[task], 'maskFile')
                    brainsuite_workflow.connect(BFPObjs[task], 'Func2T1', volbendFunc2T1Objs[task], 'inFile')

                qcstateBFP = pe.Node(interface=bs.QCState(), name='qcstateBFP')
                qcstateBFP.inputs.prefix = statesDir
                qcstateBFP.inputs.stagenum = stageNumDict['BFP']
                qcstateBFP.inputs.state = completed

                ### Connect QC to BFP ####
                brainsuite_workflow.connect(BFPObjs[-1], BFPoutput, qcstateBFP, 'Run')

                stagesRun.update({
                    'BFP_{0}'.format(BFP['sess'][-1]): stageNumDict['BFP']
                })

        brainsuite_workflow_return = \
        brainsuite_workflow.run(plugin='MultiProc', plugin_args={'n_procs': int(os.environ['NCPUS']),
                                                                 'memory_gb': int(os.environ['MAXMEM'])},
                                updatehash=False)

        if 'QC' in STAGES:
            err = False
            nodes = list(brainsuite_workflow_return.nbunch_iter())
            for node in range(0,len(nodes)):
                if nodes[node].name in stagesRun:
                    rc = nodes[node].result.runtime.returncode
                    if rc != 0:
                        err = True
                        stagenum = stagesRun[nodes[node].name]
                        cmd = [QCSTATE, statesDir, str(stagenum), errored]
                        subprocess.call(' '.join(cmd), shell=True)
            if err:
                print('Processing for subject %s has completed with error(s). Nipype workflow is located at: %s' % (
                SUBJECT_ID, WORKFLOW_BASE_DIRECTORY))
            else:
                print('Processing for subject %s has completed successfully. Nipype workflow is located at: %s' % (
                SUBJECT_ID, WORKFLOW_BASE_DIRECTORY))


