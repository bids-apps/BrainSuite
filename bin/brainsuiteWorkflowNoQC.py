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

BRAINSUITE_VERSION= os.environ['BrainSuiteVersion']
ATLAS_MRI_SUFFIX = 'brainsuite.icbm452.lpi.v08a.img'
ATLAS_LABEL_SUFFIX = 'brainsuite.icbm452.v15a.label.img'

BRAINSUITE_ATLAS_DIRECTORY = "/opt/BrainSuite{0}/atlas/".format(BRAINSUITE_VERSION)


def runWorkflow(SUBJECT_ID, INPUT_MRI_FILE, WORKFLOW_BASE_DIRECTORY, **keyword_parameters):
    # layout = BIDSLayout(BIDS_DIRECTORY)

    # WORKFLOW_NAME = SUBJECT_ID + "_cse"
    WORKFLOW_NAME = 'BrainSuite'

    brainsuite_workflow = pe.Workflow(name=WORKFLOW_NAME)
    CACHE_DIRECTORY = keyword_parameters['CACHE']
    brainsuite_workflow.base_dir = CACHE_DIRECTORY

    # brainsuite_workflow.base_dir = "/tmp"
    # t1 = INPUT_MRI_FILE.split("/")[-1].replace("_T1w", '')
    t1 = INPUT_MRI_FILE
    # copyfile(INPUT_MRI_FILE, os.path.join("/tmp", t1))
    try:
        copyfile(INPUT_MRI_FILE, os.path.join(CACHE_DIRECTORY, t1))
    except:
        pass

    bseObj = pe.Node(interface=bs.Bse(), name='BSE')
    ds0 = pe.Node(io.DataSink(), name='DATASINK')
    ds0.inputs.base_directory = WORKFLOW_BASE_DIRECTORY

    # ====BSE Inputs and Parameters====
    bseObj.inputs.inputMRIFile = os.path.join(CACHE_DIRECTORY, t1)
    bseObj.inputs.diffusionIterations = 3
    bseObj.inputs.diffusionConstant = 25  # -d
    bseObj.inputs.edgeDetectionConstant = 0.64  # -s
    bseObj.inputs.autoParameters = True

    if "BSEONLY" in keyword_parameters:
        brainsuite_workflow.connect(bseObj, 'outputMRIVolume', ds0, '@')

    if not "BSEONLY" in keyword_parameters:
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
        cerebroObj.inputs.inputAtlasMRIFile = (BRAINSUITE_ATLAS_DIRECTORY + ATLAS_MRI_SUFFIX)
        cerebroObj.inputs.inputAtlasLabelFile = (BRAINSUITE_ATLAS_DIRECTORY + ATLAS_LABEL_SUFFIX)
        # cerebroObj.inputs.useCentroids = False
        pialmeshObj.inputs.tissueThreshold = 1.05
        tcaObj.inputs.minCorrectionSize = 2500
        tcaObj.inputs.foregroundDelta = 20

        # ====Connect====

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

        if 'BDP' in keyword_parameters:
            INPUT_DWI_BASE = keyword_parameters['BDP']
            bdpObj = pe.Node(interface=bs.BDP(), name='BDP')
            bdpInputBase = WORKFLOW_BASE_DIRECTORY + os.sep + SUBJECT_ID +'_T1w'

            # bdp inputs that will be created. We delay execution of BDP until all CSE and datasink are done
            bdpObj.inputs.bfcFile = bdpInputBase + '.bfc.nii.gz'
            bdpObj.inputs.inputDiffusionData = INPUT_DWI_BASE + '.nii.gz'
            dwiabspath = os.path.abspath(os.path.dirname(INPUT_DWI_BASE + '.nii.gz'))
            bdpObj.inputs.BVecBValPair = [keyword_parameters['BVEC'], keyword_parameters['BVAL']]

            bdpObj.inputs.estimateTensors = True
            bdpObj.inputs.estimateODF_FRACT = True
            bdpObj.inputs.estimateODF_FRT = True

            bdpsubdir = '/../dwi'
            bdpObj.inputs.outputSubdir = bdpsubdir

            brainsuite_workflow.connect(ds, 'out_file', bdpObj, 'dataSinkDelay')
            if 'SVREG' in keyword_parameters:
                ds2 = pe.Node(io.DataSink(), name='DATASINK2')
                ds2.inputs.base_directory = WORKFLOW_BASE_DIRECTORY
                brainsuite_workflow.connect(bdpObj, 'tensor_coord', ds2, '@0')

        if 'SVREG' in keyword_parameters:
            svregObj = pe.Node(interface=bs.SVReg(), name='SVREG')
            svregInputBase = WORKFLOW_BASE_DIRECTORY + os.sep + SUBJECT_ID + '_T1w'

            # svreg inputs that will be created. We delay execution of SVReg until all CSE and datasink are done
            svregObj.inputs.subjectFilePrefix = svregInputBase
            svregObj.inputs.atlasFilePrefix = '/opt/BrainSuite{0}/svreg/BCI-DNI_brain_atlas/BCI-DNI_brain'.format(BRAINSUITE_VERSION)
            if 'ATLAS' in keyword_parameters:
                svregObj.inputs.atlasFilePrefix = keyword_parameters['ATLAS']
            if 'SingleThread' in keyword_parameters:
                if 'ON' in keyword_parameters['SingleThread']:
                    svregObj.inputs.useSingleThreading = True

            brainsuite_workflow.connect(ds, 'out_file', svregObj, 'dataSinkDelay')

            if not 'BDP' in keyword_parameters:
                ds2 = pe.Node(io.DataSink(), name='DATASINK2')
                ds2.inputs.base_directory = WORKFLOW_BASE_DIRECTORY

            brainsuite_workflow.connect(svregObj, 'outputLabelFile', ds2, '@')

            thickPVCObj = pe.Node(interface=bs.ThicknessPVC(), name='ThickPVC')
            thickPVCInputBase = WORKFLOW_BASE_DIRECTORY + os.sep + SUBJECT_ID + '_T1w'
            thickPVCObj.inputs.subjectFilePrefix = thickPVCInputBase

            brainsuite_workflow.connect(ds2, 'out_file', thickPVCObj, 'dataSinkDelay')

            ds3 = pe.Node(io.DataSink(), name='DATASINK3')
            ds3.inputs.base_directory = WORKFLOW_BASE_DIRECTORY

            brainsuite_workflow.connect(thickPVCObj, 'atlasSurfLeftFile', ds3, '@')
            brainsuite_workflow.connect(thickPVCObj, 'atlasSurfRightFile', ds3, '@1')


            #### smooth surface
            smoothsurf = 2.0

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

        if 'SVREG' in keyword_parameters and 'BDP' in keyword_parameters:
            bdpsubdir = os.path.dirname(WORKFLOW_BASE_DIRECTORY) + '/dwi'
            atlasFilePrefix = '/opt/BrainSuite{0}/svreg/BCI-DNI_brain_atlas/BCI-DNI_brain'.format(BRAINSUITE_VERSION)
            if 'ATLAS' in keyword_parameters:
                atlasFilePrefix = keyword_parameters['ATLAS']

            ######## Apply Map ########
            applyMapInputBase = bdpsubdir + os.sep + SUBJECT_ID + '_T1w'
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
            smoothKernel = 3.0
            bdpsubdir = os.path.dirname(WORKFLOW_BASE_DIRECTORY) + '/dwi'
            smoothVolInputBase = bdpsubdir + os.sep + SUBJECT_ID + '_T1w' + '.dwi.RAS.correct.atlas.'

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
    print('Processing for subject %s has completed. Nipype workflow is located at: %s' % (
    SUBJECT_ID, WORKFLOW_BASE_DIRECTORY))
