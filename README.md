# BrainSuite BIDS-App 
This is the BIDS-App version of BrainSuite18a (http://brainsuite.org/). This BIDS-App version of BrainSuite provides a portable, streamlined method of performing primary BrainSuite analysis workflows.

## Description
BrainSuite is an open-source collection of software for processing structural, diffusion, and functional MRI.
These stages include: 
* Extraction of cortical surface models from T1-weighted (T1w) MRI ([CSE](http://brainsuite.org/processing/surfaceextraction/)).
* Surface-constrained volumetric registration ([SVReg](http://brainsuite.org/processing/svreg/)) to produce atlas-labeled subject data.
* Processing of diffusion weighted imaging (DWI) to correct image distortion, co-registering the DWI to the T1w scan, and fitting diffusion models to the DWI data ([BDP](http://brainsuite.org/processing/diffusion/)).
* Processing of 4D fMRI datasets using a combination of tools from AFNI, FSL, BrainSuite and additional in-house tools developed for BrainSuite ([BFP](https://github.com/ajoshiusc/bfp)).
* Group-level statistical analysis of structural data using BrainSuite Statistics Toolbox in R ([bssr](http://brainsuite.org/bssr/)).
* Group-level statistical analysis of fMRI data using [BrainSync](https://github.com/ajoshiusc/bfp/tree/master/src/BrainSync), a tool that temporally aligns spatially registered fMRI datasets for direct timeseries comparisons between subjects.

## Usage
### Data input requirements
This App requires at least one T1w image. If no corresponding DWI data is found, the App will only run CSE and SVReg on the T1w(s). If there are corresponding DWI data (DWI image data, bval file, and bvec file), the App will grab the nearest DWI data (i.e. within sub-ID/ directory or sub-ID/ses directory) and will perform CSE, SVReg, and BDP. 

If there are unequal number of T1w data and DWI data, the App will process the T1w and DWI data in pairs until there are no matched pairs left. The pairs will be matched according to the run numbers (i.e. run-01). 

* **Required**: T1w image (BIDS/NIFTI format).
* (Optional): DWI image, fMRI image (BIDS/NIFTI format).

### Pre-requisites 
* Make sure the imaging data are formatted and organized with respect to the [BIDS standard](https://bids-specification.readthedocs.io/en/stable/).
* If you have not yet installed Docker, install Docker from [here](https://docs.docker.com/install/).

### Command line arguments
```
usage: run.py [-h]
              [--participant_label PARTICIPANT_LABEL [PARTICIPANT_LABEL ...]]
              [--stages {CSE,SVREG,BDP,BFP,ALL} [{CSE,SVREG,BDP,BFP,ALL} ...]]
              [--atlas {BSA,BCI,USCBrain}] [--analysistype {ANAT,FUNC,ALL}]
              [--modelspec MODELSPEC] [--preprocspec PREPROCSPEC]
              [--rmarkdown RMARKDOWN] [--singleThread] [--cache CACHE]
              [--TR TR] [--skipBSE] [-v]
              bids_dir output_dir {participant,group}

BrainSuite19b BIDS-App (T1w, dMRI, rs-fMRI)

positional arguments:
  bids_dir              The directory with the input dataset formatted
                        according to the BIDS standard.
  output_dir            The directory where the output files should be stored.
                        If you are running group level analysis this folder
                        should be prepopulated with the results of
                        theparticipant level analysis.
  {participant,group}   Level of the analysis that will be performed. Multiple
                        participant level analyses can be run independently
                        (in parallel) using the same output_dir. The group
                        analysis performs group statistical analysis.

optional arguments:
  -h, --help            show this help message and exit
  --participant_label PARTICIPANT_LABEL [PARTICIPANT_LABEL ...]
                        The label of the participant that should be analyzed.
                        The label corresponds to sub-<participant_label> from
                        the BIDS spec (so it does not include "sub-"). If this
                        parameter is not provided all subjects should be
                        analyzed. Multiple participants can be specified with
                        a space separated list.
  --stages {CSE,SVREG,BDP,BFP,ALL} [{CSE,SVREG,BDP,BFP,ALL} ...]
                        Processing stage to be run. Space delimited list.
                        Default is ALL
  --atlas {BSA,BCI,USCBrain}
                        Atlas that is to be used for labeling in SVReg.
                        Default atlas: BCI-DNI. Options: BSA, BCI, USCBrain.
  --analysistype {ANAT,FUNC,ALL}
                        Group analysis type: structural (T1 or DWI)or
                        functional (fMRI). Options: anat, func, all.
  --modelspec MODELSPEC
                        Optional. Only for group analysis level.Path to JSON
                        file that contains statistical modelspecifications.
  --preprocspec PREPROCSPEC
                        Optional. BrainSuite preprocessing parameters.Path to
                        JSON file that contains preprocessingspecifications.
  --rmarkdown RMARKDOWN
                        Optional. Executable Rmarkdown file that uses bssr
                        forgroup analysis stage.Path to R Markdown file that
                        contains bssr analysis commands.
  --singleThread        Turns on single-thread mode for SVReg.
  --cache CACHE         Nipype cache output folder
  --TR TR               Repetition time of MRI
  --skipBSE             Skips BSE stage when running CSE. Please make sure
                        there are sub-ID_T1w.mask.nii.gz files in the subject
                        folders.
  -v, --version         show program's version number and exit
```

### Participant level usage ###
To run it in participant level mode:
```bash
docker run -ti --rm \
  -v /path/to/local/bids/input/dataset/:/data \
  -v /path/to/local/output/:/output \
  bids/brainsuite \
  /data /output participant --participant_label 01
```
Where 01 is the "sub-01". User can supply multiple participant labels by listing them delimited by space (i.e. --participant_label 01 02). If ``` --stages ```stages is not specified, the default is to run all stages. 

User can remove ``` --participant_label <ids-list> ``` argument to have all subjects processed. 
All sessions will be processed. The output files will be located in the output folder specified.

### Group level usage ###

To run it in group level mode:
```bash
docker run -ti --rm \
  -v /path/to/local/bids/input/dataset/:/data \
  -v /path/to/local/output/:/output \
  bids/brainsuite \
  /data /output group --modelspec modelspec.json
```

#### Pre-requisite ####
* A TSV file containing data that is to be used for group analysis. The file must contain a column with a column header “**participant_id**” with the subject ID listed. This file MUST be in the output folder containing the outputs of the processed images. An example file can be downloaded [here](http://brainsuite.org/wp-content/uploads/2018/05/participants.tsv).
* A JSON file containing the specifications for group level analysis. Details on the fields are listed below.
Sample JSON file is provided with the source code (BrainSuite/sample_modelspec.json)

#### Explanation of modelspec.json fields ####
* **tsv_fname** : Name of the TSV file containing data that is to be used for group analysis.
* **out_dir** : Output folder path for results. The path has to be relative to the path inside the Docker container.

##### Structural data analysis #####
* **measure** : Imaging measure of interest. Options: cbm, tbm, roi, dbm.
* **test** : Model to be run. Options: anova, corr, ttest.
* **main_effect** : (Only for ANOVA) Main predictor variable. Must match the column header in the TSV file in the “tsv” field.
* **covariates** : (Only for ANOVA) Covariates. Must match the column header in the TSV file in the “tsv” field.
* **corr_var** : (Only for Correlation test) Variable for correlation test.
* **group_var** : (Only for Paired t-test) Group variable. ** Not implemented yet.
* **paired** : (Only for Paired t-test) Group variable. ** Not implemented yet.
* **smooth** : Smoothing level for cbm, tbm, and dbm.
* **mult_comp** : Multiple comparison correction method. Options: fdr, perm. Default is fdr. perm method is the t-max permutation test method.
* **niter** : Number of iterations for the permutation method.
* **pvalue** : Method for computing p-values. Options: parametric, perm. The parametric method is the classical p-value method. The permutation method refers to the Freedman-Lane method.
* **roiid** : ROI ID for roi analysis.
* **hemi** : Hemisphere for cbm. Options: left, right.
* **maskfile** : Mask file for tbm and dbm.
* **atlas** : Atlas file. Default is the atlas that was used to run SVReg.
* **roimeas** : ROI measure of interest. Options: gmthickness, gmvolume.
* **dbmmeas** : Diffusion measure of interest. Options: FA, AD, MD, RD, GFA, ADC.

##### Functional data analysis #####
* **file_ext** : Input file extension. BFP output in grayordinate.
* **lentime** : Number of timepoints.
* **matchT** : If subjects have less than 'lentime', will add zero values to match number of timepoints.
* **stat_test** : Testing options: atlas-linear, atlas-group, pairwise-linear, pairwise-group.
* **pw_pairs** : Number of random pairs to measure. (ignore if running atlas-linear).
* **pw_fdr** : FDR correction(True) or maxT permutations (False). (ignore if running atlas-linear).
* **pw_perm** : Number of permutations. Used only if maxT permutations indicated. (ignore if running atlas-linear).
* **outname** : File subnames for result outputs.
* **sig_alpha ** : P-value significance level (alpha).
* **smooth_iter** : Level of smoothing applied on brain surface outputs.
* **save_surfaces** : True, to save surface files.
* **save_figures** : True, to save PNG figure files.
* **atlas_groupsync** : False if you'd like to create reference atlas by identifying one representative subject.
* **atlas_fname** : Filename of user-defined atlas. Variable should be called atlas_data. Leave empty if no user-defined atlas should be used.
* **test_all** : False if subjects used for atlas creation are excluded from testing your hypothesis.
* **colvar_main** : For linear regression or group testing: the main effect you are testing.
* **colvar_reg1** : For group comparisons. assign all rows with zero values if running linear regression. Control up to 2 variables by linearly regressing out the effect. If you only have less than 2 variable you would like to regression out, you can create and assign a dummy column(s) with zero values for all rows.
* **colvar_reg2** : (See above).
* **colvar_exclude** : Assign a value of (1) for subjects you would like to exclude from the study. assign zero values for all rows if all subjects are to be included.
* **colvar_atlas** : Assign a value of (1) for subjects that would be used to create a representative functional atlas; (0) otherwise.

#### To modify pre-processing parameters (optional) ####
While running participant level mode, specify a preprocspec.json file:
```bash
docker run -ti --rm \
  -v /path/to/local/bids/input/dataset/:/data \
  -v /path/to/local/output/:/output \
  bids/brainsuite \
  /data /output participant --participant_label 01 --preprocspec /output/preprocspec.json
```
Sample JSON file is provided with the source code (BrainSuite/sample_preprocspec.json)

#### Explanation of preprocspec.json fields ####

To turn on an option, please use (1), to turn off (0).

* **cacheFolder** : Cache folder for nipype.

##### Brain Surface Extractor (BSE) #####
* **autoParameters** : Automated selection of optimal parameters for skull-stripping.
* **diffusionIterations** : (Typical range: 0–6). Number of times the diffusion filter is applied to the image. (Field will be ignored if autoParameters is 1 (turned on)).
* **diffusionConstant** : (Typical range: 5–35). Edge diffusion constant controls the height of the edges that are retained.
* **edgeDetectionConstant** : (Typical range: 0.5–1.0). During the edge detection step, the scale parameter influences how wide an edge must be to be identified.
* **skipBSE** : 1 to skip BSE (skull stripping) and use the pre-existing mask file in the output folder.

##### Bias Field Correction (BFC) #####
* **iterativeMode** : Iterative mode will run multiple passes of bias field correction using a range of settings to correct for severe artifacts.

##### Tissue classification (PVC) #####
* **spatialPrior** : Spatial prior can be adjusted to reduce its influence, which can be useful if the image has low signal-to-noise.

##### Cerebrum labeling #####
* **costFunction** : Possible choices are: standard deviation, least squares, and least squares with intensity rescaling.
* **useCentroids** : Use centroids of data to initialize position.
* **linearConvergence** : Sets the threshold for the change in the cost function used to determine if it converged.
* **warpConvergence** : Threshold of the change in the cost function before the scan is considered aligned with the atlas.
* **warpLevel** : (Ranges from 2 to 8) The degree of the polynomial model used for the transformation.

##### Cortex mask selection #####
* **tissueFractionThreshold** : Minimum percentage of white matter in a voxel needed for it to be included in the mask, in decimal form (e.g. 50% white matter = 0.5).

##### SVReg #####
* **atlas** : Atlas that is to be used for labeling in SVReg. Options: BSA,BCI,USCBrain. Information on the atlases are located here: http://brainsuite.org/atlases/.
* **singleThread** : 1 to turn off multithreading in Matlab parpool.

##### BrainSuite Diffusion Pipeline (BDP) #####
* **skipDistortionCorr** : Skip distortion correction for DWI data.
* **phaseEncodingDirection** : Phase encoding direction of DWI data.
* **echoSpacing** : Echo spacing of of DWI data.
* **fieldmapCorrection** : Specify fieldmap file if you would like to use field map correction.
* **estimateODF_3DShore** : Estimates ODFs using the 3DSHORE basis representation.
* **diffusion_time_ms** : Sets the diffusion time parameter required for estimating ERFO, 3DSHORE and GQI ODFs.
* **estimateODF_GQI** : Estimates ODFs using the GQI method.

##### Post-processing #####
* **smoothSurf** : Smoothing level for surface output data.
* **smoothVol** : Smoothing level for volumetric output data.

##### BrainSuite Functional Pipeline (BFP) #####
* **task-name** : Task name (should be the name after 'task' in the file name).
* **TR** : Repetition time.
* **EnabletNLMPdfFiltering** : Enable tNLMPdf(GPDF) Filtering. This step can take upto 30 min per scan.
* **fpr** : False positive rate regarding the null (noise) distribution.
* **FSLOUTPUTTYPE** : FSL output type.
* **FWHM** : Smoothing level; FWHM is mm (not in voxels!).
* **HIGHPASS** : Band pass filtering: High pass cutoff frequencies in Hz.
* **LOWPASS** : Band pass filtering: High pass cutoff frequencies in Hz.
* **memory** : RAM in FB on your system.
* **EnableShapeMeasures** : Enable SCT shape measure computation (cortical thickness using anisotropic Laplacian, shape index and curvatures). This step can take up to 1 hr per scan.
* **T1SpaceProcessing** : 1: T1 native space will be used for T1 preprocessing. 0: T1 will resample images to 1mm isotropic for preprocessing.
* **FSLRigid** : 1: Use FSL's rigid registration during processing, 0: BrainSuite's BDP rigid registration.
* **BPoption** : 1: 3dBandpass (updated function with quadratic detrending) or 0: 3dFourier + linear detrending. Detail found in AFNI documentation https://afni.nimh.nih.gov/pub/dist/doc/program_help/.
* **RunDetrend** : Enable detrending.
* **RunNSR** : Enable Nuisance Signal Regression.
* **scbPath** : SCB file is used by tNLM filtering. Set this path somewhere there is a lot of space.
* **T1mask** : T1 mask will be used to threshold fMRI data. May be useful for data with high signal dropout.


## Support
Questions about usage can be submitted to http://forums.brainsuite.org/. 
Issues or suggestions can be directly submitted as an issue to this Github Repository.


## Acknowledgments ##
This project is supported by NIH Grant R01-NS074980.
