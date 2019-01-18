# -*- coding: utf-8 -*-

import nipype.pipeline.engine as pe
import nipype.interfaces.brainsuite as bs
import nipype.interfaces.io as io
from bids.grabbids import BIDSLayout
from shutil import copyfile
import os

ATLAS_MRI_SUFFIX = 'brainsuite.icbm452.lpi.v08a.img'
ATLAS_LABEL_SUFFIX = 'brainsuite.icbm452.v15a.label.img'

BRAINSUITE_ATLAS_DIRECTORY = "/opt/BrainSuite18a/atlas/"


def runStructuralProcessing(infile, base_dir, subjID, **keyword_parameters):
    # layout = BIDSLayout(base_dir)

    # if 'BSEONLY' in keyword_parameters:


    WORKFLOW_NAME = 'BrainSuite'

    brainsuite_workflow = pe.Workflow(name=WORKFLOW_NAME)
    brainsuite_workflow.base_dir = base_dir
    CACHE_DIRECTORY = keyword_parameters['CACHE']

    # brainsuite_workflow.base_dir = "/tmp"

    bseObj = pe.Node(interface=bs.Bse(), name='BSE')
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
    # bseObj.inputs.inputMRIFile = os.path.join(base_dir, infile)
    bseObj.inputs.inputMRIFile = infile
    # Provided atlas files
    cerebroObj.inputs.inputAtlasMRIFile = (BRAINSUITE_ATLAS_DIRECTORY + ATLAS_MRI_SUFFIX)
    cerebroObj.inputs.inputAtlasLabelFile = (BRAINSUITE_ATLAS_DIRECTORY + ATLAS_LABEL_SUFFIX)

    # ====Parameters====
    bseObj.inputs.diffusionIterations = 3
    bseObj.inputs.diffusionConstant = 25  # -d
    bseObj.inputs.edgeDetectionConstant = 0.64  # -s
    bseObj.inputs.autoParameters = True

    # cerebroObj.inputs.useCentroids = False
    pialmeshObj.inputs.tissueThreshold = 1.05
    tcaObj.inputs.minCorrectionSize = 2500
    tcaObj.inputs.foregroundDelta = 20

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
    ds.inputs.base_directory = base_dir

    # **DataSink connections**
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

    # if 'SVREG' in keyword_parameters:
        #### SVREG

    svregObj = pe.Node(interface=bs.SVReg(), name='SVREG')
    svregInputBase = base_dir

    # svreg inputs that will be created. We delay execution of SVReg until all CSE and datasink are done
    svregObj.inputs.subjectFilePrefix = svregInputBase
    svregObj.inputs.atlasFilePrefix = '/opt/BrainSuite18a/svreg/BCI-DNI_brain_atlas/BCI-DNI_brain'
    # if 'ATLAS' in keyword_parameters:
    #     svregObj.inputs.atlasFilePrefix = keyword_parameters['ATLAS']
    if 'SingleThread' in keyword_parameters:
        if 'ON' in keyword_parameters['SingleThread']:
            svregObj.inputs.useSingleThreading = True

    brainsuite_workflow.connect(ds, 'out_file', svregObj, 'dataSinkDelay')



    if 'THICKPVC' in keyword_parameters:
        ds2 = pe.Node(io.DataSink(), name='DATASINK2')
        ds2.inputs.base_directory = base_dir

        brainsuite_workflow.connect(svregObj, 'outputLabelFile', ds2, '@')

        thickPVCObj = pe.Node(interface=bs.ThicknessPVC(), name='ThickPVC')
        thickPVCInputBase = base_dir + os.sep + subjID
        thickPVCObj.inputs.subjectFilePrefix = thickPVCInputBase

        brainsuite_workflow.connect(ds2, 'out_file', thickPVCObj, 'dataSinkDelay')

        ds3 = pe.Node(io.DataSink(), name='DATASINK3')
        ds3.inputs.base_directory = base_dir

        brainsuite_workflow.connect(thickPVCObj, 'atlasSurfLeftFile', ds3, '@')
        brainsuite_workflow.connect(thickPVCObj, 'atlasSurfRightFile', ds3, '@1')


    brainsuite_workflow.run(plugin='MultiProc', plugin_args={'n_procs': 2}, updatehash=False)

