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
