# -*- coding: utf-8 -*-
"""
Author: Jason Wong
Edit: Yeun Kim, Clayton Jerlow
"""
from __future__ import unicode_literals, print_function

from nipype import config #Set configuration before importing nipype pipeline
from nipype.interfaces.utility import Function
cfg = dict(execution={'remove_unnecessary_outputs' : False}) #We do not want nipype to remove unnecessary outputs
config.update_config(cfg)

import nipype.pipeline.engine as pe
import nipype.interfaces.brainsuite as bs
import nipype.interfaces.io as io
import os
from bids.grabbids import BIDSLayout
from shutil import copyfile
import os
import errno

BRAINSUITE_VERSION= os.environ['BrainSuiteVersion']
ATLAS_MRI_SUFFIX = 'brainsuite.icbm452.lpi.v08a.img'
ATLAS_LABEL_SUFFIX = 'brainsuite.icbm452.v15a.label.img'
WORKFLOW_NAME = 'BrainSuite'
BRAINSUITE_ATLAS_DIRECTORY = "/opt/BrainSuite{0}/atlas/".format(BRAINSUITE_VERSION)
BRAINSUITE_LABEL_DIRECTORY = "/opt/BrainSuite{0}/labeldesc/".format(BRAINSUITE_VERSION)
LABEL_SUFFIX = 'brainsuite_labeldescriptions_30March2018.xml'

class subjLevelProcessing(object):
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
        self.generateStats = specs.generateStats
        self.forcePartialROIStats = specs.forcePartialROIStats

        self.echoSpacing = specs.echoSpacing
        self.fieldmapCorrection = specs.fieldmapCorrection
        self.diffusion_time_ms = specs.diffusion_time_ms

        # svreg
        atlases = {'BCI': '/opt/BrainSuite{0}/svreg/BCI-DNI_brain_atlas/BCI-DNI_brain'.format(BRAINSUITE_VERSION),
                   'BSA': '/opt/BrainSuite{0}/svreg/BrainSuiteAtlas1/mri'.format(BRAINSUITE_VERSION),
                   'USCBrain': '/opt/BrainSuite{0}/svreg/USCBrain/USCBrain'.format(BRAINSUITE_VERSION)}
        self.atlas = atlases[str(specs.atlas)]
        self.singleThread = specs.singleThread

        # smoothing
        self.smoothvol = specs.smoothvol
        self.smoothsurf = specs.smoothsurf

        self.cachedir = specs.cache

        # svreg
        if keyword_parameters['ATLAS']:
            self.atlas = keyword_parameters['ATLAS']
        else:
            self.atlas = 'BCI'
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

    def runWorkflow(self, SUBJECT_ID, INPUT_MRI_FILE, WORKFLOW_BASE_DIRECTORY):
        STAGES = self.stages
        brainsuite_workflow = pe.Workflow(name=WORKFLOW_NAME)
        CACHE_DIRECTORY = self.cachedir
        if self.specs.read_file:
            CACHE_DIRECTORY = self.cachedir+ '/sub-' + SUBJECT_ID
            if not os.path.exists(CACHE_DIRECTORY):
                os.makedirs(CACHE_DIRECTORY)
        brainsuite_workflow.base_dir = CACHE_DIRECTORY

        t1 = INPUT_MRI_FILE.split("/")[-1]

        try:
            copyfile(INPUT_MRI_FILE, os.path.join(CACHE_DIRECTORY, t1))
        except OSError as e:
            if e.errno == errno.EEXIST:
                print("No need to copy T1w file into cache directory. Moving on.")
            else:
                raise

        bseObj = pe.Node(interface=bs.Bse(), name='BSE')

        # ====BSE Inputs and Parameters====
        bseObj.inputs.inputMRIFile = os.path.join(CACHE_DIRECTORY, t1)
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

        # =====Inputs=====

        # Provided input file
        # bseObj.inputs.inputMRIFile = os.path.join("/tmp", t1)

        # ====Parameters====
        # Provided atlas files
        bfcObj.inputs.iterativeMode = self.iterativeMode
        cerebroObj.inputs.inputAtlasMRIFile = (BRAINSUITE_ATLAS_DIRECTORY + ATLAS_MRI_SUFFIX)
        cerebroObj.inputs.inputAtlasLabelFile = (BRAINSUITE_ATLAS_DIRECTORY + ATLAS_LABEL_SUFFIX)
        pvcObj.inputs.spatialPrior = self.spatialPrior
        cerebroObj.inputs.useCentroids = self.useCentroids
        cerebroObj.inputs.costFunction = self.costFunction
        cerebroObj.inputs.linearConvergence = self.linearConvergence
        cerebroObj.inputs.warpConvergence = self.warpConvergence
        cerebroObj.inputs.warpLevel = self.warpLevel
        cortexObj.inputs.tissueFractionThreshold = self.tissueFractionThreshold
        pialmeshObj.inputs.tissueThreshold = 1.05
        tcaObj.inputs.minCorrectionSize = 2500
        tcaObj.inputs.foregroundDelta = 20

        # ====Connect====
        if 'noBSE' not in STAGES:
            brainsuite_workflow.connect(bseObj, 'outputMRIVolume', bfcObj, 'inputMRIFile')
        brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', pvcObj, 'inputMRIFile')
        brainsuite_workflow.connect(pvcObj, 'outputTissueFractionFile', cortexObj, 'inputTissueFractionFile')

        brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', cerebroObj, 'inputMRIFile')
        brainsuite_workflow.connect(bseObj, 'outputMaskFile', cerebroObj, 'inputBrainMaskFile')
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

        ds = pe.Node(io.DataSink(), name='DATASINK')
        ds.inputs.base_directory = WORKFLOW_BASE_DIRECTORY

        # **DataSink connections**
        if 'noBSE' not in STAGES:
            brainsuite_workflow.connect(bseObj, 'outputMRIVolume', ds, '@')
            brainsuite_workflow.connect(bseObj, 'outputMaskFile', ds, '@1')
        brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', ds, '@2')
        brainsuite_workflow.connect(pvcObj, 'outputLabelFile', ds, '@3')
        brainsuite_workflow.connect(pvcObj, 'outputTissueFractionFile', ds, '@4')
        brainsuite_workflow.connect(cerebroObj, 'outputCerebrumMaskFile', ds, '@5')
        brainsuite_workflow.connect(cerebroObj, 'outputLabelVolumeFile', ds, '@6')
        brainsuite_workflow.connect(cerebroObj, 'outputAffineTransformFile', ds, '@7')
        brainsuite_workflow.connect(cerebroObj, 'outputWarpTransformFile', ds, '@8')
        brainsuite_workflow.connect(cortexObj, 'outputCerebrumMask', ds, '@9')
        brainsuite_workflow.connect(scrubmaskObj, 'outputMaskFile', ds, '@10')
        brainsuite_workflow.connect(tcaObj, 'outputMaskFile', ds, '@11')
        brainsuite_workflow.connect(dewispObj, 'outputMaskFile', ds, '@12')
        brainsuite_workflow.connect(dfsObj, 'outputSurfaceFile', ds, '@13')
        brainsuite_workflow.connect(pialmeshObj, 'outputSurfaceFile', ds, '@14')
        brainsuite_workflow.connect(hemisplitObj, 'outputLeftHemisphere', ds, '@15')
        brainsuite_workflow.connect(hemisplitObj, 'outputRightHemisphere', ds, '@16')
        brainsuite_workflow.connect(hemisplitObj, 'outputLeftPialHemisphere', ds, '@17')
        brainsuite_workflow.connect(hemisplitObj, 'outputRightPialHemisphere', ds, '@18')

        thickPVCObj = pe.Node(interface=bs.ThicknessPVC(), name='ThickPVC')
        thickPVCInputBase = WORKFLOW_BASE_DIRECTORY + os.sep + SUBJECT_ID + '_T1w'
        thickPVCObj.inputs.subjectFilePrefix = thickPVCInputBase

        brainsuite_workflow.connect(ds, 'out_file', thickPVCObj, 'dataSinkDelay')

        if 'QC' in STAGES:
            WEBPATH = os.path.join(self.QCdir, SUBJECT_ID)
            if not os.path.exists(WEBPATH):
                os.makedirs(WEBPATH)

            labeldesc = BRAINSUITE_LABEL_DIRECTORY + LABEL_SUFFIX

            origT1 = os.path.join(CACHE_DIRECTORY, t1)
            bseMask = os.path.join(CACHE_DIRECTORY,'BrainSuite', 'BSE', SUBJECT_ID + '_T1w.mask.nii.gz')
            bfc = bfcObj.inputs.inputMRIFile
            pvclabel = os.path.join(CACHE_DIRECTORY,'BrainSuite', 'PVC', SUBJECT_ID + '_T1w.pvc.label.nii.gz')
            cerebro = os.path.join(CACHE_DIRECTORY,'BrainSuite', 'CEREBRO', SUBJECT_ID + '_T1w.cerebrum.mask.nii.gz')
            inner = os.path.join(CACHE_DIRECTORY,'BrainSuite', 'CORTEX', SUBJECT_ID + '_T1w.init.cortex.mask.nii.gz')
            scrub = os.path.join(CACHE_DIRECTORY,'BrainSuite', 'SCRUBMASK', SUBJECT_ID + '_T1w.cortex.scrubbed.mask.nii.gz')
            tca = os.path.join(CACHE_DIRECTORY,'BrainSuite', 'TCA', SUBJECT_ID + '_T1w.cortex.tca.mask.nii.gz')
            dewisp = os.path.join(CACHE_DIRECTORY,'BrainSuite', 'DEWISP', SUBJECT_ID + '_T1w.cortex.dewisp.mask.nii.gz')
            dfs = dfsObj.outputs.outputSurfaceFile
            pialmesh = pialmeshObj.outputs.outputSurfaceFile
            # hemisplit =

            volbendbseObj = pe.Node(interface=bs.Volblend(), name='volblendbse')
            volbendbseObj.inputs.inFile = origT1
            volbendbseObj.inputs.outFile = '{0}/bse.png'.format(WEBPATH)
            volbendbseObj.inputs.maskFile = bseMask
            volbendbseObj.inputs.view = 3 # sagittal

            volbendbfcObj = pe.Node(interface=bs.Volblend(), name='volblendbfc')
            volbendbfcObj.inputs.inFile = bfc
            volbendbfcObj.inputs.outFile = '{0}/bfc.png'.format(WEBPATH)
            volbendbfcObj.inputs.view = 1

            volbendpvcObj = pe.Node(interface=bs.Volblend(), name='volblendpvc')
            volbendpvcObj.inputs.inFile = bfc
            volbendpvcObj.inputs.outFile = '{0}/pvc.png'.format(WEBPATH)
            volbendpvcObj.inputs.labelFile = pvclabel
            volbendpvcObj.inputs.labelDesc = labeldesc
            volbendpvcObj.inputs.view = 2 # coronal

            volbendcerebroObj = pe.Node(interface=bs.Volblend(), name='volblendcerebro')
            volbendcerebroObj.inputs.inFile = bfc
            volbendcerebroObj.inputs.outFile = '{0}/cerebro.png'.format(WEBPATH)
            volbendcerebroObj.inputs.maskFile = cerebro
            volbendcerebroObj.inputs.view = 3

            volbendcortexObj = pe.Node(interface=bs.Volblend(), name='volblendcortex')
            volbendcortexObj.inputs.inFile = bfc
            volbendcortexObj.inputs.outFile = '{0}/cortex.png'.format(WEBPATH)
            volbendcortexObj.inputs.maskFile = inner
            volbendcortexObj.inputs.view = 2

            volbendscrubmaskObj = pe.Node(interface=bs.Volblend(), name='volblendscrubmask')
            volbendscrubmaskObj.inputs.inFile = bfc
            volbendscrubmaskObj.inputs.outFile = '{0}/scrub.png'.format(WEBPATH)
            volbendscrubmaskObj.inputs.maskFile = scrub
            volbendscrubmaskObj.inputs.view =2

            volbendtcaObj = pe.Node(interface=bs.Volblend(), name='volblendtca')
            volbendtcaObj.inputs.inFile = bfc
            volbendtcaObj.inputs.outFile = '{0}/tca.png'.format(WEBPATH)
            volbendtcaObj.inputs.maskFile = tca
            volbendtcaObj.inputs.view = 2

            volbenddewispObj = pe.Node(interface=bs.Volblend(), name='volblenddewisp')
            volbenddewispObj.inputs.inFile = bfc
            volbenddewispObj.inputs.outFile = '{0}/dewisp.png'.format(WEBPATH)
            volbenddewispObj.inputs.maskFile = dewisp
            volbenddewispObj.inputs.view = 2

            dfsrenderdfsObj = pe.Node(interface=bs.DfsRender(), name='dfsrenderdfs')
            dfsrenderdfsObj.inputs.Surfaces = dfs
            dfsrenderdfsObj.inputs.OutFile = '{0}/dfs.png'.format(WEBPATH)
            dfsrenderdfsObj.inputs.Sup = True
            dfsrenderdfsObj.inputs.Zoom = 0.6

            dfsrenderpialmeshObj = pe.Node(interface=bs.DfsRender(), name='dfsrenderpialmesh')
            dfsrenderpialmeshObj.inputs.Surfaces = pialmesh
            dfsrenderpialmeshObj.inputs.OutFile = '{0}/pialmesh.png'.format(WEBPATH)
            dfsrenderpialmeshObj.inputs.Sup = True
            dfsrenderpialmeshObj.inputs.Zoom = 0.6

            # dfsrenderhemisplitObj = pe.Node(interface=bs.DfsRender(), name='dfsrenderhemisplit')
            # dfsrenderhemisplitObj.inputs.Surfaces = hemi
            # dfsrenderhemisplitObj.inputs.OutFile = '{0}/hemisplit.png'.format(WEBPATH)
            # dfsrenderhemisplitObj.inputs.Sup = True
            # dfsrenderhemisplitObj.inputs.Zoom = 0.6

            subjstate = os.path.join(self.specs.outputdir, 'QC', SUBJECT_ID, SUBJECT_ID)

            qcstatevolbendbseObj = pe.Node(interface=bs.QCState(), name='qcstatevolbendbseObj')
            qcstatevolbendbseObj.inputs.filename = subjstate
            qcstatevolbendbseObj.inputs.stagenum = 1

            qcstatevolbendbfcObj = pe.Node(interface=bs.QCState(), name='qcstatevolbendbfcObj')
            qcstatevolbendbfcObj.inputs.filename = subjstate
            qcstatevolbendbfcObj.inputs.stagenum = 2

            qcstatevolbendpvcObj = pe.Node(interface=bs.QCState(), name='qcstatevolbendpvcObj')
            qcstatevolbendpvcObj.inputs.filename = subjstate
            qcstatevolbendpvcObj.inputs.stagenum = 3

            qcstatevolbendcerebroObj = pe.Node(interface=bs.QCState(), name='qcstatevolbendcerebroObj')
            qcstatevolbendcerebroObj.inputs.filename = subjstate
            qcstatevolbendcerebroObj.inputs.stagenum = 4

            qcstatevolbendcortexObj = pe.Node(interface=bs.QCState(), name='qcstatevolbendcortexObj')
            qcstatevolbendcortexObj.inputs.filename = subjstate
            qcstatevolbendcortexObj.inputs.stagenum = 5

            qcstatevolbendscrubmaskObj = pe.Node(interface=bs.QCState(), name='qcstatevolbendscrubmaskObj')
            qcstatevolbendscrubmaskObj.inputs.filename = subjstate
            qcstatevolbendscrubmaskObj.inputs.stagenum = 6

            qcstatevolbendtcaObj = pe.Node(interface=bs.QCState(), name='qcstatevolbendtcaObj')
            qcstatevolbendtcaObj.inputs.filename = subjstate
            qcstatevolbendtcaObj.inputs.stagenum = 7

            qcstatevolbenddewispObj = pe.Node(interface=bs.QCState(), name='qcstatevolbenddewispObj')
            qcstatevolbenddewispObj.inputs.filename = subjstate
            qcstatevolbenddewispObj.inputs.stagenum = 8

            qcstatedfsrenderdfsObj = pe.Node(interface=bs.QCState(), name='qcstatedfsrenderdfsObj')
            qcstatedfsrenderdfsObj.inputs.filename = subjstate
            qcstatedfsrenderdfsObj.inputs.stagenum = 9

            qcstatedfsrenderpialmeshObj = pe.Node(interface=bs.QCState(), name='qcstatedfsrenderpialmeshObj')
            qcstatedfsrenderpialmeshObj.inputs.filename = subjstate
            qcstatedfsrenderpialmeshObj.inputs.stagenum = 10

            # qcstatedfsrenderhemisplitObj = pe.Node(interface=bs.QCState(), name='qcstatedfsrenderhemisplitObj')
            # qcstatedfsrenderhemisplitObj.inputs.filename = os.path.join(self.specs.outputdir, 'QC', SUBJECT_ID, SUBJECT_ID)
            # qcstatedfsrenderhemisplitObj.inputs.stagenum = 11

            # Connect
            brainsuite_workflow.connect(bseObj, 'inputMRIFile', volbendbseObj, 'inFile')
            brainsuite_workflow.connect(volbendbseObj, 'outFile', qcstatevolbendbseObj, 'Run')

            #TODO: if index.html does not exist in QC folder, then run watch.sh

            brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', volbendbfcObj, 'inFile')
            brainsuite_workflow.connect(volbendbfcObj, 'outFile', qcstatevolbendbfcObj, 'Run')

            brainsuite_workflow.connect(pvcObj, 'outputLabelFile', volbendpvcObj, 'dataSinkDelay')
            brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', volbendpvcObj, 'inFile')
            brainsuite_workflow.connect(volbendpvcObj, 'outFile', qcstatevolbendpvcObj, 'Run')

            brainsuite_workflow.connect(cerebroObj, 'outputCerebrumMaskFile', volbendcerebroObj, 'dataSinkDelay')
            brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', volbendcerebroObj, 'inFile')
            brainsuite_workflow.connect(volbendcerebroObj, 'outFile', qcstatevolbendcerebroObj, 'Run')

            brainsuite_workflow.connect(cortexObj, 'outputCerebrumMask', volbendcortexObj, 'dataSinkDelay')
            brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', volbendcortexObj, 'inFile')
            brainsuite_workflow.connect(volbendcortexObj, 'outFile', qcstatevolbendcortexObj, 'Run')

            brainsuite_workflow.connect(scrubmaskObj, 'outputMaskFile', volbendscrubmaskObj, 'dataSinkDelay')
            brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', volbendscrubmaskObj, 'inFile')
            brainsuite_workflow.connect(volbendscrubmaskObj, 'outFile', qcstatevolbendscrubmaskObj, 'Run')

            brainsuite_workflow.connect(tcaObj, 'outputMaskFile', volbendtcaObj, 'dataSinkDelay')
            brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', volbendtcaObj, 'inFile')
            brainsuite_workflow.connect(volbendtcaObj, 'outFile', qcstatevolbendtcaObj, 'Run')

            brainsuite_workflow.connect(dewispObj, 'outputMaskFile', volbenddewispObj, 'dataSinkDelay')
            brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', volbenddewispObj, 'inFile')
            brainsuite_workflow.connect(volbenddewispObj, 'outFile', qcstatevolbenddewispObj, 'Run')

            brainsuite_workflow.connect(dfsObj, 'outputSurfaceFile', dfsrenderdfsObj, 'Surfaces')
            brainsuite_workflow.connect(dfsrenderdfsObj, 'outFile', qcstatedfsrenderdfsObj, 'Run')

            brainsuite_workflow.connect(pialmeshObj, 'outputSurfaceFile', dfsrenderpialmeshObj, 'Surfaces')
            brainsuite_workflow.connect(dfsrenderpialmeshObj, 'outFile', qcstatedfsrenderpialmeshObj, 'Run')

            # brainsuite_workflow.connect(hemisplitObj, 'outputRightPialHemisphere', dfsrenderhemisplitObj, 'Surfaces')
            # brainsuite_workflow.connect(dfsrenderhemisplitObj, 'outFile', qcstatedfsrenderhemisplitObj, 'filename')

        if 'BDP' in STAGES:
            INPUT_DWI_BASE = self.bdpfiles
            bdpObj = pe.Node(interface=bs.BDP(), name='BDP')
            bdpInputBase = WORKFLOW_BASE_DIRECTORY + os.sep + SUBJECT_ID +'_T1w'

            # bdp inputs that will be created. We delay execution of BDP until all CSE and datasink are done
            bdpObj.inputs.bfcFile = bdpInputBase + '.bfc.nii.gz'
            bdpObj.inputs.inputDiffusionData = INPUT_DWI_BASE + '.nii.gz'
            bdpObj.inputs.BVecBValPair = self.BVecBValPair

            bdpObj.inputs.estimateTensors = True
            bdpObj.inputs.estimateODF_FRACT = True
            bdpObj.inputs.estimateODF_FRT = True
            bdpObj.inputs.skipDistortionCorr = self.skipDistortionCorr

            bdpsubdir = '/../dwi'
            bdpObj.inputs.outputSubdir = bdpsubdir

            brainsuite_workflow.connect(ds, 'out_file', bdpObj, 'dataSinkDelay')
            if 'SVREG' in STAGES:
                ds2 = pe.Node(io.DataSink(), name='DATASINK2')
                ds2.inputs.base_directory = WORKFLOW_BASE_DIRECTORY
                brainsuite_workflow.connect(bdpObj, 'tensor_coord', ds2, '@0')

        if 'SVREG' in STAGES:
            svregObj = pe.Node(interface=bs.SVReg(), name='SVREG')
            svregInputBase = WORKFLOW_BASE_DIRECTORY + os.sep + SUBJECT_ID + '_T1w'

            # svreg inputs that will be created. We delay execution of SVReg until all CSE and datasink are done
            svregObj.inputs.subjectFilePrefix = svregInputBase
            svregObj.inputs.atlasFilePrefix = self.atlas
            # svregObj.inputs.atlasFilePrefix = '/opt/BrainSuite{0}/svreg/BCI-DNI_brain_atlas/BCI-DNI_brain'.format(BRAINSUITE_VERSION)
            # if 'ATLAS' in keyword_parameters:
            #     svregObj.inputs.atlasFilePrefix = keyword_parameters['ATLAS']
            # if 'SingleThread' in keyword_parameters:
            #     if 'ON' in keyword_parameters['SingleThread']:
            svregObj.inputs.useSingleThreading = self.singleThread

            brainsuite_workflow.connect(ds, 'out_file', svregObj, 'dataSinkDelay')

            if not 'BDP' in STAGES:
                ds2 = pe.Node(io.DataSink(), name='DATASINK2')
                ds2.inputs.base_directory = WORKFLOW_BASE_DIRECTORY

            brainsuite_workflow.connect(svregObj, 'outputLabelFile', ds2, '@')

            thick2atlasObj = pe.Node(interface=bs.Thickness2Atlas(), name='THICK2ATLAS')
            thick2atlasInputBase = WORKFLOW_BASE_DIRECTORY + os.sep + SUBJECT_ID + '_T1w'
            thick2atlasObj.inputs.subjectFilePrefix = thick2atlasInputBase

            brainsuite_workflow.connect(ds2, 'out_file', thick2atlasObj, 'dataSinkDelay')

            ds3 = pe.Node(io.DataSink(), name='DATASINK3')
            ds3.inputs.base_directory = WORKFLOW_BASE_DIRECTORY

            brainsuite_workflow.connect(thick2atlasObj, 'atlasSurfLeftFile', ds3, '@')
            brainsuite_workflow.connect(thick2atlasObj, 'atlasSurfRightFile', ds3, '@1')


            generateXls = pe.Node(interface=bs.GenerateXls(), name='GenXls')
            generateXls.inputs.subjectFilePrefix = thickPVCInputBase
            brainsuite_workflow.connect(ds3, 'out_file', generateXls, 'dataSinkDelay')


            #### smooth surface
            smoothsurf = self.smoothsurf

            smoothSurfInputBase = WORKFLOW_BASE_DIRECTORY + os.sep + 'atlas.pvc-thickness_0-6mm'

            smoothSurfLeftObj = pe.Node(interface=bs.SVRegSmoothSurf(), name='SMOOTHSURFLEFT')
            smoothSurfLeftObj.inputs.inputSurface = smoothSurfInputBase + '.left.mid.cortex.dfs'
            smoothSurfLeftObj.inputs.funcFile = smoothSurfInputBase + '.left.mid.cortex.dfs'
            smoothSurfLeftObj.inputs.outSurface = smoothSurfInputBase + '.smooth{0}mm.left.mid.cortex.dfs'.format(str(smoothsurf))
            smoothSurfLeftObj.inputs.param = smoothsurf

            smoothSurfRightObj = pe.Node(interface=bs.SVRegSmoothSurf(), name='SMOOTHSURFRIGHT')
            smoothSurfRightObj.inputs.inputSurface = smoothSurfInputBase + '.right.mid.cortex.dfs'
            smoothSurfRightObj.inputs.funcFile = smoothSurfInputBase + '.right.mid.cortex.dfs'
            smoothSurfRightObj.inputs.outSurface = smoothSurfInputBase + '.smooth{0}mm.right.mid.cortex.dfs'.format(str(smoothsurf))
            smoothSurfRightObj.inputs.param = smoothsurf

            brainsuite_workflow.connect(ds3, 'out_file', smoothSurfLeftObj, 'dataSinkDelay')
            brainsuite_workflow.connect(ds3, 'out_file', smoothSurfRightObj, 'dataSinkDelay')

            ## TODO: place svreg.inv.map smoothing here ##

        if 'SVREG' in STAGES and 'BDP' in STAGES:
            bdpsubdir = os.path.dirname(WORKFLOW_BASE_DIRECTORY) + '/dwi'
            atlasFilePrefix = self.atlas

            ######## Apply Map ########
            applyMapInputBase = bdpsubdir + os.sep + SUBJECT_ID + '_T1w' # '_dwi'
            applyMapInputBaseSVReg = WORKFLOW_BASE_DIRECTORY + os.sep + SUBJECT_ID + '_T1w'
            applyMapMapFile = applyMapInputBaseSVReg + '.svreg.inv.map.nii.gz'
            applyMapTargetFile = atlasFilePrefix + '.bfc.nii.gz'

            applyMapFAObj = pe.Node(interface=bs.SVRegApplyMap(), name='APPLYMAP_FA')
            applyMapFAObj.inputs.mapFile = applyMapMapFile
            applyMapFAObj.inputs.dataFile = applyMapInputBase + '.dwi.RAS.correct.FA.T1_coord.nii.gz'
            applyMapFAObj.inputs.outFile = applyMapInputBase + '.dwi.RAS.correct.atlas.FA.nii.gz'
            applyMapFAObj.inputs.targetFile = applyMapTargetFile

            applyMapMDObj = pe.Node(interface=bs.SVRegApplyMap(), name='APPLYMAP_MD')
            applyMapMDObj.inputs.mapFile = applyMapMapFile
            applyMapMDObj.inputs.dataFile = applyMapInputBase + '.dwi.RAS.correct.MD.T1_coord.nii.gz'
            applyMapMDObj.inputs.outFile = applyMapInputBase + '.dwi.RAS.correct.atlas.MD.nii.gz'
            applyMapMDObj.inputs.targetFile = applyMapTargetFile

            applyMapAxialObj = pe.Node(interface=bs.SVRegApplyMap(), name='APPLYMAP_AXIAL')
            applyMapAxialObj.inputs.mapFile = applyMapMapFile
            applyMapAxialObj.inputs.dataFile = applyMapInputBase + '.dwi.RAS.correct.axial.T1_coord.nii.gz'
            applyMapAxialObj.inputs.outFile = applyMapInputBase + '.dwi.RAS.correct.atlas.axial.nii.gz'
            applyMapAxialObj.inputs.targetFile = applyMapTargetFile

            applyMapRadialObj = pe.Node(interface=bs.SVRegApplyMap(), name='APPLYMAP_RADIAL')
            applyMapRadialObj.inputs.mapFile = applyMapMapFile
            applyMapRadialObj.inputs.dataFile = applyMapInputBase + '.dwi.RAS.correct.radial.T1_coord.nii.gz'
            applyMapRadialObj.inputs.outFile = applyMapInputBase + '.dwi.RAS.correct.atlas.radial.nii.gz'
            applyMapRadialObj.inputs.targetFile = applyMapTargetFile

            applyMapmADCObj = pe.Node(interface=bs.SVRegApplyMap(), name='APPLYMAP_mADC')
            applyMapmADCObj.inputs.mapFile = applyMapMapFile
            applyMapmADCObj.inputs.dataFile = applyMapInputBase + '.dwi.RAS.correct.mADC.T1_coord.nii.gz'
            applyMapmADCObj.inputs.outFile = applyMapInputBase + '.dwi.RAS.correct.atlas.mADC.nii.gz'
            applyMapmADCObj.inputs.targetFile = applyMapTargetFile

            applyMapFRT_GFAObj = pe.Node(interface=bs.SVRegApplyMap(), name='APPLYMAP_FRT_GFA')
            applyMapFRT_GFAObj.inputs.mapFile = applyMapMapFile
            applyMapFRT_GFAObj.inputs.dataFile = applyMapInputBase + '.dwi.RAS.correct.FRT_GFA.T1_coord.nii.gz'
            applyMapFRT_GFAObj.inputs.outFile = applyMapInputBase + '.dwi.RAS.correct.atlas.FRT_GFA.nii.gz'
            applyMapFRT_GFAObj.inputs.targetFile = applyMapTargetFile

            ds5 = pe.Node(io.DataSink(), name='DATASINK5')
            ds5.inputs.base_directory = WORKFLOW_BASE_DIRECTORY

            brainsuite_workflow.connect(ds2, 'out_file', applyMapFAObj, 'dataSinkDelay')
            brainsuite_workflow.connect(ds2, 'out_file', applyMapMDObj, 'dataSinkDelay')
            brainsuite_workflow.connect(ds2, 'out_file', applyMapAxialObj, 'dataSinkDelay')
            brainsuite_workflow.connect(ds2, 'out_file', applyMapRadialObj, 'dataSinkDelay')
            brainsuite_workflow.connect(ds2, 'out_file', applyMapmADCObj, 'dataSinkDelay')
            brainsuite_workflow.connect(ds2, 'out_file', applyMapFRT_GFAObj, 'dataSinkDelay')

            ds4 = pe.Node(io.DataSink(), name='DATASINK4')
            ds4.inputs.base_directory = WORKFLOW_BASE_DIRECTORY

            brainsuite_workflow.connect(applyMapFAObj, 'mappedFile', ds4, '@')
            brainsuite_workflow.connect(applyMapMDObj, 'mappedFile', ds4, '@1')
            brainsuite_workflow.connect(applyMapAxialObj, 'mappedFile', ds4, '@2')
            brainsuite_workflow.connect(applyMapRadialObj, 'mappedFile', ds4, '@3')
            brainsuite_workflow.connect(applyMapmADCObj, 'mappedFile', ds4, '@4')
            brainsuite_workflow.connect(applyMapFRT_GFAObj, 'mappedFile', ds4, '@5')


            ####### Smooth Vol #######
            smoothKernel = self.smoothvol
            bdpsubdir = os.path.dirname(WORKFLOW_BASE_DIRECTORY) + '/dwi'
            smoothVolInputBase = bdpsubdir + os.sep + SUBJECT_ID  + '_T1w' + '.dwi.RAS.correct.atlas.'

            smoothVolFAObj = pe.Node(interface=bs.SVRegSmoothVol(), name='SMOOTHVOL_FA')
            smoothVolFAObj.inputs.inFile = smoothVolInputBase + 'FA.nii.gz'
            smoothVolFAObj.inputs.stdx = smoothKernel
            smoothVolFAObj.inputs.stdy = smoothKernel
            smoothVolFAObj.inputs.stdz = smoothKernel
            smoothVolFAObj.inputs.outFile = smoothVolInputBase + 'FA.smooth{0}mm.nii.gz'.format(str(smoothKernel))

            smoothVolMDObj = pe.Node(interface=bs.SVRegSmoothVol(), name='SMOOTHVOL_MD')
            smoothVolMDObj.inputs.inFile = smoothVolInputBase + 'MD.nii.gz'
            smoothVolMDObj.inputs.stdx = smoothKernel
            smoothVolMDObj.inputs.stdy = smoothKernel
            smoothVolMDObj.inputs.stdz = smoothKernel
            smoothVolMDObj.inputs.outFile = smoothVolInputBase + 'MD.smooth{0}mm.nii.gz'.format(str(smoothKernel))

            smoothVolAxialObj = pe.Node(interface=bs.SVRegSmoothVol(), name='SMOOTHVOL_AXIAL')
            smoothVolAxialObj.inputs.inFile = smoothVolInputBase + 'axial.nii.gz'
            smoothVolAxialObj.inputs.stdx = smoothKernel
            smoothVolAxialObj.inputs.stdy = smoothKernel
            smoothVolAxialObj.inputs.stdz = smoothKernel
            smoothVolAxialObj.inputs.outFile = smoothVolInputBase + 'axial.smooth{0}mm.nii.gz'.format(str(smoothKernel))

            smoothVolRadialObj = pe.Node(interface=bs.SVRegSmoothVol(), name='SMOOTHVOL_RADIAL')
            smoothVolRadialObj.inputs.inFile = smoothVolInputBase + 'radial.nii.gz'
            smoothVolRadialObj.inputs.stdx = smoothKernel
            smoothVolRadialObj.inputs.stdy = smoothKernel
            smoothVolRadialObj.inputs.stdz = smoothKernel
            smoothVolRadialObj.inputs.outFile = smoothVolInputBase + 'radial.smooth{0}mm.nii.gz'.format(str(smoothKernel))

            smoothVolmADCObj = pe.Node(interface=bs.SVRegSmoothVol(), name='SMOOTHVOL_mADC')
            smoothVolmADCObj.inputs.inFile = smoothVolInputBase + 'mADC.nii.gz'
            smoothVolmADCObj.inputs.stdx = smoothKernel
            smoothVolmADCObj.inputs.stdy = smoothKernel
            smoothVolmADCObj.inputs.stdz = smoothKernel
            smoothVolmADCObj.inputs.outFile = smoothVolInputBase + 'mADC.smooth{0}mm.nii.gz'.format(str(smoothKernel))

            smoothVolFRT_GFAObj = pe.Node(interface=bs.SVRegSmoothVol(), name='SMOOTHVOL_FRT_GFA')
            smoothVolFRT_GFAObj.inputs.inFile = smoothVolInputBase + 'FRT_GFA.nii.gz'
            smoothVolFRT_GFAObj.inputs.stdx = smoothKernel
            smoothVolFRT_GFAObj.inputs.stdy = smoothKernel
            smoothVolFRT_GFAObj.inputs.stdz = smoothKernel
            smoothVolFRT_GFAObj.inputs.outFile = smoothVolInputBase + 'FRT_GFA.smooth{0}mm.nii.gz'.format(str(smoothKernel))

            smoothVolJacObj = pe.Node(interface=bs.SVRegSmoothVol(), name='SMOOTHVOL_MAP')
            smoothVolJacObj.inputs.inFile = WORKFLOW_BASE_DIRECTORY + os.sep + SUBJECT_ID + '_T1w' + '.svreg.inv.jacobian.nii.gz'
            smoothVolJacObj.inputs.stdx = smoothKernel
            smoothVolJacObj.inputs.stdy = smoothKernel
            smoothVolJacObj.inputs.stdz = smoothKernel
            smoothVolJacObj.inputs.outFile = WORKFLOW_BASE_DIRECTORY + os.sep + SUBJECT_ID + '_T1w' + '.svreg.inv.jacobian.smooth{0}mm.nii.gz'.format(str(smoothKernel))

            brainsuite_workflow.connect(ds4, 'out_file', smoothVolFAObj, 'dataSinkDelay')
            brainsuite_workflow.connect(ds4, 'out_file', smoothVolMDObj, 'dataSinkDelay')
            brainsuite_workflow.connect(ds4, 'out_file', smoothVolAxialObj, 'dataSinkDelay')
            brainsuite_workflow.connect(ds4, 'out_file', smoothVolRadialObj, 'dataSinkDelay')
            brainsuite_workflow.connect(ds4, 'out_file', smoothVolmADCObj, 'dataSinkDelay')
            brainsuite_workflow.connect(ds4, 'out_file', smoothVolFRT_GFAObj, 'dataSinkDelay')
            brainsuite_workflow.connect(ds4, 'out_file', smoothVolJacObj, 'dataSinkDelay')


        brainsuite_workflow.run(plugin='MultiProc', plugin_args={'n_procs': 2}, updatehash=False)

        # Print message when all processing is complete.
        print('Structural processing for subject %s has completed. Nipype workflow is located at: %s' % (
        SUBJECT_ID, WORKFLOW_BASE_DIRECTORY))
