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

from __future__ import print_function, division, unicode_literals, absolute_import

import os
import re as regex

from ..base import TraitedSpec, CommandLineInputSpec, CommandLine, File, traits, isdefined
from ..traits_extension import str
from ... import config, logging, LooseVersion, __version__
iflogger = logging.getLogger('interface')

'''
This class provides interfaces for BrainSuite command line tools.
Please see brainsuite.org for more information.
'''

class BrainSuiteCommandLine(CommandLine):
    def _check_mandatory_inputs(self):
        """ Raises an exception if a mandatory input is Undefined
        """
        for name, spec in list(self.inputs.traits(mandatory=True).items()):
            value = getattr(self.inputs, name)
            self._check_xor(spec, name, value)
            if not isdefined(value) and spec.xor is None:
                msg = ("%s requires a value for input '%s'. "
                       "For a list of required inputs, see %s.help()" %
                       (self.__class__.__name__, name, self.__class__.__name__))
                # raise ValueError(msg)
                iflogger.info(msg)
            if isdefined(value):
                self._check_requires(spec, name, value)
        for name, spec in list(self.inputs.traits(mandatory=None,
                                                  transient=None).items()):
            self._check_requires(spec, name, getattr(self.inputs, name))

    @property
    def cmdline(self):
        """ `command` plus any arguments (args)
        validates arguments and generates command line"""
        self._check_mandatory_inputs()
        allargs = [self.cmd] + self._parse_inputs()
        return ' '.join(allargs)

    def raise_exception(self, runtime):
        iflogger.info('[ERROR] RuntimeError has occurred.')
        message = "Command:\n" + runtime.cmdline + "\n"
        message += "Standard output:\n" + runtime.stdout + "\n"
        message += "Standard error:\n" + runtime.stderr + "\n"
        message += "Return code: " + str(runtime.returncode)
        iflogger.info(message)
        return runtime


class BseInputSpec(CommandLineInputSpec):
    inputMRIFile = File(
        mandatory=True, argstr='-i %s', desc='input MRI volume')
    outputMRIVolume = File(
        desc='output brain-masked MRI volume. If unspecified, output file name will be auto generated.',
        argstr='-o %s', hash_files=True, genfile=True)
    outputMaskFile = File(
        desc='save smooth brain mask. If unspecified, output file name will be auto generated.',
        argstr='--mask %s', hash_files=True, genfile=True)
    autoParameters = traits.Bool(
        desc='use autobse to set extraction parameters', argstr='--auto')
    autoIterations = traits.Int(
        5, usedefault=True, desc='number of iterations for autobse algorithm', argstr='--auto-iterations %d')
    autoTuningThreads = traits.Bool(
        desc='use threads for automatic parameter tuning', argstr='--mt')
    diffusionConstant = traits.Float(
        25, usedefault=True, desc='diffusion constant', argstr='-d %f')
    diffusionIterations = traits.Int(
        3, usedefault=True, desc='diffusion iterations', argstr='-n %d')
    edgeDetectionConstant = traits.Float(
        0.64, usedefault=True, desc='edge detection constant', argstr='-s %f')
    radius = traits.Float(
        1, usedefault=True, desc='radius of erosion/dilation filter', argstr='-r %f')
    dilateFinalMask = traits.Bool(
        True, usedefault=True, desc='dilate final mask', argstr='-p')
    trim = traits.Bool(
        True, usedefault=True, desc='trim brainstem', argstr='--trim')
    outputDiffusionFilter = File(
        desc='diffusion filter output', argstr='--adf %s', hash_files=False)
    outputEdgeMap = File(
        desc='edge map output', argstr='--edge %s', hash_files=False)
    outputDetailedBrainMask = File(
        desc='save detailed brain mask', argstr='--hires %s', hash_files=False)
    outputCortexFile = File(
        desc='cortex file', argstr='--cortex %s', hash_files=False)
    verbosityLevel = traits.Float(
        1, usedefault=True, desc=' verbosity level (0=silent)', argstr='-v %f')
    noRotate = traits.Bool(
        desc='retain original orientation(default behavior will auto-rotate input NII files to LPI orientation)',
        argstr='--norotate')
    prescale = traits.Bool(
        desc='prescale image to uint16', argstr='--prescale')
    timer = traits.Bool(
        desc='show timing', argstr='--timer')
    dummy = traits.Str(desc='dummy output')

class BseOutputSpec(TraitedSpec):
    outputMRIVolume = File(desc='path/name of brain-masked MRI volume')
    outputMaskFile = File(desc='path/name of smooth brain mask')
    outputDiffusionFilter = File(desc='path/name of diffusion filter output')
    outputEdgeMap = File(desc='path/name of edge map output')
    outputDetailedBrainMask = File(desc='path/name of detailed brain mask')
    outputCortexFile = File(desc='path/name of cortex file')
    inputMRIFile = File(desc='input MRI volume')


class Bse(BrainSuiteCommandLine):
    """
    brain surface extractor (BSE)
    This program performs automated skull and scalp removal on T1-weighted MRI volumes.

    http://brainsuite.org/processing/surfaceextraction/bse/

    Examples
    --------

    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> bse = brainsuite.Bse()
    >>> bse.inputs.inputMRIFile = example_data('structural.nii')
    >>> results = bse.run() #doctest: +SKIP

    """

    input_spec = BseInputSpec
    output_spec = BseOutputSpec
    _cmd = 'bse'

    def _gen_filename(self, name):
        inputs = self.inputs.get()
        if isdefined(inputs[name]):
            return os.path.abspath(inputs[name])

        fileToSuffixMap = {'outputMRIVolume': '.bse.nii.gz',
                           'outputMaskFile': '.mask.nii.gz'
                           }

        if name in fileToSuffixMap:
            return getFileName(self.inputs.inputMRIFile, fileToSuffixMap[name])

        return None

    def _format_arg(self, name, spec, value):
        return super(Bse, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        return l_outputs(self)


class BfcInputSpec(CommandLineInputSpec):
    inputMRIFile = File(
        mandatory=True, desc='input skull-stripped MRI volume', argstr='-i %s')
    inputMaskFile = File(
        desc='mask file', argstr='-m %s')
    outputMRIVolume = File(
        desc='output bias-corrected MRI volume.If unspecified, output file name will be auto generated.',
        argstr='-o %s', hash_files=True, genfile=True)
    outputBiasField = File(
        desc='save bias field estimate', argstr='--bias %s',)
    outputMaskedBiasField = File(
        desc='save bias field estimate (masked)', argstr='--maskedbias %s')
    histogramRadius = traits.Int(
        desc='histogram radius (voxels)', argstr='-r %d')
    biasEstimateSpacing = traits.Int(
        desc='bias sample spacing (voxels)', argstr='-s %d')
    controlPointSpacing = traits.Int(
        desc='control point spacing (voxels)', argstr='-c %d')
    splineLambda = traits.Float(
        desc='spline stiffness weighting parameter', argstr='-w %f')
    histogramType = traits.Enum(
        'ellipse', 'block',
        desc='Options for type of histogram\nellipse: use ellipsoid for ROI histogram\nblock :use block for ROI histogram',
        argstr='%s')
    iterativeMode = traits.Bool(
        desc='iterative mode (overrides -r, -s, -c, -w settings)', argstr='--iterate')
    correctionScheduleFile = File(
        desc='list of parameters ', argstr='--schedule %s')
    biasFieldEstimatesOutputPrefix = traits.Str(
        desc='save iterative bias field estimates as <prefix>.n.field.nii.gz',
        argstr='--biasprefix %s')
    correctedImagesOutputPrefix = traits.Str(
        desc='save iterative corrected images as <prefix>.n.bfc.nii.gz',
        argstr='--prefix %s')
    correctWholeVolume = traits.Bool(
        desc='apply correction field to entire volume',
        argstr='--extrapolate')
    minBias = traits.Float(
        0.5, usedefault=True, desc='minimum allowed bias value',
        argstr='-L %f')
    maxBias = traits.Float(
        1.5, usedefault=True, desc='maximum allowed bias value',
        argstr='-U %f')
    biasRange = traits.Enum(
        "low", "medium", "high",
        desc='Preset options for bias_model\n low: small bias model [0.95,1.05]\n'
             'medium: medium bias model [0.90,1.10]\n high: high bias model [0.80,1.20]',
        argstr='%s')
    intermediate_file_type = traits.Enum(
        "analyze", "nifti", "gzippedAnalyze", "gzippedNifti",
        desc='Options for the format in which intermediate files are generated',
        argstr='%s')
    convergenceThreshold = traits.Float(
        desc='convergence threshold', argstr='--eps %f')
    biasEstimateConvergenceThreshold = traits.Float(
        desc='bias estimate convergence threshold (values > 0.1 disable)', argstr='--beps %f')
    verbosityLevel = traits.Int(
        desc='verbosity level (0=silent)', argstr='-v %d')
    timer = traits.Bool(
        desc='display timing information', argstr='--timer')
    dummy = traits.Str(desc='dummy output')


class BfcOutputSpec(TraitedSpec):
    outputMRIVolume = File(desc='path/name of output file')
    outputBiasField = File(desc='path/name of bias field output file')
    outputMaskedBiasField = File(desc='path/name of masked bias field output')
    correctionScheduleFile = File(desc='path/name of schedule file')


class Bfc(BrainSuiteCommandLine):
    """
    bias field corrector (BFC)
    This program corrects gain variation in T1-weighted MRI.

    http://brainsuite.org/processing/surfaceextraction/bfc/

    Examples
    --------

    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> bfc = brainsuite.Bfc()
    >>> bfc.inputs.inputMRIFile = example_data('structural.nii')
    >>> bfc.inputs.inputMaskFile = example_data('mask.nii')
    >>> results = bfc.run() #doctest: +SKIP

    """

    input_spec = BfcInputSpec
    output_spec = BfcOutputSpec
    _cmd = 'bfc'

    def _gen_filename(self, name):
        inputs = self.inputs.get()
        if isdefined(inputs[name]):
            return os.path.abspath(inputs[name])

        fileToSuffixMap = {'outputMRIVolume': '.bfc.nii.gz'}
        if name in fileToSuffixMap:
            return getFileName(self.inputs.inputMRIFile, fileToSuffixMap[name])

        return None

    def _format_arg(self, name, spec, value):
        if name == 'histogramType':
            return spec.argstr % {"ellipse": "--ellipse", "block": "--block"}[value]
        if name == 'biasRange':
            return spec.argstr % {"low": "--low", "medium": "--medium", "high": "--high"}[value]
        if name == 'intermediate_file_type':
            return spec.argstr % {"analyze": "--analyze", "nifti": "--nifti", "gzippedAnalyze": "--analyzegz",
                                  "gzippedNifti": "--niftigz"}[value]

        return super(Bfc, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        return l_outputs(self)


class PvcInputSpec(CommandLineInputSpec):
    inputMRIFile = File(mandatory=True, desc='MRI file', argstr='-i %s')
    inputMaskFile = File(desc='brain mask file', argstr='-m %s')
    outputLabelFile = File(
        desc='output label file. If unspecified, output file name will be auto generated.',
        argstr='-o %s', genfile=True, hash_files=True)
    outputTissueFractionFile = File(
        desc='output tissue fraction file',
        argstr='-f %s', genfile=True, hash_files=True)
    spatialPrior = traits.Float(desc='spatial prior strength', argstr='-l %f')
    verbosity = traits.Int(desc='verbosity level (0 = silent)', argstr='-v %d')
    threeClassFlag = traits.Bool(
        desc='use a three-class (CSF=0,GM=1,WM=2) labeling', argstr='-3')
    timer = traits.Bool(desc='time processing', argstr='--timer')


class PvcOutputSpec(TraitedSpec):
    outputLabelFile = File(desc='path/name of label file')
    outputTissueFractionFile = File(desc='path/name of tissue fraction file')


class Pvc(BrainSuiteCommandLine):
    """
    partial volume classifier (PVC) tool.
    This program performs voxel-wise tissue classification T1-weighted MRI.
    Image should be skull-stripped and bias-corrected before tissue classification.

    http://brainsuite.org/processing/surfaceextraction/pvc/

    Examples
    --------

    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> pvc = brainsuite.Pvc()
    >>> pvc.inputs.inputMRIFile = example_data('structural.nii')
    >>> pvc.inputs.inputMaskFile = example_data('mask.nii')
    >>> results = pvc.run() #doctest: +SKIP

    """

    input_spec = PvcInputSpec
    output_spec = PvcOutputSpec
    _cmd = 'pvc'

    def _gen_filename(self, name):
        inputs = self.inputs.get()
        if isdefined(inputs[name]):
            return os.path.abspath(inputs[name])

        fileToSuffixMap = {'outputLabelFile': '.pvc.label.nii.gz',
                           'outputTissueFractionFile': '.pvc.frac.nii.gz'
                           }
        if name in fileToSuffixMap:
            return getFileName(self.inputs.inputMRIFile, fileToSuffixMap[name])

        return None

    def _list_outputs(self):
        return l_outputs(self)


class CerebroInputSpec(CommandLineInputSpec):
    inputMRIFile = File(
        mandatory=True, desc='input 3D MRI volume', argstr='-i %s')
    inputAtlasMRIFile = File(
        mandatory=True, desc='atlas MRI volume', argstr='--atlas %s')
    inputAtlasLabelFile = File(
        mandatory=True, desc='atlas labeling', argstr='--atlaslabels %s')
    inputBrainMaskFile = File(desc='brain mask file', argstr='-m %s')
    outputCerebrumMaskFile = File(
        desc='output cerebrum mask volume. If unspecified, output file name will be auto generated.',
        argstr='-o %s', genfile=True, hash_files=True)
    outputLabelVolumeFile = File(
        desc='output labeled hemisphere/cerebrum volume. If unspecified, output file name will be auto generated.',
        argstr='-l %s', genfile=True, hash_files=True)
    costFunction = traits.Int(2, usedefault=True, desc='0,1,2', argstr='-c %d')
    useCentroids = traits.Bool(
        desc='use centroids of data to initialize position', argstr='--centroids')
    outputAffineTransformFile = File(
        desc='save affine transform to file.', argstr='--air %s', genfile=True, hash_files=True)
    outputWarpTransformFile = File(
        desc='save warp transform to file.', argstr='--warp %s', genfile=True, hash_files=True)
    verbosity = traits.Int(desc='verbosity level (0=silent)', argstr='-v %d')
    linearConvergence = traits.Float(
        desc='linear convergence', argstr='--linconv %f')
    warpLevel = traits.Int(
        desc='warp order (2,3,4,5,6,7,8)', argstr='--warplevel %d')
    warpConvergence = traits.Float(
        desc='warp convergence', argstr='--warpconv %f')
    keepTempFiles = traits.Bool(
        desc="don't remove temporary files", argstr='--keep')
    tempDirectory = traits.Str(
        desc='specify directory to use for temporary files', argstr='--tempdir %s')
    tempDirectoryBase = traits.Str(
        desc='create a temporary directory within this directory', argstr='--tempdirbase %s')


class CerebroOutputSpec(TraitedSpec):
    outputCerebrumMaskFile = File(desc='path/name of cerebrum mask file')
    outputLabelVolumeFile = File(desc='path/name of label mask file')
    outputAffineTransformFile = File(desc='path/name of affine transform file')
    outputWarpTransformFile = File(desc='path/name of warp transform file')


class Cerebro(BrainSuiteCommandLine):
    """
    Cerebrum/cerebellum labeling tool
    This program performs automated labeling of cerebellum and cerebrum in T1 MRI.
    Input MRI should be skull-stripped or a brain-only mask should be provided.


    http://brainsuite.org/processing/surfaceextraction/cerebrum/

    Examples
    --------

    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> cerebro = brainsuite.Cerebro()
    >>> cerebro.inputs.inputMRIFile = example_data('structural.nii')
    >>> cerebro.inputs.inputAtlasMRIFile = 'atlasMRIVolume.img'
    >>> cerebro.inputs.inputAtlasLabelFile = 'atlasLabels.img'
    >>> cerebro.inputs.inputBrainMaskFile = example_data('mask.nii')
    >>> results = cerebro.run() #doctest: +SKIP

    """

    input_spec = CerebroInputSpec
    output_spec = CerebroOutputSpec
    _cmd = 'cerebro'

    def _gen_filename(self, name):
        inputs = self.inputs.get()
        if isdefined(inputs[name]):
            return os.path.abspath(inputs[name])

        fileToSuffixMap = {
            'outputCerebrumMaskFile': '.cerebrum.mask.nii.gz',
            'outputLabelVolumeFile': '.hemi.label.nii.gz',
            'outputWarpTransformFile': '.warp',
            'outputAffineTransformFile': '.air'
        }
        if name in fileToSuffixMap:
            return getFileName(self.inputs.inputMRIFile, fileToSuffixMap[name])

        return None

    def _list_outputs(self):
        return l_outputs(self)


class CortexInputSpec(CommandLineInputSpec):
    inputHemisphereLabelFile = File(
        mandatory=True, desc='hemisphere / lobe label volume', argstr='-h %s')
    outputCerebrumMask = File(
        desc='output structure mask. If unspecified, output file name will be auto generated.', argstr='-o %s',
        genfile=True, hash_files=True)
    inputTissueFractionFile = File(
        mandatory=True, desc='tissue fraction file (32-bit float)', argstr='-f %s')
    tissueFractionThreshold = traits.Float(
        50.0, usedefault=True, desc='tissue fraction threshold (percentage)', argstr='-p %f')
    computeWGBoundary = traits.Bool(
        True, usedefault=True, desc='compute WM/GM boundary', argstr='-w')
    computeGCBoundary = traits.Bool(
        desc='compute GM/CSF boundary', argstr='-g')
    includeAllSubcorticalAreas = traits.Bool(
        True, usedefault=True, desc='include all subcortical areas in WM mask', argstr='-a')
    verbosity = traits.Int(desc='verbosity level', argstr='-v %d')
    timer = traits.Bool(desc='timing function', argstr='--timer')


class CortexOutputSpec(TraitedSpec):
    outputCerebrumMask = File(desc='path/name of cerebrum mask')


class Cortex(BrainSuiteCommandLine):
    """
    cortex extractor
    This program produces a cortical mask using tissue fraction estimates
    and a co-registered cerebellum/hemisphere mask.

    http://brainsuite.org/processing/surfaceextraction/cortex/

    Examples
    --------

    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> cortex = brainsuite.Cortex()
    >>> cortex.inputs.inputHemisphereLabelFile = example_data('mask.nii')
    >>> cortex.inputs.inputTissueFractionFile = example_data('tissues.nii.gz')
    >>> results = cortex.run() #doctest: +SKIP

    """

    input_spec = CortexInputSpec
    output_spec = CortexOutputSpec
    _cmd = 'cortex'

    def _gen_filename(self, name):
        inputs = self.inputs.get()
        if isdefined(inputs[name]):
            return os.path.abspath(inputs[name])

        if name == 'outputCerebrumMask':
            return getFileName(self.inputs.inputHemisphereLabelFile, '.init.cortex.mask.nii.gz')
        return None

    def _list_outputs(self):
        return l_outputs(self)


class ScrubmaskInputSpec(CommandLineInputSpec):
    inputMaskFile = File(
        mandatory=True, desc='input structure mask file', argstr='-i %s')
    outputMaskFile = File(
        desc='output structure mask file. If unspecified, output file name will be auto generated.', argstr='-o %s',
        genfile=True, hash_files=True)
    backgroundFillThreshold = traits.Int(
        2, usedefault=True, desc='background fill threshold', argstr='-b %d')
    foregroundTrimThreshold = traits.Int(
        0, usedefault=True, desc='foreground trim threshold', argstr='-f %d')
    numberIterations = traits.Int(desc='number of iterations', argstr='-n %d')
    verbosity = traits.Int(desc='verbosity (0=silent)', argstr='-v %d')
    timer = traits.Bool(desc='timing function', argstr='--timer')


class ScrubmaskOutputSpec(TraitedSpec):
    outputMaskFile = File(desc='path/name of mask file')


class Scrubmask(BrainSuiteCommandLine):
    """
    ScrubMask tool
    scrubmask filters binary masks to trim loosely connected voxels that may
    result from segmentation errors and produce bumps on tessellated surfaces.

    http://brainsuite.org/processing/surfaceextraction/scrubmask/

    Examples
    --------

    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> scrubmask = brainsuite.Scrubmask()
    >>> scrubmask.inputs.inputMaskFile = example_data('mask.nii')
    >>> results = scrubmask.run() #doctest: +SKIP

    """
    input_spec = ScrubmaskInputSpec
    output_spec = ScrubmaskOutputSpec
    _cmd = 'scrubmask'

    def _gen_filename(self, name):
        inputs = self.inputs.get()
        if isdefined(inputs[name]):
            return os.path.abspath(inputs[name])

        if name == 'outputMaskFile':
            return getFileName(self.inputs.inputMaskFile, '.cortex.scrubbed.mask.nii.gz')

        return None

    def _list_outputs(self):
        return l_outputs(self)


class TcaInputSpec(CommandLineInputSpec):
    inputMaskFile = File(
        mandatory=True, desc='input mask volume', argstr='-i %s')
    outputMaskFile = File(
        desc='output mask volume. If unspecified, output file name will be auto generated.', argstr='-o %s',
        genfile=True, hash_files=True)
    minCorrectionSize = traits.Int(
        2500, usedefault=True, desc='maximum correction size', argstr='-m %d')
    maxCorrectionSize = traits.Int(
        desc='minimum correction size', argstr='-n %d')
    foregroundDelta = traits.Int(
        20, usedefault=True, desc='foreground delta', argstr='--delta %d')
    verbosity = traits.Int(desc='verbosity (0 = quiet)', argstr='-v %d')
    timer = traits.Bool(desc='timing function', argstr='--timer')


class TcaOutputSpec(TraitedSpec):
    outputMaskFile = File(desc='path/name of mask file')


class Tca(BrainSuiteCommandLine):
    """
    topological correction algorithm (TCA)
    This program removes topological handles from a binary object.

    http://brainsuite.org/processing/surfaceextraction/tca/

    Examples
    --------
    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> tca = brainsuite.Tca()
    >>> tca.inputs.inputMaskFile = example_data('mask.nii')
    >>> results = tca.run() #doctest: +SKIP

    """
    input_spec = TcaInputSpec
    output_spec = TcaOutputSpec
    _cmd = 'tca'

    def _gen_filename(self, name):
        inputs = self.inputs.get()
        if isdefined(inputs[name]):
            return os.path.abspath(inputs[name])

        if name == 'outputMaskFile':
            return getFileName(self.inputs.inputMaskFile, '.cortex.tca.mask.nii.gz')

        return None

    def _list_outputs(self):
        return l_outputs(self)


class DewispInputSpec(CommandLineInputSpec):
    inputMaskFile = File(mandatory=True, desc='input file', argstr='-i %s')
    outputMaskFile = File(
        desc='output file. If unspecified, output file name will be auto generated.', argstr='-o %s',
        genfile=True, hash_files=True)
    verbosity = traits.Int(desc='verbosity', argstr='-v %d')
    sizeThreshold = traits.Int(desc='size threshold', argstr='-t %d')
    maximumIterations = traits.Int(
        desc='maximum number of iterations', argstr='-n %d')
    timer = traits.Bool(desc='time processing', argstr='--timer')


class DewispOutputSpec(TraitedSpec):
    outputMaskFile = File(desc='path/name of mask file')


class Dewisp(BrainSuiteCommandLine):
    """
    dewisp
    removes wispy tendril structures from cortex model binary masks.
    It does so based on graph theoretic analysis of connected components,
    similar to TCA. Each branch of the structure graph is analyzed to determine
    pinch points that indicate a likely error in segmentation that attaches noise
    to the image. The pinch threshold determines how many voxels the cross-section
    can be before it is considered part of the image.

    http://brainsuite.org/processing/surfaceextraction/dewisp/

    Examples
    --------

    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> dewisp = brainsuite.Dewisp()
    >>> dewisp.inputs.inputMaskFile = example_data('mask.nii')
    >>> results = dewisp.run() #doctest: +SKIP

    """

    input_spec = DewispInputSpec
    output_spec = DewispOutputSpec
    _cmd = 'dewisp'

    def _gen_filename(self, name):
        inputs = self.inputs.get()
        if isdefined(inputs[name]):
            return os.path.abspath(inputs[name])

        if name == 'outputMaskFile':
            return getFileName(self.inputs.inputMaskFile, '.cortex.dewisp.mask.nii.gz')

        return None

    def _list_outputs(self):
        return l_outputs(self)


class DfsInputSpec(CommandLineInputSpec):
    inputVolumeFile = File(
        mandatory=True, desc='input 3D volume', argstr='-i %s')
    outputSurfaceFile = File(
        desc='output surface mesh file. If unspecified, output file name will be auto generated.', argstr='-o %s',
        genfile=True, hash_files=True)
    inputShadingVolume = File(
        desc='shade surface model with data from image volume', argstr='-c %s')
    smoothingIterations = traits.Int(
        10, usedefault=True, desc='number of smoothing iterations', argstr='-n %d')
    smoothingConstant = traits.Float(
        0.5, usedefault=True, desc='smoothing constant', argstr='-a %f')
    curvatureWeighting = traits.Float(
        5.0, usedefault=True, desc='curvature weighting', argstr='-w %f')
    scalingPercentile = traits.Float(desc='scaling percentile', argstr='-f %f')
    nonZeroTessellation = traits.Bool(
        desc='tessellate non-zero voxels', argstr='-nz', xor=('nonZeroTessellation', 'specialTessellation'))
    tessellationThreshold = traits.Float(
        desc='To be used with specialTessellation. Set this value first, then set specialTessellation value.\nUsage: tessellate voxels greater_than, less_than, or equal_to <tessellationThreshold>',
        argstr='%f')
    specialTessellation = traits.Enum('greater_than', 'less_than', 'equal_to',
                                      desc='To avoid throwing a UserWarning, set tessellationThreshold first. Then set this attribute.\nUsage: tessellate voxels greater_than, less_than, or equal_to <tessellationThreshold>',
                                      argstr='%s', xor=(
            'nonZeroTessellation', 'specialTessellation'), requires=['tessellationThreshold'], position=-1)
    zeroPadFlag = traits.Bool(
        desc='zero-pad volume (avoids clipping at edges)', argstr='-z')
    noNormalsFlag = traits.Bool(
        desc='do not compute vertex normals', argstr='--nonormals')
    postSmoothFlag = traits.Bool(
        desc='smooth vertices after coloring', argstr='--postsmooth')
    verbosity = traits.Int(desc='verbosity (0 = quiet)', argstr='-v %d')
    timer = traits.Bool(desc='timing function', argstr='--timer')


class DfsOutputSpec(TraitedSpec):
    outputSurfaceFile = File(desc='path/name of surface file')


class Dfs(BrainSuiteCommandLine):
    """
    Surface Generator
    Generates mesh surfaces using an isosurface algorithm.

    http://brainsuite.org/processing/surfaceextraction/inner-cortical-surface/

    Examples
    --------

    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> dfs = brainsuite.Dfs()
    >>> dfs.inputs.inputVolumeFile = example_data('structural.nii')
    >>> results = dfs.run() #doctest: +SKIP

    """

    input_spec = DfsInputSpec
    output_spec = DfsOutputSpec
    _cmd = 'dfs'

    def _format_arg(self, name, spec, value):
        if name == 'tessellationThreshold':
            return ''  # blank argstr
        if name == 'specialTessellation':
            threshold = self.inputs.tessellationThreshold
            return spec.argstr % \
                   {"greater_than": ''.join(("-gt %f" % threshold)), "less_than": ''.join(("-lt %f" % threshold)),
                    "equal_to": ''.join(("-eq %f" % threshold))}[value]
        return super(Dfs, self)._format_arg(name, spec, value)

    def _gen_filename(self, name):
        inputs = self.inputs.get()
        if isdefined(inputs[name]):
            return os.path.abspath(inputs[name])

        if name == 'outputSurfaceFile':
            return getFileName(self.inputs.inputVolumeFile, '.inner.cortex.dfs')

        return None

    def _list_outputs(self):
        return l_outputs(self)


class PialmeshInputSpec(CommandLineInputSpec):
    inputSurfaceFile = File(mandatory=True, desc='input file', argstr='-i %s')
    outputSurfaceFile = File(
        desc='output file. If unspecified, output file name will be auto generated.', argstr='-o %s',
        genfile=True, hash_files=True)
    verbosity = traits.Int(desc='verbosity', argstr='-v %d')
    inputTissueFractionFile = File(
        mandatory=True, desc='floating point (32) tissue fraction image', argstr='-f %s')
    numIterations = traits.Int(
        100, usedefault=True, desc='number of iterations', argstr='-n %d')
    searchRadius = traits.Float(
        1, usedefault=True, desc='search radius', argstr='-r %f')
    stepSize = traits.Float(0.4, usedefault=True,
                            desc='step size', argstr='-s %f')
    inputMaskFile = File(
        mandatory=True, desc='restrict growth to mask file region', argstr='-m %s')
    maxThickness = traits.Float(
        20, usedefault=True, desc='maximum allowed tissue thickness', argstr='--max %f')
    tissueThreshold = traits.Float(
        1.05, usedefault=True, desc='tissue threshold', argstr='-t %f')
    # output interval is not an output -- it specifies how frequently the
    # output surfaces are generated
    outputInterval = traits.Int(
        10, usedefault=True, desc='output interval', argstr='--interval %d')
    exportPrefix = traits.Str(
        desc='prefix for exporting surfaces if interval is set', argstr='--prefix %s')
    laplacianSmoothing = traits.Float(
        0.025, usedefault=True, desc='apply Laplacian smoothing', argstr='--smooth %f')
    timer = traits.Bool(desc='show timing', argstr='--timer')
    recomputeNormals = traits.Bool(
        desc='recompute normals at each iteration', argstr='--norm')
    normalSmoother = traits.Float(
        0.2, usedefault=True, desc='strength of normal smoother.', argstr='--nc %f')
    tangentSmoother = traits.Float(
        desc='strength of tangential smoother.', argstr='--tc %f')


class PialmeshOutputSpec(TraitedSpec):
    outputSurfaceFile = File(desc='path/name of surface file')


class Pialmesh(BrainSuiteCommandLine):
    """
    pialmesh
    computes a pial surface model using an inner WM/GM mesh and a tissue fraction map.

    http://brainsuite.org/processing/surfaceextraction/pial/

    Examples
    --------

    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> pialmesh = brainsuite.Pialmesh()
    >>> pialmesh.inputs.inputSurfaceFile = 'input_mesh.dfs'
    >>> pialmesh.inputs.inputTissueFractionFile = 'frac_file.nii.gz'
    >>> pialmesh.inputs.inputMaskFile = example_data('mask.nii')
    >>> results = pialmesh.run() #doctest: +SKIP

    """

    input_spec = PialmeshInputSpec
    output_spec = PialmeshOutputSpec
    _cmd = 'pialmesh'

    def _gen_filename(self, name):
        inputs = self.inputs.get()
        if isdefined(inputs[name]):
            return os.path.abspath(inputs[name])

        if name == 'outputSurfaceFile':
            return getFileName(self.inputs.inputSurfaceFile, '.pial.cortex.dfs')

        return None

    def _list_outputs(self):
        return l_outputs(self)


class HemisplitInputSpec(CommandLineInputSpec):
    inputSurfaceFile = File(
        mandatory=True, desc='input surface', argstr='-i %s')
    inputHemisphereLabelFile = File(
        mandatory=True, desc='input hemisphere label volume', argstr='-l %s')
    outputLeftHemisphere = File(
        desc='output surface file, left hemisphere. If unspecified, output file name will be auto generated.',
        argstr='--left %s', genfile=True, hash_files=True)
    outputRightHemisphere = File(
        desc='output surface file, right hemisphere. If unspecified, output file name will be auto generated.',
        argstr='--right %s', genfile=True, hash_files=True)
    pialSurfaceFile = File(
        desc='pial surface file -- must have same geometry as input surface', argstr='-p %s')
    outputLeftPialHemisphere = File(
        desc='output pial surface file, left hemisphere. If unspecified, output file name will be auto generated.',
        argstr='-pl %s', genfile=True, hash_files=True)
    outputRightPialHemisphere = File(
        desc='output pial surface file, right hemisphere. If unspecified, output file name will be auto generated.',
        argstr='-pr %s', genfile=True, hash_files=True)
    verbosity = traits.Int(desc='verbosity (0 = silent)', argstr='-v %d')
    timer = traits.Bool(desc='timing function', argstr='--timer')


class HemisplitOutputSpec(TraitedSpec):
    outputLeftHemisphere = File(desc='path/name of left hemisphere')
    outputRightHemisphere = File(desc='path/name of right hemisphere')
    outputLeftPialHemisphere = File(desc='path/name of left pial hemisphere')
    outputRightPialHemisphere = File(desc='path/name of right pial hemisphere')


class Hemisplit(BrainSuiteCommandLine):
    """
    Hemisphere splitter
    Splits a surface object into two separate surfaces given an input label volume.
    Each vertex is labeled left or right based on the labels being odd (left) or even (right).
    The largest contour on the split surface is then found and used as the separation between left and right.

    Examples
    --------

    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> hemisplit = brainsuite.Hemisplit()
    >>> hemisplit.inputs.inputSurfaceFile = 'input_surf.dfs'
    >>> hemisplit.inputs.inputHemisphereLabelFile = 'label.nii'
    >>> hemisplit.inputs.pialSurfaceFile = 'pial.dfs'
    >>> results = hemisplit.run() #doctest: +SKIP

    """

    input_spec = HemisplitInputSpec
    output_spec = HemisplitOutputSpec
    _cmd = 'hemisplit'

    def _gen_filename(self, name):
        inputs = self.inputs.get()
        if isdefined(inputs[name]):
            return os.path.abspath(inputs[name])

        fileToSuffixMap = {
            'outputLeftHemisphere': '.left.inner.cortex.dfs',
            'outputLeftPialHemisphere': '.left.pial.cortex.dfs',
            'outputRightHemisphere': '.right.inner.cortex.dfs',
            'outputRightPialHemisphere': '.right.pial.cortex.dfs'
        }
        if name in fileToSuffixMap:
            return getFileName(self.inputs.inputSurfaceFile, fileToSuffixMap[name])

        return None

    def _list_outputs(self):
        return l_outputs(self)


class SkullfinderInputSpec(CommandLineInputSpec):
    inputMRIFile = File(mandatory=True, desc='input file', argstr='-i %s')
    inputMaskFile = File(
        mandatory=True, desc='A brain mask file, 8-bit image (0=non-brain, 255=brain)', argstr='-m %s')
    outputLabelFile = File(
        desc='output multi-colored label volume segmenting brain, scalp, inner skull & outer skull '
             'If unspecified, output file name will be auto generated.',
        argstr='-o %s', genfile=True, hash_files=True)
    verbosity = traits.Int(desc='verbosity', argstr='-v %d')
    lowerThreshold = traits.Int(
        desc='Lower threshold for segmentation', argstr='-l %d')
    upperThreshold = traits.Int(
        desc='Upper threshold for segmentation', argstr='-u %d')
    surfaceFilePrefix = traits.Str(
        desc='if specified, generate surface files for brain, skull, and scalp', argstr='-s %s')
    bgLabelValue = traits.Int(
        desc='background label value (0-255)', argstr='--bglabel %d')
    scalpLabelValue = traits.Int(
        desc='scalp label value (0-255)', argstr='--scalplabel %d')
    skullLabelValue = traits.Int(
        desc='skull label value (0-255)', argstr='--skulllabel %d')
    spaceLabelValue = traits.Int(
        desc='space label value (0-255)', argstr='--spacelabel %d')
    brainLabelValue = traits.Int(
        desc='brain label value (0-255)', argstr='--brainlabel %d')
    performFinalOpening = traits.Bool(
        desc='perform a final opening operation on the scalp mask', argstr='--finalOpening')


class SkullfinderOutputSpec(TraitedSpec):
    outputLabelFile = File(desc='path/name of label file')


class Skullfinder(BrainSuiteCommandLine):
    """
    Skull and scalp segmentation algorithm.

    Examples
    --------

    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> skullfinder = brainsuite.Skullfinder()
    >>> skullfinder.inputs.inputMRIFile = example_data('structural.nii')
    >>> skullfinder.inputs.inputMaskFile = example_data('mask.nii')
    >>> results = skullfinder.run() #doctest: +SKIP

    """
    input_spec = SkullfinderInputSpec
    output_spec = SkullfinderOutputSpec
    _cmd = 'skullfinder'

    def _gen_filename(self, name):
        inputs = self.inputs.get()
        if isdefined(inputs[name]):
            return os.path.abspath(inputs[name])

        if name == 'outputLabelFile':
            return getFileName(self.inputs.inputMRIFile, '.skullfinder.label.nii.gz')

        return None

    def _list_outputs(self):
        return l_outputs(self)


class SVRegInputSpec(CommandLineInputSpec):
    subjectFilePrefix = traits.Str(
        argstr='\'%s\'', mandatory=True, position=0,
        desc='Absolute path and filename prefix of the subjects output from BrainSuite '
             'Cortical Surface Extraction Sequence'
    )
    dataSinkDelay = traits.Any(
        str, argstr='%s',
        desc='Connect datasink out_file to dataSinkDelay to delay execution of SVReg '
             'until dataSink has finished sinking CSE outputs.'
             'For use with parallel processing workflows including Brainsuites Cortical '
             'Surface Extraction sequence (SVReg requires certain files from Brainsuite '
             'CSE, which must all be in the pathway specified by subjectFilePrefix. see '
             'http://brainsuite.org/processing/svreg/usage/ for list of required inputs '
    )
    atlasFilePrefix = traits.Str(
        position=1, argstr='\'%s\'',
        desc='Optional: Absolute Path and filename prefix of atlas files and labels to which '
             'the subject will be registered. If unspecified, SVReg'
             'will use its own included atlas files'
    )
    iterations = traits.Int(
        argstr='\'-H %d\'',
        desc='Assigns a number of iterations in the intensity registration step.'
             'if unspecified, performs 100 iterations'
    )
    refineOutputs = traits.Bool(
        argstr='\'-r\'',
        desc='Refine outputs at the expense of more processing time.'
    )
    skipToVolumeReg = traits.Bool(
        argstr='\'-s\'',
        desc='If surface registration was already performed at an earlier time and the '
             'user would not like to redo this step, then this flag may be used to skip '
             'ahead to the volumetric registration. Necessary input files will need to '
             'be present in the input directory called by the command.'
    )
    skipToIntensityReg = traits.Bool(
        argstr='\'-p\'',
        desc='If the p-harmonic volumetric registration was already performed at an '
             'earlier time and the user would not like to redo this step, then this '
             'flag may be used to skip ahead to the intensity registration and '
             'label transfer step.'
    )
    useManualMaskFile = traits.Bool(
        argstr='\'-cbm\'',
        desc='Can call a manually edited cerebrum mask to limit boundaries. Will '
             'use file: subbasename.cerebrum.mask.nii.gz Make sure to correctly '
             'replace your manually edited mask file in your input folder with the '
             'correct subbasename.'
    )
    curveMatchingInstructions = traits.Str(
        argstr='\'-cur %s\'',
        desc='Used to take control of the curve matching process between the atlas '
             'and subject. One can specify the name of the .dfc file <sulname.dfc> and '
             'the sulcal numbers <#sul> to be used as constraints. '
             'example: curveMatchingInstructions = "subbasename.right.dfc 1 2 20"'
    )
    useCerebrumMask = traits.Bool(
        argstr='\'-C\'',
        desc='The cerebrum mask <subbasename.cerebrum.mask.nii.gz> will be used for '
             'masking the final labels instead of the default pial surface mask. '
             'Every voxel will be labeled within the cerebrum mask regardless of '
             'the boundaries of the pial surface.'
    )
    pialSurfaceMaskDilation = traits.Int(
        argstr='\'-D %d\'',
        desc='Cortical volume labels found in file output subbasename.svreg.label.nii.gz '
             'find its boundaries by using the pial surface then dilating by 1 voxel. '
             'Use this flag in order to control the number of pial surface mask dilation. '
             '(ie. -D 0 will assign no voxel dilation)'
    )
    keepIntermediates = traits.Bool(
        argstr='\'-k\'',
        desc='Keep the intermediate files after the svreg sequence is complete.'
    )
    _XOR_verbosity = ('verbosity0', 'verbosity1', 'verbosity2')
    verbosity0 = traits.Bool(
        argstr='\'-v0\'', xor=_XOR_verbosity,
        desc='no messages will be reported'
    )
    verbosity1 = traits.Bool(
        argstr='\'-v1\'', xor=_XOR_verbosity,
        desc='messages will be reported but not the iteration-wise detailed messages'
    )
    verbosity2 = traits.Bool(
        argstr='\'v2\'', xor=_XOR_verbosity,
        desc='all the messages, including per-iteration, will be displayed'
    )
    shortMessages = traits.Bool(
        argstr='\'-gui\'',
        desc='Short messages instead of detailed messages'
    )
    displayModuleName = traits.Bool(
        argstr='\'-m\'',
        desc='Module name will be displayed in the messages'
    )
    displayTimestamps = traits.Bool(
        argstr='\'-t\'',
        desc='Timestamps will be displayed in the messages'
    )
    skipVolumetricProcessing = traits.Bool(
        argstr='\'-S\'',
        desc='Only surface registration and labeling will be performed. Volumetric '
             'processing will be skipped.'
    )
    useMultiThreading = traits.Bool(
        argstr='\'-P\'',
        desc='If multiple CPUs are present on the system, the code will try to use '
             'multithreading to make the execution fast.'
    )
    useSingleThreading = traits.Bool(
        argstr='\'-U\'',
        desc='Use single threaded mode.'
    )


class SVRegOutputSpec(TraitedSpec):
    outputLabelFile = File(desc='path/name of svreg label file', hash_files=True)
    JacDetFile = File(desc='path/name of jacobian determinant of inverse map file', hash_files=True)
    InvMapFile = File(desc='path/name of inverse map file', hash_files=True)

class SVReg(BrainSuiteCommandLine):
    """
    surface and volume registration (svreg)
    This program registers a subject's BrainSuite-processed volume and surfaces
    to an atlas, allowing for automatic labelling of volume and surface ROIs.

    For more information, please see:
    http://brainsuite.org/processing/svreg/usage/

    Examples
    --------

    >>> from nipype.interfaces import brainsuite
    >>> svreg = brainsuite.SVReg()
    >>> svreg.inputs.subjectFilePrefix = 'home/user/btestsubject/testsubject'
    >>> svreg.inputs.refineOutputs = True
    >>> svreg.inputs.skipToVolumeReg = False
    >>> svreg.inputs. keepIntermediates = True
    >>> svreg.inputs.verbosity2 = True
    >>> svreg.inputs.displayTimestamps = True
    >>> svreg.inputs.useSingleThreading = True
    >>> results = svreg.run() #doctest: +SKIP


    """

    input_spec = SVRegInputSpec
    output_spec = SVRegOutputSpec
    _cmd = 'svreg.sh'

    def _gen_filename(self, name):
        fileToSuffixMap = {
            'outputLabelFile': '.svreg.label.nii.gz',
            'JacDetFile': '.svreg.inv.jacobian.nii.gz',
            'InvMapFile' : '.svreg.inv.map.nii.gz'
        }

        if name in fileToSuffixMap:
            return self.inputs.subjectFilePrefix + fileToSuffixMap[name]

        return None

    def _list_outputs(self):
        return l_outputs(self)

    def _format_arg(self, name, spec, value):
        if name == 'subjectFilePrefix' or name == 'atlasFilePrefix' or name == 'curveMatchingInstructions':
            return spec.argstr % os.path.expanduser(value)
        if name == 'dataSinkDelay':
            return spec.argstr % ''
        return super(SVReg, self)._format_arg(name, spec, value)


class BDPInputSpec(CommandLineInputSpec):
    bfcFile = File(
        argstr='%s', mandatory=True, position=0, xor=['noStructuralRegistration'],
        desc='Specify absolute path to file produced by bfc. By default, bfc produces the file in '
             'the format: prefix.bfc.nii.gz'
    )
    noStructuralRegistration = traits.Bool(
        argstr='--no-structural-registration', mandatory=True, position=0, xor=['bfcFile'],
        desc='Allows BDP to work without any structural input. This can useful when '
             'one is only interested in diffusion modelling part of BDP. With this '
             'flag only fieldmap-based distortion correction is supported. '
             'outPrefix can be used to specify fileprefix of the output '
             'filenames. Change dwiMask to define region of interest '
             'for diffusion modelling.'
    )
    inputDiffusionData = File(
        argstr='--nii %s', mandatory=True, position=-2,
        desc='Specifies the absolute path and filename of the input diffusion data in 4D NIfTI-1 '
             'format. The flag must be followed by the filename. Only NIfTI-1 files '
             'with extension .nii or .nii.gz are supported. Furthermore, either  '
             'bMatrixFile, or a combination of both bValueFile and diffusionGradientFile '
             'must be used to provide the necessary b-matrices/b-values and gradient vectors. '
    )
    bMatrixFile = File(
        argstr='--bmat %s', mandatory=True, xor=['BVecBValPair'], position=-1,
        desc='Specifies the absolute path and filename of the file containing b-matrices for '
             'diffusion-weighted scans. The flag must be followed by the filename. '
             'This file must be a plain text file containing 3x3 matrices for each '
             'diffusion encoding direction. It should contain zero matrices '
             'corresponding to b=0 images. This file usually has ".bmat" as its '
             'extension, and can be used to provide BDP with the more-accurate '
             'b-matrices as saved by some proprietary scanners. The b-matrices '
             'specified by the file must be in the voxel coordinates of the input '
             'diffusion weighted image (NIfTI file). In case b-matrices are not known/calculated, '
             'bvec and .bval files can be used instead (see diffusionGradientFile and bValueFile). '
    )
    BVecBValPair = traits.List(
        str, minlen=2, maxlen=2, mandatory=True, position=-1, xor=['bMatrixFile'],
        argstr='--bvec %s --bval %s',
        desc='Must input a list containing first the BVector file, then the BValue file (both must be absolute paths)\n'
             'Example: bdp.inputs.BVecBValPair = [\'/directory/subdir/prefix.dwi.bvec\', \'/directory/subdir/prefix.dwi.bval\'] '
             'The first item in the list specifies the filename of the file containing b-values for the '
             'diffusion scan. The b-value file must be a plain-text file and usually has an '
             'extension of .bval\n'
             'The second item in the list specifies the filename of the file containing the diffusion gradient '
             'directions (specified in the voxel coordinates of the input '
             'diffusion-weighted image)The b-vectors file must be a plain text file and '
             'usually has an extension of .bvec '
    )
    dataSinkDelay = traits.Any(
        str, argstr='%s',
        desc='For use in parallel processing workflows including Brainsuite Cortical '
             'Surface Extraction sequence. Connect datasink out_file to dataSinkDelay '
             'to delay execution of BDP until dataSink has finished sinking outputs. '
             'In particular, BDP may be run after BFC has finished. For more information '
             'see http://brainsuite.org/processing/diffusion/pipeline/'
    )
    phaseEncodingDirection = traits.Enum(
        'x', 'x-', 'y', 'y-', 'z', 'z-',
        argstr='--dir=%s',
        desc='Specifies the phase-encoding direction of the EPI (diffusion) images. '
             'It is same as the dominant direction of distortion in the images. This '
             'information is used to constrain the distortion correction along the '
             'specified direction. Directions are represented by any one of x, x-, y, '
             'y-, z or z-. "x" direction increases towards the right side of the '
             'subject, while "x-" increases towards the left side of the subject. '
             'Similarly, "y" and "y-" are along the anterior-posterior direction of '
             'the subject, and "z" & "z-" are along the inferior-superior direction. '
             'When this flag is not used, BDP uses "y" as the default phase-encoding '
             'direction. '
    )
    echoSpacing = traits.Float(
        argstr='--echo-spacing=%f',
        desc='Sets the echo spacing to t seconds, which is used for fieldmap-based '
             'distortion correction. This flag is required when using fieldmapCorrection'
    )
    bValRatioThreshold = traits.Float(
        argstr='--bval-ratio-threshold %f',
        desc='Sets a threshold which is used to determine b=0 images. When there are '
             'no diffusion weighted image with b-value of zero, then BDP tries to use '
             'diffusion weighted images with a low b-value in place of b=0 image. The '
             'diffusion images with minimum b-value is used as b=0 image only if the '
             'ratio of the maximum and minimum b-value is more than the specified '
             'threshold. A lower value of threshold will allow diffusion images with '
             'higher b-value to be used as b=0 image. The default value of this '
             'threshold is set to 45, if this trait is not set. '
    )
    estimateTensors = traits.Bool(
        argstr='--tensors',
        desc='Estimates diffusion tensors using a weighted log-linear estimation and '
             'saves derived diffusion tensor parameters (FA, MD, axial, radial, L2, '
             'L3). This is the default behavior if no diffusion modeling flags are '
             'specified. The estimated diffusion tensors can be visualized by loading '
             'the saved *.eig.nii.gz file in BrainSuite. BDP reports diffusivity (MD, '
             'axial, radial, L2 and L3) in a unit which is reciprocal inverse of the '
             'unit of input b-value. '
    )
    estimateODF_FRACT = traits.Bool(
        argstr='--FRACT',
        desc='Estimates ODFs using the Funk-Radon and Cosine Transformation (FRACT). '
             'The outputs are saved in a separate directory with name "FRACT" and the '
             'ODFs can be visualized by loading the saved ".odf" file in BrainSuite. '
    )
    estimateODF_FRT = traits.Bool(
        argstr='--FRT',
        desc='Estimates ODFs using Funk-Radon Transformation (FRT). The coefficient '
             'maps for ODFs are saved in a separate directory with name "FRT" and the '
             'ODFs can be visualized by loading the saved ".odf" file in BrainSuite. '
             'The derived generalized-FA (GFA) maps are also saved in the output '
             'directory. '
    )
    estimateODF_3DShore = traits.Bool(
        argstr='--3dshore ',
        desc='Estimates ODFs using 3Dshore. Pass in diffusion time, in ms'
    )
    estimateODF_GQI = traits.Bool(
        argstr='--gqi',
        desc='Estimates ODFs using the GQI method. The outputs are saved in a '
             'separate directory with name "GQI" and the ODFs can be visualized by '
             'loading the saved ".odf" file in BrainSuite.'
    )
    sigma_GQI = traits.Float(
        argstr='--gqi-simga %f',
        desc='Sets the GQI adjustable factor, required for calculating diffusion'
             'sampling length. The default value is set to 1.25. Paper suggests'
             'setting this parameter between 1 and 1.3.'
    )
    odfLambda = traits.Bool(
        argstr='--odf-lambda <L>',
        desc='Sets the regularization parameter, lambda, of the Laplace-Beltrami '
             'operator while estimating ODFs. The default value is set to 0.006 . This '
             'can be used to set the appropriate regularization for the input '
             'diffusion data. '
    )
    estimateODF_ERFO = traits.Bool(
        argstr='--erfo',
        desc='Estimates ODFs using the ERFO method. The outputs are saved in a'
             'separate directory with name "ERFO" and the ODFs can be visualized by '
             'loading the saved ".odf" file in BrainSuite.'
    )
    diffusion_time_ms = traits.Float(
        argstr='--diffusion_time_ms %f',
        desc='Estimates ODFs using 3Dshore and ERFO. Pass in diffusion time, in ms'
    )
    ERFO_SNR = traits.Float(
        argstr='--snr %f',
        desc='Sets the SNR of the acquired data, required for calculating ERFO ODFs. '
             'This is an optional parameter with the default value is set to 35.'
    )
    t1Mask = File(
        argstr='--t1-mask %s',
        desc='Specifies the filename of the brain-mask file for input T1-weighted '
             'image. This mask can be same as the brain mask generated during '
             'BrainSuite extraction sequence. For best results, the mask should not '
             'include any extra-meningial tissues from T1-weighted image. The mask '
             'must be in the same coordinates as input T1-weighted image (i.e. should '
             'overlay correctly with input <fileprefix>.bfc.nii.gz file in '
             'BrainSuite). This mask is used for co-registration and defining brain '
             'boundary for statistics computation. The mask can be generated and/or '
             'edited in BrainSuite. In case outputDiffusionCoordinates is also '
             'used, this mask is first transformed to diffusion coordinate and the '
             'transformed mask is used for defining brain boundary in diffusion '
             'coordinates. When t1Mask is not set, BDP will try to use '
             'fileprefix>.mask.nii.gz as brain-mask. If <fileprefix>.mask.nii.gz is '
             'not found, then BDP will use the input <fileprefix>.bfc.nii.gz itself as '
             'mask (i.e. all non-zero voxels in <fileprefix>.bfc.nii.gz is assumed to '
             'constitute brain mask).  '
    )
    dwiMask = File(
        argstr='--dwi-mask %s',
        desc='Specifies the filename of the brain-mask file for diffusion data. This '
             'mask is used only for co-registration purposes and can affect overall '
             'quality of co-registration (see t1Mask for definition of brain mask '
             'for statistics computation). The mask must be a 3D volume and should be '
             'in the same coordinates as input Diffusion file/data (i.e. should '
             'overlay correctly with input diffusion data in BrainSuite). For best '
             'results, the mask should include only brain voxels (CSF voxels around '
             'brain is also acceptable). When this flag is not used, BDP will generate '
             'a pseudo mask using first b=0 image volume and would save it as '
             'fileprefix>.dwi.RSA.mask.nii.gz. In case co-registration is not '
             'accurate with automatically generated pseudo mask, BDP should be re-run '
             'with a refined diffusion mask. The mask can be generated and/or edited '
             'in BrainSuite. '
    )
    rigidRegMeasure = traits.Enum(
        'MI', 'INVERSION', 'BDP',
        argstr='--rigid-reg-measure %s',
        desc='Defines the similarity measure to be used for rigid registration. '
             'Possible measures are "MI", "INVERSION" and "BDP". MI measure uses '
             'normalized mutual information based cost function. INVERSION measure '
             'uses simpler cost function based on sum of squared difference by '
             'exploiting the approximate inverse-contrast relationship in T1- and '
             'T2-weighted images. BDP measure combines MI and INVERSION. It starts '
             'with INVERSION measure and refines the result with MI measure. BDP is '
             'the default measure when this trait is not set.  '
    )
    dcorrRegMeasure = traits.Enum(
        'MI', 'INVERSION-EPI', 'INVERSION-T1', 'INVERSION-BOTH', 'BDP',
        argstr='--dcorr-reg-method %s',
        desc='Defines the method for registration-based distortion correction. '
             'Possible methods are "MI", "INVERSION-EPI", "INVERSION-T1", '
             'INVERSION-BOTH", and "BDP". MI method uses normalized mutual '
             'information based cost-function while estimating the distortion field. '
             'INVERSION-based method uses simpler cost function based on sum of '
             'squared difference by exploiting the known approximate contrast '
             'relationship in T1- and T2-weighted images. T2-weighted EPI is inverted '
             'when INVERSION-EPI is used; T1-image is inverted when INVERSION-T1 is '
             'used; and both are inverted when INVERSION-BOTH is used. BDP method add '
             'the MI-based refinement after the correction using INVERSION-BOTH '
             'method. BDP is the default method when this trait is not set.  '
    )
    dcorrWeight = traits.Float(
        argstr='--dcorr-regularization-wt %f',
        desc='Sets the (scalar) weighting parameter for regularization penalty in '
             'registration-based distortion correction. Set this trait to a single, non-negative '
             'number which specifies the weight. A large regularization weight encourages '
             'smoother distortion field at the cost of low measure of image similarity '
             'after distortion correction. On the other hand, a smaller regularization '
             'weight can result into higher measure of image similarity but with '
             'unrealistic and unsmooth distortion field. A weight of 0.5 would reduce '
             'the penalty to half of the default regularization penalty (By default, this weight '
             'is set to 1.0). Similarly, a weight of 2.0 '
             'would increase the penalty to twice of the default penalty.  '
    )
    skipDistortionCorr = traits.Bool(
        argstr='--no-distortion-correction',
        desc='Skips distortion correction completely and performs only a rigid '
             'registration of diffusion and T1-weighted image. This can be useful when '
             'the input diffusion images do not have any distortion or they have been '
             'corrected for distortion. '
    )
    skipNonuniformityCorr = traits.Bool(
        argstr='--no-nonuniformity-correction',
        desc='Skips intensity non-uniformity correction in b=0 image for '
             'registration-based distortion correction. The intensity non-uniformity '
             'correction does not affect any diffusion modeling. '
    )
    skipIntensityCorr = traits.Bool(
        argstr='--no-intensity-correction', xor=['fieldmapCorrectionMethod'],
        desc='Disables intensity correction when performing distortion correction. '
             'Intensity correction can change the noise distribution in the corrected '
             'image, but it does not affect estimated diffusion parameters like FA, '
             'etc. '
    )
    fieldmapCorrection = File(
        argstr='--fieldmap-correction %s', requires=['echoSpacing'],
        desc='Use an acquired fieldmap for distortion correction. The fieldmap must '
             'have units of radians/second. Specify the filename of the fieldmap file. '
             'The field of view (FOV) of the fieldmap scan must cover the FOV of the diffusion '
             'scan. BDP will try to check the overlap of the FOV of the two scans and '
             'will issue a warning/error if the diffusion scan"s FOV is not fully '
             'covered by the fieldmap"s FOV. BDP uses all of the information saved in '
             'the NIfTI header to compute the FOV. If you get this error and think '
             'that it is incorrect, then it can be suppressed using the flag '
             'ignore-fieldmap-FOV. Neither the image matrix size nor the imaging '
             'grid resolution of the fieldmap needs to be the same as that of the '
             'diffusion scan, but the fieldmap must be pre-registred to the diffusion '
             'scan. BDP does NOT align the fieldmap to the diffusion scan, nor does it '
             'check the alignment of the fieldmap and diffusion scans. Only NIfTI '
             'files with extension of .nii or .nii.gz are supported. Fieldmap-based '
             'distortion correction also requires the echoSpacing. Also '
             'fieldmapCorrectionMethod allows you to define method for '
             'distortion correction. least squares is the default method. '
    )
    fieldmapCorrectionMethod = traits.Enum(
        'pixelshift', 'leastsq', xor=['skipIntensityCorr'],
        argstr='--fieldmap-correction-method %s',
        desc='Defines the distortion correction method while using fieldmap. '
             'Possible methods are "pixelshift" and "leastsq". leastsq is the default '
             'method when this flag is not used. Pixel-shift (pixelshift) method uses '
             'image interpolation to un-distort the distorted diffusion images. Least '
             'squares (leastsq) method uses a physical model of distortion which is '
             'more accurate (and more computationally expensive) than pixel-shift '
             'method.'
    )
    ignoreFieldmapFOV = traits.Bool(
        argstr='--ignore-fieldmap-fov',
        desc='Supresses the error generated by an insufficient field of view of the '
             'input fieldmap and continues with the processing. It is useful only when '
             'used with fieldmap-based distortion correction. See '
             'fieldmap-correction for a detailed explanation. '
    )
    fieldmapSmooth = traits.Float(
        argstr='--fieldmap-smooth3=%f',
        desc='Applies 3D Gaussian smoothing with a standard deviation of S '
             'millimeters (mm) to the input fieldmap before applying distortion '
             'correction. This trait is only useful with '
             'fieldmapCorrection. Skip this trait for no smoothing. '
    )
    transformDiffusionVolume = File(
        argstr='--transform-diffusion-volume %s',
        desc='This flag allows to define custom volumes in diffusion coordinate '
             'which would be transformed into T1 coordinate in a rigid fashion. The '
             'flag must be followed by the name of either a NIfTI file or of a folder '
             'that contains one or more NIfTI files. All of the files must be in '
             'diffusion coordinate, i.e. the files should overlay correctly with the '
             'diffusion scan in BrainSuite. Only NIfTI files with an extension of .nii '
             'or .nii.gz are supported. The transformed files are written to the '
             'output directory with suffix ".T1_coord" in the filename and will not be '
             'corrected for distortion, if any. The trait transformInterpolation can '
             'be used to define the type of interpolation that would be used (default '
             'is set to linear). If you are attempting to transform a label file or '
             'mask file, use "nearest" interpolation method with transformInterpolation. '
             'See also transformT1Volume and transformInterpolation'
    )
    transformT1Volume = File(
        argstr='--transform-t1-volume %s',
        desc='Same as transformDiffusionVolume except that files specified must '
             'be in T1 coordinate, i.e. the files should overlay correctly with the '
             'input <fileprefix>.bfc.nii.gz files in BrainSuite. BDP transforms these '
             'data/images from T1 coordinate to diffusion coordinate. The transformed '
             'files are written to the output directory with suffix ".D_coord" in the '
             'filename. See also transformDiffusionVolume  and transformInterpolation. '
    )
    transformInterpolation = traits.Enum(
        'linear', 'nearest', 'cubic', 'spline',
        argstr='--transform-interpolation %s',
        desc='Defines the type of interpolation method which would be used while '
             'transforming volumes defined by transformT1Volume and '
             'transformDiffusionVolume. Possible methods are "linear", "nearest", '
             '"cubic" and "spline". By default, "linear" interpolation is used. '
    )
    transformT1Surface = File(
        argstr='--transform-t1-surface %s',
        desc='Similar to transformT1Volume, except that this flag allows '
             'transforming surfaces (instead of volumes) in T1 coordinate into '
             'diffusion coordinate in a rigid fashion. The flag must be followed by '
             'the name of either a .dfs file or of a folder that contains one or more '
             'dfs files. All of the files must be in T1 coordinate, i.e. the files '
             'should overlay correctly with the T1-weighted scan in BrainSuite. The '
             'transformed files are written to the output directory with suffix '
             'D_coord" in the filename. '
    )
    transformDiffusionSurface = File(
        argstr='--transform-diffusion-surface %s',
        desc='Same as transformT1Volume, except that the .dfs files specified '
             'must be in diffusion coordinate, i.e. the surface files should overlay '
             'correctly with the diffusion scan in BrainSuite. The transformed files '
             'are written to the output directory with suffix ".T1_coord" in the '
             'filename. See also transformT1Volume. '
    )
    transformDataOnly = traits.Bool(
        argstr='--transform-data-only',
        desc='Skip all of the processing (co-registration, distortion correction and '
             'tensor/ODF estimation) and directly start transformation of defined '
             'custom volumes, mask and labels (using transformT1Volume, '
             'transformDiffusionVolume, transformT1Surface, '
             'transformDiffusionSurface, customDiffusionLabel, '
             'customT1Label). This flag is useful when BDP was previously run on a '
             'subject (or <fileprefix>) and some more data (volumes, mask or labels) '
             'need to be transformed across the T1-diffusion coordinate spaces. This '
             'assumes that all the necessary files were generated earlier and all of '
             'the other flags MUST be used in the same way as they were in the initial '
             'BDP run that processed the data. '
    )
    generateStats = traits.Bool(
        argstr='--generate-stats',
        desc='Generate ROI-wise statistics of estimated diffusion tensor parameters. '
             'Units of the reported statistics are same as that of the estimated '
             'tensor parameters (see estimateTensors). Mean, variance, and voxel counts of '
             'white matter(WM), grey matter(GM), and both WM and GM combined are '
             'written for each estimated parameter in a separate comma-seperated value '
             'csv) file. BDP uses the ROI labels generated by Surface-Volume '
             'Registration (SVReg) in the BrainSuite extraction sequence. '
             'Specifically, it looks for labels saved in either '
             'fileprefix>.svreg.corr.label.nii.gz or <fileprefix>.svreg.label.nii.gz. '
             'In case both files are present, only the first file is used. Also see '
             'customDiffusionLabel and customT1Label for specifying your own '
             'ROIs. It is also possible to forgo computing the SVReg ROI-wise '
             'statistics and only compute stats with custom labels if SVReg label is '
             'missing. BDP also transfers (and saves) the label/mask files to '
             'appropriate coordinates before computing statistics. Also see '
             'outputDiffusionCoordinates for outputs in diffusion coordinate and '
             'forcePartialROIStats for an important note about field of view of '
             'diffusion and T1-weighted scans. '
    )
    onlyStats = traits.Bool(
        argstr='--generate-only-stats',
        desc='Skip all of the processing (co-registration, distortion correction and '
             'tensor/ODF estimation) and directly start computation of statistics. '
             'This flag is useful when BDP was previously run on a subject (or '
             'fileprefix>) and statistics need to be (re-)computed later. This '
             'assumes that all the necessary files were generated earlier. All of the '
             'other flags MUST be used in the same way as they were in the initial BDP '
             'run that processed the data. '
    )
    forcePartialROIStats = traits.Bool(
        argstr='--force-partial-roi-stats',
        desc='The field of view (FOV) of the diffusion and T1-weighted scans may '
             'differ significantly in some situations. This may result in partial '
             'acquisitions of some ROIs in the diffusion scan. By default, BDP does '
             'not compute statistics for partially acquired ROIs and shows warnings. '
             'This flag forces computation of statistics for all ROIs, including those '
             'which are partially acquired. When this flag is used, number of missing '
             'voxels are also reported for each ROI in statistics files. Number of '
             'missing voxels are reported in the same coordinate system as the '
             'statistics file.  '
    )
    customDiffusionLabel = File(
        argstr='--custom-diffusion-label %s',
        desc='BDP supports custom ROIs in addition to those generated by BrainSuite '
             'SVReg) for ROI-wise statistics calculation. The flag must be followed '
             'by the name of either a file (custom ROI file) or of a folder that '
             'contains one or more ROI files. All of the files must be in diffusion '
             'coordinate, i.e. the label files should overlay correctly with the '
             'diffusion scan in BrainSuite. These input label files are also '
             'transferred (and saved) to T1 coordinate for statistics in T1 '
             'coordinate. BDP uses nearest-neighborhood interpolation for this '
             'transformation. Only NIfTI files, with an extension of .nii or .nii.gz '
             'are supported. In order to avoid confusion with other ROI IDs in the '
             'statistic files, a 5-digit ROI ID is generated for each custom label '
             'found and the mapping of ID to label file is saved in the file '
             'fileprefix>.BDP_ROI_MAP.xml. Custom label files can also be generated '
             'by using the label painter tool in BrainSuite. See also '
             'customLabelXML'
    )
    customT1Label = File(
        argstr='--custom-t1-label %s',
        desc='Same as customDiffusionLabelexcept that the label files specified '
             'must be in T1 coordinate, i.e. the label files should overlay correctly '
             'with the T1-weighted scan in BrainSuite. If the trait '
             'outputDiffusionCoordinates is also used then these input label files '
             'are also transferred (and saved) to diffusion coordinate for statistics '
             'in diffusion coordinate. BDP uses nearest-neighborhood interpolation for '
             'this transformation. See also customLabelXML. '
    )
    customLabelXML = File(
        argstr='--custom-label-xml %s',
        desc='BrainSuite saves a descriptions of the SVReg labels (ROI name, ID, '
             'color, and description) in an .xml file '
             'brainsuite_labeldescription.xml). BDP uses the ROI ID"s from this xml '
             'file to report statistics. This flag allows for the use of a custom '
             'label description xml file. The flag must be followed by an xml '
             'filename. This can be useful when you want to limit the ROIs for which '
             'you compute statistics. You can also use custom xml files to name your '
             'own ROIs (assign ID"s) for custom labels. BrainSuite can save a label '
             'description in .xml format after using the label painter tool to create '
             'a ROI label. The xml file MUST be in the same format as BrainSuite"s '
             'label description file (see brainsuite_labeldescription.xml for an '
             'example). When this flag is used, NO 5-digit ROI ID is generated for '
             'custom label files and NO Statistics will be calculated for ROIs not '
             'identified in the custom xml file. See also customDiffusionLabel and '
             'customT1Label.'
    )
    outputSubdir = traits.Str(
        argstr='--output-subdir %s',
        desc='By default, BDP writes out all the output (and intermediate) files in '
             'the same directory (or folder) as the BFC file. This flag allows to '
             'specify a sub-directory name in which output (and intermediate) files '
             'would be written. BDP will create the sub-directory in the same '
             'directory as BFC file. <directory_name> should be the name of the '
             'sub-directory without any path. This can be useful to organize all '
             'outputs generated by BDP in a separate sub-directory. '
    )
    outputDiffusionCoordinates = traits.Bool(
        argstr='--output-diffusion-coordinate',
        desc='Enables estimation of diffusion tensors and/or ODFs (and statistics if '
             'applicable) in the native diffusion coordinate in addition to the '
             'default T1-coordinate. All native diffusion coordinate files are saved '
             'in a seperate folder named "diffusion_coord_outputs". In case statistics '
             'computation is required, it will also transform/save all label/mask '
             'files required to diffusion coordinate (see generateStats for '
             'details). '
    )
    flagConfigFile = File(
        argstr='--flag-conf-file %s',
        desc='Uses the defined file to specify BDP flags which can be useful for '
             'batch processing. A flag configuration file is a plain text file which '
             'can contain any number of BDP"s optional flags (and their parameters) '
             'separated by whitespace. Everything coming after # until end-of-line is '
             'treated as comment and is ignored. If a flag is defined in configuration '
             'file and is also specified in the command used to run BDP, then the '
             'later get preference and overrides the definition in configuration '
             'file. '
    )
    outPrefix = traits.Str(
        argstr='--output-fileprefix %s',
        desc='Specifies output fileprefix when noStructuralRegistration is '
             'used. The fileprefix can not start with a dash (-) and should be a '
             'simple string reflecting the absolute path to desired location, along with outPrefix. When this flag is '
             'not specified (and noStructuralRegistration is used) then the output '
             'files have same file-base as the input diffusion file. This trait is '
             'ignored when noStructuralRegistration is not used. '
    )
    threads = traits.Int(
        argstr='--threads=%d',
        desc='Sets the number of parallel process threads which can be used for '
             'computations to N, where N must be an integer. Default value of N is '
             ' '
    )
    lowMemory = traits.Bool(
        argstr='--low-memory',
        desc='Activates low-memory mode. This will run the registration-based '
             'distortion correction at a lower resolution, which could result in a '
             'less-accurate correction. This should only be used when no other '
             'alternative is available. '
    )
    ignoreMemory = traits.Bool(
        argstr='--ignore-memory',
        desc='Deactivates the inbuilt memory checks and forces BDP to run '
             'registration-based distortion correction at its default resolution even '
             'on machines with a low amount of memory. This may result in an '
             'out-of-memory error when BDP cannot allocate sufficient memory. '
    )
    maskOnly = traits.Bool(
        argstr='--mask-only',
        desc='Generates brain mask in the diffusion data only and does not perform other '
            'processing.'
    )


class BDPOutputSpec(TraitedSpec):
    corrFA = File(desc='path/name of distortion corrected FA map file', hash_files=True)
    corrColorFA = File(desc='path/name of distortion corrected color FA map file', hash_files=True)
    corrMADC = File(desc='path/name of distortion corrected mADC map file', hash_files=True)
    corrAxial = File(desc='path/name of distortion corrected Axial map file', hash_files=True)
    corrRadial = File(desc='path/name of distortion corrected Radial map file', hash_files=True)
    corrMD = File(desc='path/name of distortion corrected MD map file', hash_files=True)
    corrFRTGFA = File(desc='path/name of distortion corrected FRT_GFA map file', hash_files=True)

    FA = File(desc='path/name of non-distortion corrected FA map file', hash_files=True)
    ColorFA = File(desc='path/name of non-distortion corrected color FA map file', hash_files=True)
    MADC = File(desc='path/name of non-distortion corrected mADC map file', hash_files=True)
    Axial = File(desc='path/name of non-distortion corrected Axial map file', hash_files=True)
    Radial = File(desc='path/name of non-distortion corrected Radial map file', hash_files=True)
    MD = File(desc='path/name of non-distortion corrected MD map file', hash_files=True)
    FRTGFA = File(desc='path/name of non-distortion corrected FRT_GFA map file', hash_files=True)

    DcoordMask = File(desc='path/name of T1 brain mask file transformed into diffusion space', hash_files=True)
    PreCorrDWI = File(desc='path/name of non-distortion corrected DWI file', hash_files=True)
    PostCorrDWI = File(desc='path/name of distortion corrected DWI file', hash_files=True)
    tensor_coord = File(desc='path/name of the tensor bst file in T1 coordinate space', hash_files=True)
    DWIMask = File(desc='path/name of the DWI mask file in Diffusion coordinate space', hash_files=True)
    dummy = traits.Str(desc='dummy output')


class BDP(BrainSuiteCommandLine):
    """
    BrainSuite Diffusion Pipeline (BDP) enables fusion of diffusion and
    structural MRI information for advanced image and connectivity analysis.
    It provides various methods for distortion correction, co-registration,
    diffusion modeling (DTI and ODF) and basic ROI-wise statistic. BDP is a
    flexible and diverse tool which supports wide variety of diffusion
    datasets.
    For more information, please see:

    http://brainsuite.org/processing/diffusion/

    Examples
    --------

    >>> from nipype.interfaces import brainsuite
    >>> bdp = brainsuite.BDP()
    >>> bdp.inputs.bfcFile = '/directory/subdir/prefix.bfc.nii.gz'
    >>> bdp.inputs.inputDiffusionData = '/directory/subdir/prefix.dwi.nii.gz'
    >>> bdp.inputs.BVecBValPair = ['/directory/subdir/prefix.dwi.bvec', '/directory/subdir/prefix.dwi.bval']
    >>> results = bdp.run() #doctest: +SKIP


    """

    input_spec = BDPInputSpec
    output_spec = BDPOutputSpec
    _cmd = 'bdp.sh'

    def _gen_filename(self, name):

        fileToSuffixMap = {
            'corrFA': '.dwi.RAS.correct.FA.T1_coord.nii.gz',
            'corrColorFA': '.dwi.RAS.correct.FA.color.T1_coord.nii.gz',
            'corrMADC': '.dwi.RAS.correct.mADC.T1_coord.nii.gz',
            'corrAxial': '.dwi.RAS.correct.axial.T1_coord.nii.gz',
            'corrRadial': '.dwi.RAS.correct.radial.T1_coord.nii.gz',
            'corrMD': '.dwi.RAS.correct.MD.T1_coord.nii.gz',
            'corrFRTGFA': '.dwi.RAS.correct.FRT_GFA.T1_coord.nii.gz',
            'FA': '.dwi.RAS.FA.T1_coord.nii.gz',
            'ColorFA': '.dwi.RAS.FA.color.T1_coord.nii.gz',
            'MADC': '.dwi.RAS.mADC.T1_coord.nii.gz',
            'Axial': '.dwi.RAS.axial.T1_coord.nii.gz',
            'Radial': '.dwi.RAS.radial.T1_coord.nii.gz',
            'MD': '.dwi.RAS.MD.T1_coord.nii.gz',
            'FRTGFA': '.dwi.RAS.FRT_GFA.T1_coord.nii.gz',
            'PreCorrDWI': '.dwi.RAS.nii.gz',
            'DcoordMask' : '.D_coord.mask.nii.gz',
            'PostCorrDWI': '.dwi.RAS.correct.nii.gz',
            'tensor_coord': '.tensor.T1_coord.bst',
            'DWIMask': '.RAS.mask.nii.gz'
        }

        if name == 'DWIMask':
            return getFileName(self.inputs.inputDiffusionData, fileToSuffixMap[name])
        elif name in fileToSuffixMap:
            try:
                return getFileName(self.inputs.bfcFile, fileToSuffixMap[name])
            except TypeError:
                return getFileName(self.inputs.inputDiffusionData, fileToSuffixMap[name])

        # if name == 'tensor_coord':
        #     return getFileName(self.inputs.inputDiffusionData, '.tensor.T1_coord.bst')
        if name == 'dummy':
            return ''
        return None

    def _list_outputs(self):
        return l_outputs(self)

    def _format_arg(self, name, spec, value):
        if name == 'BVecBValPair':
            return spec.argstr % (value[0], value[1])
        if name == 'dataSinkDelay':
            return spec.argstr % ''
        return super(BDP, self)._format_arg(name, spec, value)


class ThicknessPVCInputSpec(CommandLineInputSpec):
    subjectFilePrefix = traits.Str(
        argstr='%s', mandatory=True,
        desc='Absolute path and filename prefix of the subject data'
    )
    dataSinkDelay = traits.List(
        str, argstr='%s',
        desc='Connect datasink out_file to dataSinkDelay to delay execution of SVReg '
             'until dataSink has finished sinking CSE outputs.'
             'For use with parallel processing workflows including Brainsuites Cortical '
             'Surface Extraction sequence (SVReg requires certain files from Brainsuite '
             'CSE, which must all be in the pathway specified by subjectFilePrefix. see '
             'http://brainsuite.org/processing/svreg/usage/ for list of required inputs '
    )


class ThicknessPVCOutputSpec(TraitedSpec):
    atlasSurfLeftFile = File(desc='path/name of atlas-registered surface file containing left cortical thickness data')
    atlasSurfRightFile = File(
        desc='path/name of atlas-registered surface file containing right cortical thickness data')


class ThicknessPVC(BrainSuiteCommandLine):
    """
    ThicknessPVC computes cortical thickness using partial tissue fractions.
    This thickness measure is then transferred to the atlas surface to
    facilitate population studies. It also stores the computed thickness into
    separate hemisphere files and subject thickness mapped to the atlas
    hemisphere surfaces. ThicknessPVC is not run through the main SVReg
    sequence, and should be used after executing the BrainSuite and SVReg
    sequence.
    For more informaction, please see:

    http://brainsuite.org/processing/svreg/svreg_modules/

    Examples
    --------

    >>> from nipype.interfaces import brainsuite
    >>> thicknessPVC = brainsuite.ThicknessPVC()
    >>> thicknessPVC.inputs.subjectFilePrefix = 'home/user/btestsubject/testsubject'
    >>> results = thicknessPVC.run() #doctest: +SKIP

    """

    input_spec = ThicknessPVCInputSpec
    output_spec = ThicknessPVCOutputSpec
    _cmd = 'thicknessPVC.sh'

    def _gen_filename(self, name):
        if name == 'atlasSurfLeftFile':
            return getFileName(self.inputs.subjectFilePrefix, '.pvc-thickness_0-6mm.left.mid.cortex.dfs')
        if name == 'atlasSurfRightFile':
            return getFileName(self.inputs.subjectFilePrefix, '.pvc-thickness_0-6mm.right.mid.cortex.dfs')
        return None

    def _list_outputs(self):
        return l_outputs(self)

    def _format_arg(self, name, spec, value):
        if name == 'subjectFilePrefix':
            return spec.argstr % os.path.expanduser(value)
        if name == 'dataSinkDelay':
            return spec.argstr % ''

        return super(ThicknessPVC, self)._format_arg(name, spec, value)


class Thickness2AtlasInputSpec(CommandLineInputSpec):
    subjectFilePrefix = traits.Str(
        argstr='%s', mandatory=True,
        desc='Absolute path and filename prefix of the subject data'
    )
    dataSinkDelay = traits.Any(
        str, argstr='%s',
        desc='Connect datasink out_file to dataSinkDelay to delay execution of SVReg '
             'until dataSink has finished sinking CSE outputs.'
             'For use with parallel processing workflows including Brainsuites Cortical '
             'Surface Extraction sequence (SVReg requires certain files from Brainsuite '
             'CSE, which must all be in the pathway specified by subjectFilePrefix. see '
             'http://brainsuite.org/processing/svreg/usage/ for list of required inputs '
    )


class Thickness2AtlasOutputSpec(TraitedSpec):
    atlasSurfLeftFile = File(desc='path/name of atlas-registered surface file containing left cortical thickness data')
    atlasSurfRightFile = File(
        desc='path/name of atlas-registered surface file containing right cortical thickness data')


class Thickness2Atlas(BrainSuiteCommandLine):
    """
    ThicknessPVC computes cortical thickness using partial tissue fractions.
    This thickness measure is then transferred to the atlas surface to
    facilitate population studies. It also stores the computed thickness into
    separate hemisphere files and subject thickness mapped to the atlas
    hemisphere surfaces. ThicknessPVC is not run through the main SVReg
    sequence, and should be used after executing the BrainSuite and SVReg
    sequence.
    For more informaction, please see:

    http://brainsuite.org/processing/svreg/svreg_modules/

    Examples
    --------

    >>> from nipype.interfaces import brainsuite
    >>> Thickness2Atlas = brainsuite.Thickness2Atlas()
    >>> Thickness2Atlas.inputs.subjectFilePrefix = 'home/user/btestsubject/testsubject'
    >>> results = Thickness2Atlas.run() #doctest: +SKIP

    """

    input_spec = Thickness2AtlasInputSpec
    output_spec = Thickness2AtlasOutputSpec
    _cmd = 'svreg_thickness2atlas.sh'

    def _gen_filename(self, name):
        if name == 'atlasSurfLeftFile':
            return os.path.join(os.path.dirname(self.inputs.subjectFilePrefix), 'atlas.pvc-thickness_0-6mm.left.mid.cortex.dfs')
        if name == 'atlasSurfRightFile':
            return os.path.join(os.path.dirname(self.inputs.subjectFilePrefix),'atlas.pvc-thickness_0-6mm.right.mid.cortex.dfs')
        return None

    def _list_outputs(self):
        return l_outputs(self)

    def _format_arg(self, name, spec, value):
        if name == 'subjectFilePrefix':
            return spec.argstr % os.path.expanduser(value)
        if name == 'dataSinkDelay':
            return spec.argstr % ''

        return super(Thickness2Atlas, self)._format_arg(name, spec, value)


class SVRegSmoothSurfInputSpec(CommandLineInputSpec):
    inputSurface = File(mandatory=True, argstr='%s', position=0, desc='input surface file')
    funcFile = File(mandatory=True, argstr='%s', position=1,
                    desc='surface file with function to be smoothed in .attributes field')
    outSurface = File(mandatory=True, argstr='%s', position=2, desc='output surface file', genfile=True,
                      hash_files=True)
    param = traits.Float(mandatory=False, argstr='%f', position=3, desc='smoothing parameter (std dev in mm)')
    dataSinkDelay = traits.List(
        str,
        argstr='%s',
        desc='Connect datasink out_file to dataSinkDelay to delay execution of '
             'SVReg smooth surf until dataSink has finished sinking SVReg outputs.'
    )


class SVRegSmoothSurfOutputSpec(TraitedSpec):
    smoothSurfFile = File(desc='path/name of smoothed surface file')


class SVRegSmoothSurf(BrainSuiteCommandLine):
    """
        SVRegApplyMap (SVRegApplyMap)
        This program applies an SVReg deformation file to an input volume.

        http://brainsuite.org/processing/svreg/

        Examples
        --------

        >>> from nipype.interfaces import brainsuite
        >>> from nipype.testing import example_data
        >>> svregSmoothSurf = brainsuite.SVRegSmoothSurf()
        >>> svregSmoothSurf.inputs.inputMRIFile = example_data('structural.nii')
        >>> results = svregApplyMap.run() #doctest: +SKIP
        """

    input_spec = SVRegSmoothSurfInputSpec
    output_spec = SVRegSmoothSurfOutputSpec
    _cmd = 'svreg_smooth_surf_function.sh'

    def _gen_filename(self, name):
        return self.inputs.outSurface

    def _list_outputs(self):
        return l_outputs(self)

    def _format_arg(self, name, spec, value):
        if name == 'inputSurface':
            return spec.argstr % os.path.expanduser(value)
        if name == 'dataSinkDelay':
            return spec.argstr % ''

        return super(SVRegSmoothSurf, self)._format_arg(name, spec, value)


class SVRegApplyMapInputSpec(CommandLineInputSpec):
    mapFile = File(mandatory=True, argstr='%s', position=0, desc='input SVReg map file')
    dataFile = File(mandatory=True, argstr='%s', position=1, desc='input nifti datafile file')
    outFile = File(mandatory=True, argstr='%s', position=2, desc='output resampled nifti file containing warped data',
                   genfile=True, hash_files=True)
    targetFile = File(mandatory=True, argstr='%s', position=3, desc='target image file for copying header')
    dataSinkDelay = traits.List(
        str,
        argstr='',
        desc='Connect datasink out_file to dataSinkDelay to delay execution of '
             'SVReg apply map until dataSink has finished sinking SVReg outputs.'
    )


class SVRegApplyMapOutputSpec(TraitedSpec):
    mappedFile = File(desc='path/name of resampled nifti file containing warped data')


class SVRegApplyMap(BrainSuiteCommandLine):
    """
        SVRegApplyMap (SVRegApplyMap)
        This program applies an SVReg deformation file to an input volume.

    http://brainsuite.org/processing/svreg/

    Examples
        --------

    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> svregApplyMap = brainsuite.SVRegApplyMap()
    >>> svregApplyMap.inputs.inputMRIFile = example_data('structural.nii')
    >>> results = svregApplyMap.run() #doctest: +SKIP
    """

    input_spec = SVRegApplyMapInputSpec
    output_spec = SVRegApplyMapOutputSpec
    _cmd = 'svreg_apply_map.sh'

    def _format_arg(self, name, spec, value):
        if name == 'dataSinkDelay':
            return spec.argstr % ''

        return super(SVRegApplyMap, self)._format_arg(name, spec, value)

    def _gen_filename(self, name):
        if name == 'mappedFile':
            return self.inputs.outFile

    def _list_outputs(self):
        return l_outputs(self)


class SVRegSmoothVolInputSpec(CommandLineInputSpec):
    inFile = File(mandatory=True, argstr='%s', position=0, desc='input DTI vol file')
    stdx = traits.Float(mandatory=True, argstr='%f', position=1,
                        desc='smoothing parameter (std dev in mm) in x direction')
    stdy = traits.Float(mandatory=True, argstr='%f', position=2,
                        desc='smoothing parameter (std dev in mm) in y direction')
    stdz = traits.Float(mandatory=True, argstr='%f', position=3,
                        desc='smoothing parameter (std dev in mm) in z direction')
    outFile = File(mandatory=True, argstr='%s', position=4, desc='output smoothed vol filei',
                   genfile=True, hash_files=True)
    dataSinkDelay = traits.List(
        str,
        argstr='%s',
        desc='Connect datasink out_file to dataSinkDelay to delay execution of '
             'SVReg smooth vol until dataSink has finished sinking SVReg apply map outputs.'
    )


class SVRegSmoothVolOutputSpec(TraitedSpec):
    smoothFile = File(desc='path/name of resampled nifti file containing smooth vol data')


class SVRegSmoothVol(BrainSuiteCommandLine):
    """
        SVRegSmoothVol (SVRegSmoothVol)
        This program applies volumetric smoothing on an input atlas file.

    http://brainsuite.org/processing/svreg/

    Examples
        --------

    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> svregSmoothVol = brainsuite.SVRegSmoothVol()
    >>> svregSmoothVol.inputs.inFile = example_data('structural.nii')
    >>> results = svregSmoothVol.run() #doctest: +SKIP
    """

    input_spec = SVRegSmoothVolInputSpec
    output_spec = SVRegSmoothVolOutputSpec
    _cmd = 'svreg_smooth_vol_function.sh'

    def _format_arg(self, name, spec, value):
        if name == 'dataSinkDelay':
            return spec.argstr % ''

        return super(SVRegSmoothVol, self)._format_arg(name, spec, value)

    def _gen_filename(self, name):
        return self.inputs.outFile
        # return None

    def _list_outputs(self):
        return l_outputs(self)

class GSmoothInputSpec(CommandLineInputSpec):
    inFile = File(mandatory=True, argstr='-i %s', desc='input MRI volume')
    outFile = File(mandatory=True, desc='output smoothed volume file.', argstr='-o %s', genfile=True,
                   hash_files=True)
    sigma = traits.Str( desc='std dev of filter in x, y, and z dimensions. [default: 3 3 3]',
        argstr='-s %s')
    float32 = traits.Bool(desc='use float32 for all calculations and outputs', argstr='--float32')
    delta = traits.Bool(desc='add 1e-4 to the sigma values', argstr='--delta')
    dataSinkDelay = traits.List(
        str,
        argstr='%s',
        desc='Connect datasink out_file to dataSinkDelay to delay execution of '
             'gsmooth until dataSink has finished sinking SVReg apply map outputs.'
    )

class GSmoothOutputSpec(TraitedSpec):
    smoothFile = File(desc='path/name of nifti file containing smooth vol data')


class GSmooth(BrainSuiteCommandLine):
    """
        GSmooth
        This program is a C++ compiled binary that applies volumetric smoothing on an input file.

    Examples
        --------

    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> GSmooth = brainsuite.GSmooth()
    >>> GSmooth.inputs.inFile = example_data('structural.nii')
    >>> results = GSmooth.run() #doctest: +SKIP
    """

    input_spec = GSmoothInputSpec
    output_spec = GSmoothOutputSpec
    _cmd = 'gsmooth'

    def _format_arg(self, name, spec, value):
        if name == 'dataSinkDelay':
            return spec.argstr % ''

        return super(GSmooth, self)._format_arg(name, spec, value)

    def _gen_filename(self, name):
        if name == 'smoothFile':
            return self.inputs.outFile
        return None

    def _list_outputs(self):
        return l_outputs(self)


class GenerateXlsInputSpec(CommandLineInputSpec):
    subjectFilePrefix = traits.Str(
        argstr='%s', mandatory=True,
        desc='Absolute path and filename prefix of the subject data'
    )
    dataSinkDelay = traits.List(
        str,
        argstr='%s',
        desc='Connect datasink out_file to dataSinkDelay to delay execution of '
             'generate_xls until dataSink has finished sinking ThicknessPVC outputs.'
    )


class GenerateXlsOutputSpec(TraitedSpec):
    roiwisestats = File(desc='path/name of ROIwise stats file.')


class GenerateXls(BrainSuiteCommandLine):
    input_spec = GenerateXlsInputSpec
    output_spec = GenerateXlsOutputSpec
    _cmd = 'generate_stats_xls.sh'

    def _gen_filename(self, name):
        return self.inputs.subjectFilePrefix

    def _list_outputs(self):
        return l_outputs(self)

    def _format_arg(self, name, spec, value):
        if name == 'subjectFilePrefix':
            return spec.argstr % os.path.expanduser(value)
        if name == 'dataSinkDelay':
            return spec.argstr % ''

        return super(GenerateXls, self)._format_arg(name, spec, value)


class VolsliceInputSpec(CommandLineInputSpec):
    inFile = File(argstr='-i %s', mandatory=True, desc='Input file.')
    outFile = File(argstr='-o %s', mandatory=True, desc='Output file.', genfile=True, hash_files=True)
    Overlay = File(argstr='-r %s', mandatory=False, desc='Overlay image file name.')
    OverlayAlpha = traits.Int(argstr='--alpha %d', mandatory=False, desc='Overlay alpha (0-255) [default: 128]')
    maskFile = File(argstr='-m %s', mandatory=False, desc='Mask filename.')
    colorMap = traits.Str(argstr='-c %s', mandatory=False,
                          desc='blue, blue, bone, cool, copper, green, grey, hot, hsv, '
                               'inverse, jet, pink, prism, red [default: grey]')
    labelFile = File(argstr='-l %s', mandatory=False, desc='Label filename.')
    labelAlpha = traits.Int(argstr='--labelalpha %d', mandatory=False, desc='Label alpha (0-255) [default: 64]')
    labelDesc = File(argstr='-x %s', mandatory=False, desc='Label description xml file.')
    scaling = traits.Float(argstr='-s %f', mandatory=False, desc='scaling value for image (0==autoscale) [default: 0]')
    view = traits.Int(argstr='--view %d', mandatory=False, desc='1=axial, 2=coronal, 3=sagittal [default: 1]')
    Slice = traits.Int(argstr='--slice %d', mandatory=False, desc='slice number (0-indexed, -1 uses center slice) '
                                                                  '[default: -1]')
    flip = traits.Bool(argstr='--flip', mandatory=False, desc='flip image U/D.')
    flop = traits.Bool(argstr='--flop', mandatory=False, desc='flip image L/R.')
    voxelspace = traits.Bool(argstr='--voxelspace',mandatory=False,
                             desc="Use voxel coordinates (don't rescale anisotropic)")
    dataSinkDelay = traits.List(
        str,
        argstr='%s',
        desc='Connect datasink outfile to dataSinkDelay to delay execution of '
             'qcState until dataSink has finished sinking volslice outputs.'
    )
    start = traits.Str(mandatory=False,
        # argstr='',
        desc='Triggers volslice to render QC thumbnail pngs.'
    )



class VolsliceOutputSpec(TraitedSpec):
    outFile = File(desc='Output file.')


class Volslice(BrainSuiteCommandLine):
    input_spec = VolsliceInputSpec
    output_spec = VolsliceOutputSpec
    _cmd = 'volslice'

    def _gen_filename(self, name):
        return self.inputs.outFile

    def _list_outputs(self):
        return l_outputs(self)

    def _format_arg(self, name, spec, value):
        # if name == 'start':
        #     return spec.argstr % os.path.expanduser(value)
        # elif name == 'inFile':
        #     return spec.argstr % os.path.expanduser(value)
        if name == 'dataSinkDelay':
            return spec.argstr % ''
        else:
            return spec.argstr % value
        # return super(Volslice, self)._format_arg(name, spec, value)


class RenderDfsInputSpec(CommandLineInputSpec):
    OutFile = File(argstr='-o %s', mandatory=True, desc='Output file. Must be a png.', genfile=True, hash_files=True)
    Ant = traits.Bool(argstr='--ant', mandatory=False, desc='coronal view (anterior)')
    Pos = traits.Bool(argstr='--pos', mandatory=False, desc='coronal view (posterior)')
    Sup = traits.Bool(argstr='--sup', mandatory=False, desc='axial view (superior)')
    Inf = traits.Bool(argstr='--inf', mandatory=False, desc='axial view (inferior)')
    Left = traits.Bool(argstr='--left', mandatory=False, desc='sagittal view (left)')
    Right = traits.Bool(argstr='--right', mandatory=False, desc='sagittal view (right)')
    BGcolor = traits.Str(argstr='--bg %s', mandatory=False, desc='background color (rgb) [default: 0 0 0]')
    Xwidth = traits.Int(argstr='-x %d', mandatory=False, desc='width in pixels [default: 512]')
    Ywidth = traits.Int(argstr='-y %d', mandatory=False, desc='height in pixels [default: 512]')
    Surfaces = traits.Str(argstr='-s %s', mandatory=False, desc='surface1 [... surfaceN]')
    SolidSurfaces = traits.Str(argstr='--solidcolor %s', mandatory=False,
                               desc='surfaceIndex1 [ ... surfaceIndexN] (render these surfaces in grey)')
    Zoom = traits.Float(argstr='--zoom %f', mandatory=False, desc='zoom factor [default: 1]')
    xRot = traits.Int(argstr='--xrot %d', mandatory=False, desc='x rotation angle [default: 0]')
    yRot = traits.Int(argstr='--yrot %d', mandatory=False, desc='y rotation angle [default: 0]')
    zRot = traits.Int(argstr='--zrot %d', mandatory=False, desc='z rotation angle [default: 0]')
    Position = traits.Int(argstr='-p %d %d %d', mandatory=False,
                          desc='position (if no-center is selected) [default: 0 0 0]')
    Grey = traits.Bool(argstr='--no-color', mandatory=False, desc='render surfaces in greyscale')
    NoCenter = traits.Bool(argstr='--nocenter', mandatory=False, desc='do not center based on first surface')
    KeepGoing = traits.Bool(argstr='-k', mandatory=False, desc='Keep going')
    NoColor = traits.Bool(argstr='--no-color', mandatory=False, desc='Render surfaces in greyscale')
    CenterVol = File(argstr='--vol %s', mandatory=False, desc='center based on volume')
    UseColors = traits.Str(argstr='--use-colors %s', mandatory=False, desc='r1 g1 b1 [ ... rN gN bN] (use these colors)')
    Surfbilateral = traits.List(mandatory=False, desc='dummy argument to print bilateral hemi')
    dataSinkDelay = traits.Any(
        str,
        argstr='',
        desc='Connect datasink outfile to dataSinkDelay to delay execution of '
             'qcState until dataSink has finished sinking dfsrender outputs.'
    )

class RenderDfsOutputSpec(TraitedSpec):
    outFile = File(desc='Output file. Must be a png.')


class RenderDfs(BrainSuiteCommandLine):
    input_spec = RenderDfsInputSpec
    output_spec = RenderDfsOutputSpec
    _cmd = 'renderdfs'

    def _gen_filename(self, name):
        return self.inputs.OutFile

    def _list_outputs(self):
        return l_outputs(self)

    def _format_arg(self, name, spec, value):
        if (name=='bilteral') or (name == 'Surfaces') or (name == 'SolidSurfaces') or (name == 'TransSurfaces') or (name == 'WireSurfaces'):
            return spec.argstr % os.path.expanduser(value)
        elif name == 'dataSinkDelay':
            return

        return super(RenderDfs, self)._format_arg(name, spec, value)


class QCStateInputSpec(CommandLineInputSpec):
    prefix = traits.Str(mandatory=True, argstr='%s', position=0, desc='Basename.')
    stagenum = traits.Int(mandatory=True, argstr='%d', position=1, desc='Stage number.')
    # stage = traits.Str(mandatory=True, argstr='%s', position=2, desc='Stage character/symbol of the state.')
    state = traits.Str(mandatory=True, argstr='%s', position=2, desc='String of all states.')
    Run = traits.Any(argstr='', mandatory=False, desc='dummy arg.')
    LaunchInput = traits.Any(argstr='', mandatory=False, desc='Waits for QC launch state.')

class QCStateOutputSpec(TraitedSpec):
    OutStateFile = File(desc='State file output.')

class QCState(BrainSuiteCommandLine):
    input_spec = QCStateInputSpec
    output_spec = QCStateOutputSpec
    _cmd = 'qcState.sh'

    def _gen_filename(self, name):
        if name == 'OutStateFile':
            return self.inputs.prefix + os.sep + 'stage-{0}.state'.format(self.inputs.stagenum)
        # return getFileName(self.inputs.filename, '.state')

    def _list_outputs(self):
        return l_outputs(self)

    def _format_arg(self, name, spec, value):
        if (name == 'Run') or (name == 'LaunchInput'):
            return #' %s %s %s ' % (self.inputs.prefix,self.inputs.stagenum,self.inputs.state)
        return spec.argstr % value


class makeMaskInputSpec(CommandLineInputSpec):
    fileNameAndROIs = traits.Str(mandatory=True, argstr='%s', position=0, desc='Input file name and ROI IDs.')
    Run = traits.Str(mandatory=False, position=1, desc='dummy arg.')

class makeMaskOutputSpec(TraitedSpec):
    OutFile = File(desc='Output mask file name.')

class makeMask(BrainSuiteCommandLine):
    input_spec = makeMaskInputSpec
    output_spec = makeMaskOutputSpec
    _cmd = 'makeMask.sh'

    def _gen_filename(self, name):
        if name == 'OutFile':
            return self.inputs.fileNameAndROIs.split(' ')[0].split('.')[0] + '.pvc.edge.mask.nii.gz'

    def _list_outputs(self):
        return l_outputs(self)

    def _format_arg(self, name, spec, value):
        if name == "Run":
            return super(makeMask, self)._format_arg(name, spec, value)
        return super(makeMask, self)._format_arg(name, spec, value)

class copyFileInputSpec(CommandLineInputSpec):
    inFile = traits.Str(mandatory=True, argstr='%s', position=0, desc='Input file name to be copied.')
    outFile = traits.Str(mandatory=True, argstr='%s', position=1, desc='Output copied file name.',
                         genfile=True, hash_files=True)
    Run = traits.Str(argstr='%s', position=2, desc='dummy arg.')

class copyFileOutputSpec(TraitedSpec):
    OutFile = File(desc='Copied file name.')

class copyFile(BrainSuiteCommandLine):
    input_spec = copyFileInputSpec
    output_spec = copyFileOutputSpec
    _cmd = 'cp'

    def _gen_filename(self, name):
        return self.inputs.outFile

    def _list_outputs(self):
        return l_outputs(self)

    def _format_arg(self, name, spec, value):
        if name == "Run":
            return super(copyFile, self)._format_arg(name, spec, value)
        return super(copyFile, self)._format_arg(name, spec, value)


## BFP module
class BFPInputSpec(CommandLineInputSpec):
    configini = traits.Str(mandatory=True, argstr='%s', position=0, desc='Configuration INI file.')
    t1file = traits.File(mandatory=True, argstr='%s', position=1, desc='T1-weighted image.')
    fmrifile = traits.File(mandatory=True, argstr='%s', position=2, desc='fMRI data.')
    studydir= traits.Str(mandatory=True, argstr='%s', position=3, desc='Output directory.')
    subjID = traits.Str(mandatory=True, argstr='%s', position=4, desc='Subject ID.')
    session = traits.Str(mandatory=True, argstr='%s', position=5, desc='Session name.')
    TR = traits.Int(mandatory=True, argstr='%d', position=6, desc='Repetition time in seconds.')
    dataSinkDelay = traits.Any(
        str,
        argstr='',
        desc='Connect datasink outfile to dataSinkDelay to delay execution of '
             'BFP until dataSink has finished sinking SVREG outputs.'
    )

class BFPOutputSpec(TraitedSpec):
    SSIMpng = File(desc='SSIM plot PNG.', hash_files=True)
    MCOpng = File(desc='MCO PNG.', hash_files=True)
    Func2T1 = File(desc='fMRI registration to T1w space output file.', hash_files=True)
    GOrdmat = File(desc='Grayordinate output file.', hash_files=True)
    GOrdFiltmat = File(desc='Filtered grayordinate output file.', hash_files=True)
    dummy = traits.Str(desc='dummy output')

class BFP(BrainSuiteCommandLine):
    input_spec = BFPInputSpec
    output_spec = BFPOutputSpec
    _cmd = 'bfp.sh'

    def _gen_filename(self, name):

        fileToSuffixMap = {
            'SSIMpng': '.mc.ssim.png',
            'MCOpng': '.mco.png',
            'Func2T1': '.example.func2t1.nii.gz',
            'GOrdmat': '.32k.GOrd.mat',
            'GOrdFiltmat': '.32k.GOrd.filt.mat'
        }

        if name in fileToSuffixMap:
            return os.path.join(self.inputs.studydir, self.inputs.subjID, 'func',
                                self.inputs.subjID+'_'+self.inputs.session+'_bold'+
                                fileToSuffixMap[name])

        if name == 'dummy':
            return ''
        return None
    def _list_outputs(self):
        return l_outputs(self)
    def _format_arg(self, name, spec, value):
        # if name == 'configini':
        #     return spec.argstr % os.path.expanduser(value)
        if name == 'configini':
            return super(BFP, self)._format_arg(name, spec, value)
        if name == 'dataSinkDelay':
            return #spec.argstr % ''
        return super(BFP, self)._format_arg(name, spec, value)


# used to generate file names for outputs
# removes pathway and extension of inputName, returns concatenation of:
# inputName and suffix
def getFileName(inputName, suffix):
    base_filename = os.path.basename(inputName)
    file_prefix = base_filename.split('.')[0]
    return os.path.join(os.path.dirname(inputName), file_prefix+suffix)
    # fullInput = os.path.basename(inputName)
    # dotRegex = regex.compile("[^.]+")
    # # extract between last slash and first period
    # inputNoExtension = dotRegex.findall(fullInput)[0]
    # return os.path.abspath(
    #     ''.join((inputNoExtension, suffix)))


def l_outputs(self):
    outputs = self.output_spec().get()
    for key in outputs:
        name = self._gen_filename(key)
        if name is not None:
            outputs[key] = name

    return outputs
