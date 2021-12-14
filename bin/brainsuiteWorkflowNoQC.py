# -*- coding: utf-8 -*-
"""
Author: Jason Wong
Edit: Yeun Kim, Clayton Jerlow
"""
from __future__ import unicode_literals, print_function
import subprocess
from nipype import config #Set configuration before importing nipype pipeline
from nipype.interfaces.utility import Function
cfg = dict(execution={'remove_unnecessary_outputs' : False}) #We do not want nipype to remove unnecessary outputs
config.update_config(cfg)

import nipype.pipeline.engine as pe
import nipype.interfaces.brainsuite as bs
import nipype.interfaces.io as io
from shutil import copyfile
import os
import errno
from QC.makeMask import makeMask

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

        self.epit1corr = specs.epit1corr

        self.bdponly = False

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

        if 'QC' in self.stages:
            WEBPATH = os.path.join(self.QCdir, SUBJECT_ID)
            if not os.path.exists(WEBPATH):
                os.makedirs(WEBPATH)
            subjstate = os.path.join(WEBPATH, SUBJECT_ID)

        t1 = INPUT_MRI_FILE.split("/")[-1]
        t1 = SUBJECT_ID + '_T1w.' + '.'.join(t1.split('.')[1:])
        # TODO: check logic
        SUBJECT_ID = t1.split('.')[0].split('_T1w')[0]


        labeldesc = BRAINSUITE_LABEL_DIRECTORY + LABEL_SUFFIX
        try:
            #TODO: copy and change file name
            copyfile(INPUT_MRI_FILE, os.path.join(CACHE_DIRECTORY, t1))
        except OSError as e:
            if e.errno == errno.EEXIST:
                print("No need to copy T1w file into cache directory. Moving on.")
            else:
                raise

        if 'CSE' in STAGES:
            if not os.path.exists(anat):
                os.makedirs(anat)

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
            ds.inputs.base_directory = anat

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
            thickPVCInputBase = anat + os.sep + SUBJECT_ID + '_T1w'
            thickPVCObj.inputs.subjectFilePrefix = thickPVCInputBase

            brainsuite_workflow.connect(ds, 'out_file', thickPVCObj, 'dataSinkDelay')

            if 'QC' in STAGES:

                origT1 = os.path.join(CACHE_DIRECTORY, t1)
                bseMask = os.path.join(CACHE_DIRECTORY,'BrainSuite', 'BSE', SUBJECT_ID + '_T1w.mask.nii.gz')
                bfc = os.path.join(CACHE_DIRECTORY,'BrainSuite', 'BFC', SUBJECT_ID + '_T1w.bfc.nii.gz')
                pvclabel = os.path.join(CACHE_DIRECTORY,'BrainSuite', 'PVC', SUBJECT_ID + '_T1w.pvc.label.nii.gz')
                cerebro = os.path.join(CACHE_DIRECTORY,'BrainSuite', 'CEREBRO', SUBJECT_ID + '_T1w.cerebrum.mask.nii.gz')
                hemilabel = os.path.join(CACHE_DIRECTORY, 'BrainSuite', 'CEREBRO',
                                         SUBJECT_ID + '_T1w.hemi.label.nii.gz')
                # inner = os.path.join(CACHE_DIRECTORY,'BrainSuite', 'CORTEX', SUBJECT_ID + '_T1w.init.cortex.mask.nii.gz')
                # scrub = os.path.join(CACHE_DIRECTORY,'BrainSuite', 'SCRUBMASK', SUBJECT_ID + '_T1w.cortex.scrubbed.mask.nii.gz')
                # tca = os.path.join(CACHE_DIRECTORY,'BrainSuite', 'TCA', SUBJECT_ID + '_T1w.cortex.tca.mask.nii.gz')
                dewisp = os.path.join(CACHE_DIRECTORY,'BrainSuite', 'DEWISP', SUBJECT_ID + '_T1w.cortex.dewisp.mask.nii.gz')
                dfs = dfsObj.outputs.outputSurfaceFile
                Thickdfs = anat + os.sep + SUBJECT_ID + '_T1w.pvc-thickness_0-6mm.left.mid.cortex.dfs ' + \
                           anat + os.sep + SUBJECT_ID + '_T1w.pvc-thickness_0-6mm.right.mid.cortex.dfs'

                pialmesh = os.path.join(CACHE_DIRECTORY, 'BrainSuite', 'PIALMESH', SUBJECT_ID + '_T1w.pial.cortex.dfs')
                hemisplit = os.path.join(CACHE_DIRECTORY,'BrainSuite', 'HEMISPLIT', SUBJECT_ID + '_T1w.right.pial.cortex.dfs') + \
                            ' ' + os.path.join(CACHE_DIRECTORY, 'BrainSuite', 'HEMISPLIT',
                                         SUBJECT_ID + '_T1w.left.pial.cortex.dfs')

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
                volbendpvcObj.inputs.view = 1 # axial

                volbendHemilabelObj = pe.Node(interface=bs.Volblend(), name='volblendHemilabel')
                volbendHemilabelObj.inputs.inFile = bfc
                volbendHemilabelObj.inputs.outFile = '{0}/hemilabel.png'.format(WEBPATH)
                volbendHemilabelObj.inputs.maskFile = cerebro
                volbendHemilabelObj.inputs.labelFile = hemilabel
                volbendHemilabelObj.inputs.labelDesc = labeldesc
                volbendHemilabelObj.inputs.view = 2

                volbendcerebroObj = pe.Node(interface=bs.Volblend(), name='volblendcerebro')
                volbendcerebroObj.inputs.inFile = bfc
                volbendcerebroObj.inputs.outFile = '{0}/cerebro.png'.format(WEBPATH)
                volbendcerebroObj.inputs.maskFile = cerebro
                volbendcerebroObj.inputs.view = 3

                volbenddewispObj = pe.Node(interface=bs.Volblend(), name='volblenddewisp')
                volbenddewispObj.inputs.inFile = bfc
                volbenddewispObj.inputs.outFile = '{0}/dewisp.png'.format(WEBPATH)
                volbenddewispObj.inputs.maskFile = dewisp
                volbenddewispObj.inputs.view = 1

                volbenddewispCorObj = pe.Node(interface=bs.Volblend(), name='volblenddewispCor')
                volbenddewispCorObj.inputs.inFile = bfc
                volbenddewispCorObj.inputs.outFile = '{0}/dewispCor.png'.format(WEBPATH)
                volbenddewispCorObj.inputs.maskFile = dewisp
                volbenddewispCorObj.inputs.view = 2

                dfsrenderdfsLeftObj = pe.Node(interface=bs.DfsRender(), name='dfsrenderdfsLeft')
                dfsrenderdfsLeftObj.inputs.Surfaces = dfs
                dfsrenderdfsLeftObj.inputs.OutFile = '{0}/dfsLeft.png'.format(WEBPATH)
                dfsrenderdfsLeftObj.inputs.Left = True
                dfsrenderdfsLeftObj.inputs.Zoom = 0.6
                dfsrenderdfsLeftObj.inputs.CenterVol = bfc

                dfsrenderdfsRightObj = pe.Node(interface=bs.DfsRender(), name='dfsrenderdfsRight')
                dfsrenderdfsRightObj.inputs.Surfaces = dfs
                dfsrenderdfsRightObj.inputs.OutFile = '{0}/dfsRight.png'.format(WEBPATH)
                dfsrenderdfsRightObj.inputs.Right = True
                dfsrenderdfsRightObj.inputs.Zoom = 0.6
                dfsrenderdfsRightObj.inputs.CenterVol = bfc

                dfsrenderdfsSupObj = pe.Node(interface=bs.DfsRender(), name='dfsrenderdfsSup')
                dfsrenderdfsSupObj.inputs.Surfaces = dfs
                dfsrenderdfsSupObj.inputs.OutFile = '{0}/dfsSup.png'.format(WEBPATH)
                dfsrenderdfsSupObj.inputs.Sup = True
                dfsrenderdfsSupObj.inputs.Zoom = 0.6
                dfsrenderdfsSupObj.inputs.CenterVol = bfc

                dfsrenderdfsInfObj = pe.Node(interface=bs.DfsRender(), name='dfsrenderdfsInf')
                dfsrenderdfsInfObj.inputs.Surfaces = dfs
                dfsrenderdfsInfObj.inputs.OutFile = '{0}/dfsInf.png'.format(WEBPATH)
                dfsrenderdfsInfObj.inputs.Inf = True
                dfsrenderdfsInfObj.inputs.Zoom = 0.6
                dfsrenderdfsInfObj.inputs.CenterVol = bfc

                dfsrenderhemisplitObj = pe.Node(interface=bs.DfsRender(), name='dfsrenderhemisplit')
                dfsrenderhemisplitObj.inputs.Surfaces = pialmesh
                dfsrenderhemisplitObj.inputs.OutFile = '{0}/hemisplit.png'.format(WEBPATH)
                dfsrenderhemisplitObj.inputs.Sup = True
                dfsrenderhemisplitObj.inputs.Zoom = 0.6
                dfsrenderhemisplitObj.inputs.CenterVol = bfc

                dfsrenderThickLeftObj = pe.Node(interface=bs.DfsRender(), name='dfsrenderThickLeft')
                dfsrenderThickLeftObj.inputs.Surfaces = Thickdfs
                dfsrenderThickLeftObj.inputs.OutFile = '{0}/ThickdfsLeft.png'.format(WEBPATH)
                dfsrenderThickLeftObj.inputs.Left = True
                dfsrenderThickLeftObj.inputs.Zoom = 0.6
                dfsrenderThickLeftObj.inputs.CenterVol = bfc

                dfsrenderThickRightObj = pe.Node(interface=bs.DfsRender(), name='dfsrenderThickRight')
                dfsrenderThickRightObj.inputs.Surfaces = Thickdfs
                dfsrenderThickRightObj.inputs.OutFile = '{0}/ThickdfsRight.png'.format(WEBPATH)
                dfsrenderThickRightObj.inputs.Right = True
                dfsrenderThickRightObj.inputs.Zoom = 0.6
                dfsrenderThickRightObj.inputs.CenterVol = bfc

                dfsrenderThickSupObj = pe.Node(interface=bs.DfsRender(), name='dfsrenderThickSup')
                dfsrenderThickSupObj.inputs.Surfaces = Thickdfs
                dfsrenderThickSupObj.inputs.OutFile = '{0}/ThickdfsSup.png'.format(WEBPATH)
                dfsrenderThickSupObj.inputs.Sup = True
                dfsrenderThickSupObj.inputs.Zoom = 0.6
                dfsrenderThickSupObj.inputs.CenterVol = bfc

                dfsrenderThickInfObj = pe.Node(interface=bs.DfsRender(), name='dfsrenderThickInf')
                dfsrenderThickInfObj.inputs.Surfaces = Thickdfs
                dfsrenderThickInfObj.inputs.OutFile = '{0}/ThickdfsInf.png'.format(WEBPATH)
                dfsrenderThickInfObj.inputs.Inf = True
                dfsrenderThickInfObj.inputs.Zoom = 0.6
                dfsrenderThickInfObj.inputs.CenterVol = bfc


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

                qcstatedfsrenderhemisplitObj = pe.Node(interface=bs.QCState(), name='qcstatedfsrenderhemisplitObj')
                qcstatedfsrenderhemisplitObj.inputs.filename = subjstate
                qcstatedfsrenderhemisplitObj.inputs.stagenum = 11

                # Connect
                brainsuite_workflow.connect(bseObj, 'inputMRIFile', volbendbseObj, 'inFile')
                #TODO: if index.html does not exist in QC folder, then run watch.sh

                brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', volbendbfcObj, 'inFile')

                brainsuite_workflow.connect(pvcObj, 'outputLabelFile', volbendpvcObj, 'dataSinkDelay')

                brainsuite_workflow.connect(cerebroObj, 'outputCerebrumMaskFile', volbendHemilabelObj, 'dataSinkDelay')

                brainsuite_workflow.connect(cerebroObj, 'outputCerebrumMaskFile', volbendcerebroObj, 'dataSinkDelay')

                brainsuite_workflow.connect(dewispObj, 'outputMaskFile', volbenddewispObj, 'dataSinkDelay')

                brainsuite_workflow.connect(dewispObj, 'outputMaskFile', volbenddewispCorObj, 'dataSinkDelay')

                brainsuite_workflow.connect(dfsObj, 'outputSurfaceFile', dfsrenderdfsLeftObj, 'Surfaces')
                brainsuite_workflow.connect(dfsObj, 'outputSurfaceFile', dfsrenderdfsRightObj, 'Surfaces')
                brainsuite_workflow.connect(dfsObj, 'outputSurfaceFile', dfsrenderdfsSupObj, 'Surfaces')
                brainsuite_workflow.connect(dfsObj, 'outputSurfaceFile', dfsrenderdfsInfObj, 'Surfaces')

                # TODO: fix to actual hemi surfaces later
                brainsuite_workflow.connect(pialmeshObj, 'outputSurfaceFile', dfsrenderhemisplitObj, 'Surfaces')

                dsQCThick = pe.Node(io.DataSink(), name='DATASINK_QCTHICK')
                brainsuite_workflow.connect(thickPVCObj, 'atlasSurfLeftFile', dsQCThick, '@1')
                brainsuite_workflow.connect(thickPVCObj, 'atlasSurfRightFile', dsQCThick, '@2')
                brainsuite_workflow.connect(dsQCThick, 'out_file', dfsrenderThickLeftObj, 'dataSinkDelay')
                brainsuite_workflow.connect(dsQCThick, 'out_file', dfsrenderThickRightObj, 'dataSinkDelay')
                brainsuite_workflow.connect(dsQCThick, 'out_file', dfsrenderThickSupObj, 'dataSinkDelay')
                brainsuite_workflow.connect(dsQCThick, 'out_file', dfsrenderThickInfObj, 'dataSinkDelay')


                # brainsuite_workflow.connect(hemisplitObj, 'outputRightPialHemisphere', dfsrenderhemisplitObj, 'Surfaces')
                # brainsuite_workflow.connect(dfsrenderhemisplitObj, 'outFile', qcstatedfsrenderhemisplitObj, 'filename')

                ###### Connect QC states with the steps ############
                brainsuite_workflow.connect(bseObj, 'outputMRIVolume', qcstatevolbendbseObj, 'Run')
                brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', qcstatevolbendbfcObj, 'Run')
                brainsuite_workflow.connect(pvcObj, 'outputLabelFile', qcstatevolbendpvcObj, 'Run')
                brainsuite_workflow.connect(cerebroObj, 'outputCerebrumMaskFile', qcstatevolbendcerebroObj, 'Run')
                brainsuite_workflow.connect(cortexObj, 'outputCerebrumMask', qcstatevolbendcortexObj, 'Run')
                brainsuite_workflow.connect(scrubmaskObj, 'outputMaskFile', qcstatevolbendscrubmaskObj, 'Run')
                brainsuite_workflow.connect(tcaObj, 'outputMaskFile', qcstatevolbendtcaObj, 'Run')
                brainsuite_workflow.connect(dewispObj, 'outputMaskFile', qcstatevolbenddewispObj, 'Run')
                brainsuite_workflow.connect(dfsObj, 'outputSurfaceFile', qcstatedfsrenderdfsObj, 'Run')
                brainsuite_workflow.connect(pialmeshObj, 'outputSurfaceFile', qcstatedfsrenderpialmeshObj, 'Run')
                brainsuite_workflow.connect(hemisplitObj, 'outputRightPialHemisphere', qcstatedfsrenderhemisplitObj, 'Run')

        if 'BDP' in STAGES:
            if not os.path.exists(dwi):
                os.makedirs(dwi)

            INPUT_DWI_BASE = self.bdpfiles
            bdpObj = pe.Node(interface=bs.BDP(), name='BDP')
            bdpInputBase = anat + os.sep + SUBJECT_ID +'_T1w'

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

            if ('CSE' in STAGES) or ('SVREG' in STAGES):
                brainsuite_workflow.connect(ds, 'out_file', bdpObj, 'dataSinkDelay')
                ds2 = pe.Node(io.DataSink(), name='DATASINK2')
                ds2.inputs.base_directory = anat
            else: # 'SVREG' in STAGES:
                ds2 = pe.Node(io.DataSink(), name='DATASINK2')
                ds2.inputs.base_directory = anat
                brainsuite_workflow.connect(bdpObj, 'tensor_coord', ds2, '@0')
            # else:
            #     self.bdponly = True
            #     bdpObj.run()

            if 'QC' in STAGES:

                BDPqcPrefix = dwi + SUBJECT_ID + '_T1w'
                if self.skipDistortionCorr:
                    FA = BDPqcPrefix + '.dwi.RAS.FA.T1_coord.nii.gz'
                    colorFA = BDPqcPrefix + '.dwi.RAS.FA.color.T1_coord.nii.gz'
                    mADC = BDPqcPrefix + '.dwi.RAS.mADC.T1_coord.nii.gz'
                else:
                    FA = BDPqcPrefix + '.dwi.RAS.correct.FA.T1_coord.nii.gz'
                    colorFA = BDPqcPrefix + '.dwi.RAS.correct.FA.color.T1_coord.nii.gz'
                    mADC = BDPqcPrefix + '.dwi.RAS.correct.mADC.T1_coord.nii.gz'
                PreCorrDWI = BDPqcPrefix + '.dwi.RAS.nii.gz'
                PostCorrDWI = BDPqcPrefix + '.dwi.RAS.correct.nii.gz'
                bseMask = BDPqcPrefix + '.D_coord.mask.nii.gz'
                pvcLabel = anat + SUBJECT_ID + '_T1w.pvc.label.nii.gz'

                makeMaskObj = pe.Node(bs.makeMask(), name='makeMaskDWI')
                makeMaskObj.inputs.fileNameAndROIs =' '.join([pvcLabel,"1","2","4","5","6"])
                brainsuite_workflow.connect(bdpObj, 'dummy', makeMaskObj, "Run")

                pvcMask = anat + SUBJECT_ID + '_T1w'  + '.pvc.edge.mask.nii.gz'

                # FA PVC
                volbendFApvcObj = pe.Node(interface=bs.Volblend(), name='volblendFApvc')
                volbendFApvcObj.inputs.inFile = FA
                volbendFApvcObj.inputs.outFile = '{0}/FApvc.png'.format(WEBPATH)
                volbendFApvcObj.inputs.view = 1  # axial
                volbendFApvcObj.inputs.maskFile = pvcMask

                # FA axial
                volbendFAObj = pe.Node(interface=bs.Volblend(), name='volblendFA')
                volbendFAObj.inputs.inFile = FA
                volbendFAObj.inputs.outFile = '{0}/FA.png'.format(WEBPATH)
                volbendFAObj.inputs.view = 1  # axial

                # color FA axial
                volbendColorFAObj = pe.Node(interface=bs.Volblend(), name='volblendColorFA')
                volbendColorFAObj.inputs.inFile = colorFA
                volbendColorFAObj.inputs.outFile = '{0}/colorFA.png'.format(WEBPATH)
                volbendColorFAObj.inputs.view = 1  # axial

                # color mADC axial
                volbendMADCObj = pe.Node(interface=bs.Volblend(), name='volblendMADC')
                volbendMADCObj.inputs.inFile = mADC
                volbendMADCObj.inputs.outFile = '{0}/mADC.png'.format(WEBPATH)
                volbendMADCObj.inputs.view = 1  # axial

                # precorr axial
                volbendPreCorrDWIObj = pe.Node(interface=bs.Volblend(), name='volblendPreCorrDWI')
                volbendPreCorrDWIObj.inputs.inFile = PreCorrDWI
                volbendPreCorrDWIObj.inputs.outFile = '{0}/PreCorrDWI.png'.format(WEBPATH)
                volbendPreCorrDWIObj.inputs.view = 1  # axial
                volbendPreCorrDWIObj.inputs.maskFile = bseMask

                # precorr sag
                volbendPreCorrDWIsagObj = pe.Node(interface=bs.Volblend(), name='volblendPreCorrDWIsag')
                volbendPreCorrDWIsagObj.inputs.inFile = PreCorrDWI
                volbendPreCorrDWIsagObj.inputs.outFile = '{0}/PreCorrDWIsag.png'.format(WEBPATH)
                volbendPreCorrDWIsagObj.inputs.view = 3  # axial
                volbendPreCorrDWIsagObj.inputs.maskFile = bseMask

                ### Connect rendering to bdp ####
                brainsuite_workflow.connect(makeMaskObj, 'OutFile', volbendFApvcObj, 'dataSinkDelay')
                brainsuite_workflow.connect(bdpObj, 'tensor_coord', volbendFAObj, 'dataSinkDelay')
                brainsuite_workflow.connect(bdpObj, 'tensor_coord', volbendColorFAObj, 'dataSinkDelay')
                brainsuite_workflow.connect(bdpObj, 'tensor_coord', volbendMADCObj, 'dataSinkDelay')
                brainsuite_workflow.connect(bdpObj, 'tensor_coord', volbendPreCorrDWIObj, 'dataSinkDelay')
                brainsuite_workflow.connect(bdpObj, 'tensor_coord', volbendPreCorrDWIsagObj, 'dataSinkDelay')

                if not self.skipDistortionCorr:
                    # postcorr axial
                    volbendPostCorrDWIObj = pe.Node(interface=bs.Volblend(), name='volblendPostCorrDWI')
                    volbendPostCorrDWIObj.inputs.inFile = PostCorrDWI
                    volbendPostCorrDWIObj.inputs.outFile = '{0}/PostCorrDWI.png'.format(WEBPATH)
                    volbendPostCorrDWIObj.inputs.view = 1  # axial
                    volbendPostCorrDWIObj.inputs.maskFile = bseMask

                    # postcorr sag
                    volbendPostCorrDWIsagObj = pe.Node(interface=bs.Volblend(), name='volblendPostCorrDWIsag')
                    volbendPostCorrDWIsagObj.inputs.inFile = PostCorrDWI
                    volbendPostCorrDWIsagObj.inputs.outFile = '{0}/PostCorrDWIsag.png'.format(WEBPATH)
                    volbendPostCorrDWIsagObj.inputs.view = 3  # axial
                    volbendPostCorrDWIsagObj.inputs.maskFile = bseMask

                    brainsuite_workflow.connect(bdpObj, 'tensor_coord', volbendPostCorrDWIObj, 'dataSinkDelay')
                    brainsuite_workflow.connect(bdpObj, 'tensor_coord', volbendPostCorrDWIsagObj, 'dataSinkDelay')

                ###### Connect QC states with the steps ############
                qcstateBDP = pe.Node(interface=bs.QCState(), name='qcstateBDP')
                qcstateBDP.inputs.filename = subjstate
                qcstateBDP.inputs.stagenum = 12

                brainsuite_workflow.connect(bdpObj, 'tensor_coord', qcstateBDP, 'Run')

        if 'SVREG' in STAGES:
            if 'CSE' in STAGES:
                ds0_thick = pe.Node(io.DataSink(), name='DATASINK0THICK')
                brainsuite_workflow.connect(thickPVCObj, 'atlasSurfLeftFile', ds0_thick, '@')
                brainsuite_workflow.connect(thickPVCObj, 'atlasSurfRightFile', ds0_thick, '@1')
                svregObj = pe.Node(interface=bs.SVReg(), name='SVREG')
                svregInputBase = anat + os.sep + SUBJECT_ID + '_T1w'

                # svreg inputs that will be created. We delay execution of SVReg until all CSE and datasink are done
                svregObj.inputs.subjectFilePrefix = svregInputBase
                svregObj.inputs.atlasFilePrefix = self.atlas
                # svregObj.inputs.atlasFilePrefix = '/opt/BrainSuite{0}/svreg/BCI-DNI_brain_atlas/BCI-DNI_brain'.format(BRAINSUITE_VERSION)
                # if 'ATLAS' in keyword_parameters:
                #     svregObj.inputs.atlasFilePrefix = keyword_parameters['ATLAS']
                # if 'SingleThread' in keyword_parameters:
                #     if 'ON' in keyword_parameters['SingleThread']:
                svregObj.inputs.useSingleThreading = self.singleThread

                brainsuite_workflow.connect(ds0_thick, 'out_file', svregObj, 'dataSinkDelay')
            else:
                thickPVCInputBase = anat + os.sep + SUBJECT_ID + '_T1w'
                svregObj = pe.Node(interface=bs.SVReg(), name='SVREG')
                svregInputBase = anat + os.sep + SUBJECT_ID + '_T1w'
                svregObj.inputs.subjectFilePrefix = svregInputBase
                svregObj.inputs.atlasFilePrefix = self.atlas
                svregObj.inputs.useSingleThreading = self.singleThread

            if not 'BDP' in STAGES:
                ds2 = pe.Node(io.DataSink(), name='DATASINK2')
                ds2.inputs.base_directory = anat

            brainsuite_workflow.connect(svregObj, 'outputLabelFile', ds2, '@')

            thick2atlasObj = pe.Node(interface=bs.Thickness2Atlas(), name='THICK2ATLAS')
            thick2atlasInputBase = anat + os.sep + SUBJECT_ID + '_T1w'
            thick2atlasObj.inputs.subjectFilePrefix = thick2atlasInputBase

            brainsuite_workflow.connect(ds2, 'out_file', thick2atlasObj, 'dataSinkDelay')

            ds3 = pe.Node(io.DataSink(), name='DATASINK3')
            ds3.inputs.base_directory = anat

            brainsuite_workflow.connect(thick2atlasObj, 'atlasSurfLeftFile', ds3, '@')
            brainsuite_workflow.connect(thick2atlasObj, 'atlasSurfRightFile', ds3, '@1')


            generateXls = pe.Node(interface=bs.GenerateXls(), name='GenXls')
            generateXls.inputs.subjectFilePrefix = thickPVCInputBase
            brainsuite_workflow.connect(ds3, 'out_file', generateXls, 'dataSinkDelay')

            if 'QC' in STAGES:

                svregLabel = anat + SUBJECT_ID + '_T1w.svreg.label.nii.gz'
                SVREGdfs = anat + SUBJECT_ID + '_T1w.left.mid.cortex.svreg.dfs' + ' ' + \
                           anat + SUBJECT_ID + '_T1w.right.mid.cortex.svreg.dfs'
                bfc = anat + SUBJECT_ID + '_T1w.bfc.nii.gz'

                volbendSVRegLabelObj = pe.Node(interface=bs.Volblend(), name='volblendSVRegLabel')
                volbendSVRegLabelObj.inputs.inFile = bfc
                volbendSVRegLabelObj.inputs.outFile = '{0}/svregLabel.png'.format(WEBPATH)
                volbendSVRegLabelObj.inputs.labelFile = svregLabel
                volbendSVRegLabelObj.inputs.labelDesc = labeldesc
                volbendSVRegLabelObj.inputs.view = 1 # axial

                volbendSVRegLabelCorObj = pe.Node(interface=bs.Volblend(), name='volblendSVRegLabelCor')
                volbendSVRegLabelCorObj.inputs.inFile = bfc
                volbendSVRegLabelCorObj.inputs.outFile = '{0}/svregLabelCor.png'.format(WEBPATH)
                volbendSVRegLabelCorObj.inputs.labelFile = svregLabel
                volbendSVRegLabelCorObj.inputs.labelDesc = labeldesc
                volbendSVRegLabelCorObj.inputs.view = 2  # coronal

                volbendSVRegLabelSagObj = pe.Node(interface=bs.Volblend(), name='volblendSVRegLabelSag')
                volbendSVRegLabelSagObj.inputs.inFile = bfc
                volbendSVRegLabelSagObj.inputs.outFile = '{0}/svregLabelSag.png'.format(WEBPATH)
                volbendSVRegLabelSagObj.inputs.labelFile = svregLabel
                volbendSVRegLabelSagObj.inputs.labelDesc = labeldesc
                volbendSVRegLabelSagObj.inputs.view = 3  # saggittal

                dfsrenderSVREGdfsLeftObj = pe.Node(interface=bs.DfsRender(), name='dfsrenderSVREGdfsLeft')
                dfsrenderSVREGdfsLeftObj.inputs.Surfaces = SVREGdfs
                dfsrenderSVREGdfsLeftObj.inputs.OutFile = '{0}/SVREGdfsLeft.png'.format(WEBPATH)
                dfsrenderSVREGdfsLeftObj.inputs.Left = True
                dfsrenderSVREGdfsLeftObj.inputs.Zoom = 0.6
                dfsrenderSVREGdfsLeftObj.inputs.CenterVol = bfc

                dfsrenderSVREGdfsRightObj = pe.Node(interface=bs.DfsRender(), name='dfsrenderSVREGdfsRight')
                dfsrenderSVREGdfsRightObj.inputs.Surfaces = SVREGdfs
                dfsrenderSVREGdfsRightObj.inputs.OutFile = '{0}/SVREGdfsRight.png'.format(WEBPATH)
                dfsrenderSVREGdfsRightObj.inputs.Right = True
                dfsrenderSVREGdfsRightObj.inputs.Zoom = 0.6
                dfsrenderSVREGdfsRightObj.inputs.CenterVol = bfc

                dfsrenderSVREGdfsInfObj = pe.Node(interface=bs.DfsRender(), name='dfsrenderSVREGdfsInf')
                dfsrenderSVREGdfsInfObj.inputs.Surfaces = SVREGdfs
                dfsrenderSVREGdfsInfObj.inputs.OutFile = '{0}/SVREGdfsInf.png'.format(WEBPATH)
                dfsrenderSVREGdfsInfObj.inputs.Inf = True
                dfsrenderSVREGdfsInfObj.inputs.Zoom = 0.6
                dfsrenderSVREGdfsInfObj.inputs.CenterVol = bfc

                dfsrenderSVREGdfsSupObj = pe.Node(interface=bs.DfsRender(), name='dfsrenderSVREGdfsSup')
                dfsrenderSVREGdfsSupObj.inputs.Surfaces = SVREGdfs
                dfsrenderSVREGdfsSupObj.inputs.OutFile = '{0}/SVREGdfsSup.png'.format(WEBPATH)
                dfsrenderSVREGdfsSupObj.inputs.Sup = True
                dfsrenderSVREGdfsSupObj.inputs.Zoom = 0.6
                dfsrenderSVREGdfsSupObj.inputs.CenterVol = bfc

                dfsrenderSVREGdfsAntObj = pe.Node(interface=bs.DfsRender(), name='dfsrenderSVREGdfsAnt')
                dfsrenderSVREGdfsAntObj.inputs.Surfaces = SVREGdfs
                dfsrenderSVREGdfsAntObj.inputs.OutFile = '{0}/SVREGdfsAnt.png'.format(WEBPATH)
                dfsrenderSVREGdfsAntObj.inputs.Ant = True
                dfsrenderSVREGdfsAntObj.inputs.Zoom = 0.6
                dfsrenderSVREGdfsAntObj.inputs.CenterVol = bfc

                dfsrenderSVREGdfsPosObj = pe.Node(interface=bs.DfsRender(), name='dfsrenderSVREGdfsPos')
                dfsrenderSVREGdfsPosObj.inputs.Surfaces = SVREGdfs
                dfsrenderSVREGdfsPosObj.inputs.OutFile = '{0}/SVREGdfsPos.png'.format(WEBPATH)
                dfsrenderSVREGdfsPosObj.inputs.Pos = True
                dfsrenderSVREGdfsPosObj.inputs.Zoom = 0.6
                dfsrenderSVREGdfsPosObj.inputs.CenterVol = bfc

                qcstateSVREG = pe.Node(interface=bs.QCState(), name='qcstateSVREG')
                qcstateSVREG.inputs.filename = subjstate
                qcstateSVREG.inputs.stagenum = 13

                ### Connect rendering to SVREG ####
                brainsuite_workflow.connect(svregObj, 'outputLabelFile', volbendSVRegLabelObj, 'dataSinkDelay')
                brainsuite_workflow.connect(svregObj, 'outputLabelFile', volbendSVRegLabelCorObj, 'dataSinkDelay')
                brainsuite_workflow.connect(svregObj, 'outputLabelFile', volbendSVRegLabelSagObj, 'dataSinkDelay')
                brainsuite_workflow.connect(svregObj, 'outputLabelFile', dfsrenderSVREGdfsLeftObj, 'dataSinkDelay')
                brainsuite_workflow.connect(svregObj, 'outputLabelFile', dfsrenderSVREGdfsRightObj, 'dataSinkDelay')
                brainsuite_workflow.connect(svregObj, 'outputLabelFile', dfsrenderSVREGdfsInfObj, 'dataSinkDelay')
                brainsuite_workflow.connect(svregObj, 'outputLabelFile', dfsrenderSVREGdfsSupObj, 'dataSinkDelay')
                brainsuite_workflow.connect(svregObj, 'outputLabelFile', dfsrenderSVREGdfsAntObj, 'dataSinkDelay')
                brainsuite_workflow.connect(svregObj, 'outputLabelFile', dfsrenderSVREGdfsPosObj, 'dataSinkDelay')

                ### Connect QC to SVREG ####
                brainsuite_workflow.connect(generateXls, 'roiwisestats', qcstateSVREG, 'Run')

            #### smooth surface
            smoothsurf = self.smoothsurf

            smoothSurfInputBase = anat + os.sep + 'atlas.pvc-thickness_0-6mm'

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

            smoothKernel = self.smoothvol

            smoothVolJacObj = pe.Node(interface=bs.SVRegSmoothVol(), name='SMOOTHVOL_MAP')
            smoothVolJacObj.inputs.inFile = anat + os.sep + SUBJECT_ID + '_T1w' + '.svreg.inv.jacobian.nii.gz'
            smoothVolJacObj.inputs.stdx = smoothKernel
            smoothVolJacObj.inputs.stdy = smoothKernel
            smoothVolJacObj.inputs.stdz = smoothKernel
            smoothVolJacObj.inputs.outFile = anat + os.sep + SUBJECT_ID + '_T1w' + '.svreg.inv.jacobian.smooth{0}mm.nii.gz'.format(
                str(smoothKernel))

            brainsuite_workflow.connect(ds3, 'out_file', smoothSurfLeftObj, 'dataSinkDelay')
            brainsuite_workflow.connect(ds3, 'out_file', smoothSurfRightObj, 'dataSinkDelay')
            brainsuite_workflow.connect(ds3, 'out_file', smoothVolJacObj, 'dataSinkDelay')

            ## TODO: place svreg.inv.map smoothing here ##

        if 'SVREG' in STAGES and 'BDP' in STAGES:
            atlasFilePrefix = self.atlas

            ######## Apply Map ########
            applyMapInputBase = dwi + os.sep + SUBJECT_ID + '_T1w' # '_dwi'
            applyMapInputBaseSVReg = anat + os.sep + SUBJECT_ID + '_T1w'
            applyMapMapFile = applyMapInputBaseSVReg + '.svreg.inv.map.nii.gz'
            applyMapTargetFile = atlasFilePrefix + '.bfc.nii.gz'
            
            distcorr = "correct."
            if self.skipDistortionCorr:
                distcorr = ""

            applyMapFAObj = pe.Node(interface=bs.SVRegApplyMap(), name='APPLYMAP_FA')
            applyMapFAObj.inputs.mapFile = applyMapMapFile
            applyMapFAObj.inputs.dataFile = applyMapInputBase + '.dwi.RAS.{0}FA.T1_coord.nii.gz'.format(distcorr)
            applyMapFAObj.inputs.outFile = applyMapInputBase + '.dwi.RAS.{0}atlas.FA.nii.gz'.format(distcorr)
            applyMapFAObj.inputs.targetFile = applyMapTargetFile

            applyMapMDObj = pe.Node(interface=bs.SVRegApplyMap(), name='APPLYMAP_MD')
            applyMapMDObj.inputs.mapFile = applyMapMapFile
            applyMapMDObj.inputs.dataFile = applyMapInputBase + '.dwi.RAS.{0}MD.T1_coord.nii.gz'.format(distcorr)
            applyMapMDObj.inputs.outFile = applyMapInputBase + '.dwi.RAS.{0}atlas.MD.nii.gz'.format(distcorr)
            applyMapMDObj.inputs.targetFile = applyMapTargetFile

            applyMapAxialObj = pe.Node(interface=bs.SVRegApplyMap(), name='APPLYMAP_AXIAL')
            applyMapAxialObj.inputs.mapFile = applyMapMapFile
            applyMapAxialObj.inputs.dataFile = applyMapInputBase + '.dwi.RAS.{0}axial.T1_coord.nii.gz'.format(distcorr)
            applyMapAxialObj.inputs.outFile = applyMapInputBase + '.dwi.RAS.{0}atlas.axial.nii.gz'.format(distcorr)
            applyMapAxialObj.inputs.targetFile = applyMapTargetFile

            applyMapRadialObj = pe.Node(interface=bs.SVRegApplyMap(), name='APPLYMAP_RADIAL')
            applyMapRadialObj.inputs.mapFile = applyMapMapFile
            applyMapRadialObj.inputs.dataFile = applyMapInputBase + '.dwi.RAS.{0}radial.T1_coord.nii.gz'.format(distcorr)
            applyMapRadialObj.inputs.outFile = applyMapInputBase + '.dwi.RAS.{0}atlas.radial.nii.gz'.format(distcorr)
            applyMapRadialObj.inputs.targetFile = applyMapTargetFile

            applyMapmADCObj = pe.Node(interface=bs.SVRegApplyMap(), name='APPLYMAP_mADC')
            applyMapmADCObj.inputs.mapFile = applyMapMapFile
            applyMapmADCObj.inputs.dataFile = applyMapInputBase + '.dwi.RAS.{0}mADC.T1_coord.nii.gz'.format(distcorr)
            applyMapmADCObj.inputs.outFile = applyMapInputBase + '.dwi.RAS.{0}atlas.mADC.nii.gz'.format(distcorr)
            applyMapmADCObj.inputs.targetFile = applyMapTargetFile

            applyMapFRT_GFAObj = pe.Node(interface=bs.SVRegApplyMap(), name='APPLYMAP_FRT_GFA')
            applyMapFRT_GFAObj.inputs.mapFile = applyMapMapFile
            applyMapFRT_GFAObj.inputs.dataFile = applyMapInputBase + '.dwi.RAS.{0}FRT_GFA.T1_coord.nii.gz'.format(distcorr)
            applyMapFRT_GFAObj.inputs.outFile = applyMapInputBase + '.dwi.RAS.{0}atlas.FRT_GFA.nii.gz'.format(distcorr)
            applyMapFRT_GFAObj.inputs.targetFile = applyMapTargetFile

            ds5 = pe.Node(io.DataSink(), name='DATASINK5')
            ds5.inputs.base_directory = anat

            brainsuite_workflow.connect(ds2, 'out_file', applyMapFAObj, 'dataSinkDelay')
            brainsuite_workflow.connect(ds2, 'out_file', applyMapMDObj, 'dataSinkDelay')
            brainsuite_workflow.connect(ds2, 'out_file', applyMapAxialObj, 'dataSinkDelay')
            brainsuite_workflow.connect(ds2, 'out_file', applyMapRadialObj, 'dataSinkDelay')
            brainsuite_workflow.connect(ds2, 'out_file', applyMapmADCObj, 'dataSinkDelay')
            brainsuite_workflow.connect(ds2, 'out_file', applyMapFRT_GFAObj, 'dataSinkDelay')

            ds4 = pe.Node(io.DataSink(), name='DATASINK4')
            ds4.inputs.base_directory = anat

            brainsuite_workflow.connect(applyMapFAObj, 'mappedFile', ds4, '@')
            brainsuite_workflow.connect(applyMapMDObj, 'mappedFile', ds4, '@1')
            brainsuite_workflow.connect(applyMapAxialObj, 'mappedFile', ds4, '@2')
            brainsuite_workflow.connect(applyMapRadialObj, 'mappedFile', ds4, '@3')
            brainsuite_workflow.connect(applyMapmADCObj, 'mappedFile', ds4, '@4')
            brainsuite_workflow.connect(applyMapFRT_GFAObj, 'mappedFile', ds4, '@5')


            ####### Smooth Vol #######
            smoothKernel = self.smoothvol
            smoothVolInputBase = dwi + os.sep + SUBJECT_ID  + '_T1w' + '.dwi.RAS.{0}atlas.'.format(distcorr)

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

            brainsuite_workflow.connect(ds4, 'out_file', smoothVolFAObj, 'dataSinkDelay')
            brainsuite_workflow.connect(ds4, 'out_file', smoothVolMDObj, 'dataSinkDelay')
            brainsuite_workflow.connect(ds4, 'out_file', smoothVolAxialObj, 'dataSinkDelay')
            brainsuite_workflow.connect(ds4, 'out_file', smoothVolRadialObj, 'dataSinkDelay')
            brainsuite_workflow.connect(ds4, 'out_file', smoothVolmADCObj, 'dataSinkDelay')
            brainsuite_workflow.connect(ds4, 'out_file', smoothVolFRT_GFAObj, 'dataSinkDelay')

        if 'BFP' in STAGES:
            if not os.path.exists(func):
                os.makedirs(func)

            BFPObjs = []
            for task in range(len(BFP['sess'])):
                BFPObjs.append(pe.Node(interface=bs.BFP(), name='BFP_{0}'.format(BFP['sess'][task])))
                BFPObjs[task].inputs.configini = str(BFP['configini'])
                BFPObjs[task].inputs.t1file = os.path.join(CACHE_DIRECTORY, t1)
                BFPObjs[task].inputs.fmrifile = BFP['func'][task]
                BFPObjs[task].inputs.studydir = BFP['studydir']
                BFPObjs[task].inputs.subjID = BFP['subjID']
                # fullname = BFP['task'][task].split('/')[-1].split('_bold')[0].split('task-')[-1]
                BFPObjs[task].inputs.session = BFP['sess'][task]
                BFPObjs[task].inputs.TR = BFP['TR']

            if 'QC' in STAGES:

                BFPQCPrefix = func + BFP['subjID'] + '_' + BFP['sess'][0] + "_bold"
                ssimpng = BFPQCPrefix + '.mc.ssim.png'
                mcopng = BFPQCPrefix + '.mco.png'
                Func2T1 = BFPQCPrefix + '.example.func2t1.nii.gz'
                PreCorrFunc = BFPQCPrefix + '_b0/' + BFP['subjID'] + '_' + BFP['sess'][0] + "_bold" + '.infile.RAS.nii.gz'
                PostCorrFunc = BFPQCPrefix + '_b0/' + BFP['subjID'] + '_' + BFP['sess'][0] + "_bold" + '.infile.corr.nii.gz'
                pvcLabel = anat + SUBJECT_ID + '_T1w.pvc.label.nii.gz'
                pvcFuncLabel = BFPQCPrefix + '.pvc.label.nii.gz'

                makeMaskBFPpvcObj = pe.Node(bs.makeMask(), name='makeMaskBFPpvc')
                makeMaskBFPpvcObj.inputs.fileNameAndROIs = ' '.join([pvcLabel, "1", "2", "4", "5", "6"])
                makeMaskBFPObj = pe.Node(bs.makeMask(), name='makeMaskBFP')
                makeMaskBFPObj.inputs.fileNameAndROIs = ' '.join([pvcFuncLabel, "1", "2", "4", "5", "6"])
                brainsuite_workflow.connect(BFPObjs[0], 'dummy', makeMaskBFPpvcObj, "Run")
                brainsuite_workflow.connect(BFPObjs[0], 'dummy', makeMaskBFPObj, "Run")

                pvcMask = anat + SUBJECT_ID + '_T1w' + '.pvc.edge.mask.nii.gz'

                funcPVCmask = BFPQCPrefix + '.pvc.edge.mask.nii.gz'

                ## Copy png files
                copySSIMObj = pe.Node(interface=bs.copyFile(), name='CopyMCSSIM')
                copySSIMObj.inputs.inFile = ssimpng
                copySSIMObj.inputs.outFile = '{0}/ssim.png'.format(WEBPATH)

                copyMCOObj = pe.Node(interface=bs.copyFile(), name='CopyMCO')
                copyMCOObj.inputs.inFile = mcopng
                copyMCOObj.inputs.outFile = '{0}/mco.png'.format(WEBPATH)

                brainsuite_workflow.connect(BFPObjs[0], 'dummy', copySSIMObj, "Run")
                brainsuite_workflow.connect(BFPObjs[0], 'dummy', copyMCOObj, "Run")

                # Func2T1 with PVC label mask
                volbendFunc2T1Obj = pe.Node(interface=bs.Volblend(), name='volblendFunc2T1')
                volbendFunc2T1Obj.inputs.inFile = Func2T1
                volbendFunc2T1Obj.inputs.outFile = '{0}/Func2T1.png'.format(WEBPATH)
                volbendFunc2T1Obj.inputs.view = 1  # axial
                volbendFunc2T1Obj.inputs.maskFile = pvcMask

                if self.epit1corr ==1:
                    # precorr axial
                    volbendPreCorrFuncObj = pe.Node(interface=bs.Volblend(), name='volblendPreCorrFunc')
                    volbendPreCorrFuncObj.inputs.inFile = PreCorrFunc
                    volbendPreCorrFuncObj.inputs.outFile = '{0}/PreCorrFunc.png'.format(WEBPATH)
                    volbendPreCorrFuncObj.inputs.view = 1  # axial
                    volbendPreCorrFuncObj.inputs.maskFile = funcPVCmask

                    # precorr sag
                    volbendPreCorrFuncSagObj = pe.Node(interface=bs.Volblend(), name='volblendPreCorrFuncSag')
                    volbendPreCorrFuncSagObj.inputs.inFile = PreCorrFunc
                    volbendPreCorrFuncSagObj.inputs.outFile = '{0}/PreCorrFuncSag.png'.format(WEBPATH)
                    volbendPreCorrFuncSagObj.inputs.view = 3  # sagittal
                    volbendPreCorrFuncSagObj.inputs.maskFile = funcPVCmask

                    # postcorr axial
                    volbendPostCorrFuncObj = pe.Node(interface=bs.Volblend(), name='volblendPostCorrFunc')
                    volbendPostCorrFuncObj.inputs.inFile = PostCorrFunc
                    volbendPostCorrFuncObj.inputs.outFile = '{0}/PostCorrFunc.png'.format(WEBPATH)
                    volbendPostCorrFuncObj.inputs.view = 1  # axial
                    volbendPostCorrFuncObj.inputs.maskFile = funcPVCmask

                    # postcorr sag
                    volbendPostCorrFuncSagObj = pe.Node(interface=bs.Volblend(), name='volblendPostCorrFuncSag')
                    volbendPostCorrFuncSagObj.inputs.inFile = PostCorrFunc
                    volbendPostCorrFuncSagObj.inputs.outFile = '{0}/PostCorrFuncSag.png'.format(WEBPATH)
                    volbendPostCorrFuncSagObj.inputs.view = 3  # sagittal
                    volbendPostCorrFuncSagObj.inputs.maskFile = funcPVCmask

                    brainsuite_workflow.connect(makeMaskBFPObj, 'OutFile', volbendPreCorrFuncObj, 'dataSinkDelay')
                    brainsuite_workflow.connect(makeMaskBFPObj, 'OutFile', volbendPreCorrFuncSagObj, 'dataSinkDelay')
                    brainsuite_workflow.connect(makeMaskBFPObj, 'OutFile', volbendPostCorrFuncObj, 'dataSinkDelay')
                    brainsuite_workflow.connect(makeMaskBFPObj, 'OutFile', volbendPostCorrFuncSagObj, 'dataSinkDelay')

                qcstateBFP = pe.Node(interface=bs.QCState(), name='qcstateBFP')
                qcstateBFP.inputs.filename = subjstate
                qcstateBFP.inputs.stagenum = 14

                ### Connect rendering to BFP ####
                brainsuite_workflow.connect(makeMaskBFPpvcObj, 'OutFile', volbendFunc2T1Obj, 'dataSinkDelay')

                ### Connect QC to BFP ####
                brainsuite_workflow.connect(BFPObjs[0], 'res2std', qcstateBFP, 'Run')

            if 'SVREG' not in STAGES:
                ds2 = pe.Node(io.DataSink(), name='DATASINK2')
                ds2.inputs.base_directory = anat
            brainsuite_workflow.connect(ds2, 'out_file', BFPObjs[0], 'dataSinkDelay')
            if len(BFP['sess']) > 1:
                for task in range(len(BFP['func'])-1):
                    brainsuite_workflow.connect(BFPObjs[task], 'res2std', BFPObjs[int(task+1)], 'dataSinkDelay')

        try:
            brainsuite_workflow.run(plugin='MultiProc', plugin_args={'n_procs': 2}, updatehash=False)
            if 'QC' in STAGES:
                cmd = '/BrainSuite/QC/qcState.sh {0} {1}'.format(subjstate, 111)
                subprocess.call(cmd, shell=True)
            print('Processing for subject %s has completed. Nipype workflow is located at: %s' % (
                SUBJECT_ID, WORKFLOW_BASE_DIRECTORY))
        except(RuntimeError) as err:
            if 'QC' in STAGES:
                cmd = '/BrainSuite/QC/qcState.sh {0} {1}'.format(subjstate, 404)
                subprocess.call(cmd, shell=True)
            print("RuntimeError:", err)

