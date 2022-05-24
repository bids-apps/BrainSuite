# Modifying participant-level pre-processing parameters (optional) #
Users can run the participant-level workflow with custom parameters by including a preprocessing configuration file. Prior to running the participant-level workflows, modify the parameters in a preprocspec.json file. A sample JSON file is provided with the source code ([BrainSuite/sample_preprocspec.json](https://bitbucket.org/brainsuite/brainsuite-bids-app/src/master/sample_preprocspec.json))

Then run participant-level mode and specify the preprocspec.json file:

```bash
docker run -ti --rm \
  -v /path/to/local/bids/input/dataset/:/data \
  -v /path/to/local/output/:/output \
  bids/brainsuite \
  /data /output participant --participant_label 01 --preprocspec /output/preprocspec.json
```


## Explanation of preprocspec.json fields ##
This optional JSON file defines objects named Anatomical, Diffusion, PostProc, and Functional that can be used to specify parameters for each of those components. 
For parameters whose options are Boolean values, 1 (True) and 0 (False) are used, e.g., 1 enables an option and 0 disables it.

### Global Settings ###
* **cacheFolder** : Specifies the location of the cache folder for Nipype. The default location for the cache folder is the output directory.

### Anatomical Pipeline Settings ###

#### Skull-stripping (bse) ####
* **autoParameters** : Enables automated selection of optimal parameters for skull-stripping/Brain Surface Extractor (BSE). Options: 0, 1. Default: 1 (enabled).
* **diffusionIterations** : Specifies the number of times the anisotropic diffusion filter is applied to the image during BSE. This field will be ignored if autoParameters is 1. Typical range: \[0 . . . 6]. Default: 3.
* **diffusionConstant** : Specifies the anisotropic diffusion constant, which controls the height of the edges that are retained during anisotropic diffusion filtering. This field will be ignored if autoParameters is 1. Typical range: \[5 . . . 35]. Default: 25.
* **edgeDetectionConstant** : specifies the edge detection constant, σ. During the edge detection step in BSE, σ influences how wide an edge must be to be identified. Typical range: (0.5 − 1.0). Default: 0.64
* **skipBSE** : If enabled (1), skull stripping (BSE) is skipped and a custom mask is used (e.g., if manual edits to a brain mask were necessary). The custom mask must be copied to the output folder prior to running BAP. Options: {0,1}. Default: 0 (disabled).

#### Bias Field Correction (bfc) #####
* **iterativeMode** : If iterative mode is enabled, the bias field correction (BFC) program will run multiple passes using a range of settings to correct for severe artifacts. Options: {0,1}. Default: 0.

#### Tissue classification (pvc) ####
* **spatialPrior** : Controls the weighting of the spatial prior used during tissue classification stage. Reducing this value can be useful if an image has low signal-to-noise. Default: 0.1.

#### Cerebrum labeling (cerebro) ####
* **costFunction** : The cost function used by AIR’s alignlinear during the initial linear registration to the atlas for cerebrum labeling. Possible choices are: standard deviation of the ratio image (0), least squares (1), and least squares with intensity rescaling (2). Options: {0,1,2}. Default: 2.
* **useCentroids** : If enabled, the cerebrum labeling program will initialize the registration process using the centroids of the subject image and the atlas image. Options: {0,1}. Default: 0.
* **linearConvergence** : Sets the threshold used by AIR’s alignlinear during cerebrum labeling to determine if the linear registration has converged. Default: 0.1.
* **warpConvergence** : Sets the threshold used by AIR’s align_warp during cerebrum labeling to determine if the nonlinear registration has converged. Default: 100.
* **warpLevel** : Sets the degree of the polynomial model used for the transformation used by AIR’s align_warp during cerebrum labeling. Typical Range: (2 − 8). Default: 5

#### White Matter Mask Generation (cortex) ####
* **tissueFractionThreshold** : Minimum percentage of white matter in a voxel needed for it to be included in the mask, in decimal form (e.g., 50% white matter) during initial cortical mask generation. Range: (0 − 100). Default: 50.0

#### Registration and Labeling (svreg) ####
* **atlas** : Specifies the atlas used for registration and labeling (see [here](http://brainsuite.org/atlases/) for details on the atlases). Options: BSA, BCI-DNI, USCBrain. 1 Default: BCI-DNI.
* **singleThread** : If enabled, SVReg runs in single-threaded mode by disabling multithreading in MATLAB’s parpool. This can be helpful if errors related to MATLAB parpool occur on compute nodes. Options: {0,1}. Default: 0

### BrainSuite Diffusion Pipeline (BDP) Settings ###
* **skipDistortionCorr** : If enabled, BDP skips distortion correction completely and performs only a rigid registration of the diffusion and T1-weighted images. This can be useful when the input diffusion images do not have any distortion or they have already been corrected for distortion. Options: {0,1}. Default: 0.
* **phaseEncodingDirection** : Sets the phase encoding direction of the DWI data, which is the dominant direction of distortion in the images. This information is used to constrain the distortion correction along the specified direction. Directions are represented by any one of x, x-, y, y-, z or z-. x direction increases towards the right side of the subject, while x- increases towards the left side of the subject. Similarly, y and y- are along the anterior-posterior direction of the subject, and z and z- are along the inferior-superior direction. When this field is not specified, BDP uses y as the default phase-encoding direction. Options: {x,x-,y,y-,z,z-}. Default: y.
* **echoSpacing** : Sets the echo spacing in units of seconds, which is used during fieldmap-based distortion correction. (Example: For an echo spacing of 0.36ms, use echo-spacing=0.00036). This value is required when using fieldmapCorrection.
* **fieldmapCorrection** : Use an acquired fieldmap for distortion correction. The parameter specifies the path to the field map file to use.
* **estimateODF_3DShore** : If enabled, estimates ODFs using the 3D-SHORE (Özarslan et al., 2013) basis representation. Options: {0,1}. Default: 0.
* **diffusion_time_ms** : Sets the diffusion time parameter (in milliseconds). This parameter is required for estimating ERFO, 3D-SHORE and GQI ODFs.
* **estimateODF_GQI** : Estimates ODFs using the GQI method (Yeh et al., 2010). Options: {0,1}. Default: 0.
* **sigma_GQI** : Sets the GQI adjustable factor, required for calculating diffusion sampling length. Typical range: \[1 . . . 1.3]. Default: 1.25.
* **estimateODF_ERFO** : If enabled, estimates ODFs using the ERFO method. (Varadarajan & Haldar, 2018). Options: {0,1}. Default: 0.
* **ERFO_SNR** : Sets the SNR of the acquired data, required for estimating ERFO ODFs. Default: 35.

### Smoothing Parameters Settings ###
* **smoothSurf** : Specifies the kernel size (in mm) used for smoothing the surface output data from BAP. Typical range: (2 − 5). Default: 2.
* **smoothVol** : Specifies the kernel size (in mm) used for smoothing the volumetric output data from BAP and BDP. Typical range: (2 − 6). Default: 3.

### BrainSuite Functional Pipeline (BFP) Settings ###
* **task-name** : The names of the tasks to be processed in list form using square brackets, e.g., \[restingstate, emomatching]. The task names should correspond to the task names specified in the input fMRI filenames after the task- delimiter. For example, in the fMRI file sub-0001_task-restingstate_bold.nii.gz, the task name would be ‘restingstate’.
* **TR** : Repetition time (in seconds) of the fMRI data.
* **EnabletNLMPdfFiltering** : If enabled, BFP will apply tNLMPdf (GPDF) filtering. This step can take up to 30 minutes per scan. Options: {0,1}. Default: 1.
* **fpr** : False positive rate regarding the null (noise) distribution. This parameter is used for global non-local means filtering (GPDF) for fMRI denoising. Default: 0.001
* **FSLOUTPUTTYPE** : Specifies the format that FSL uses to save its outputs. 2 Default: NIFTI_GZ
* **FWHM** : Full-width-half-maximum value, in mm, used for spatial smoothing. Default: 6
* **HIGHPASS** : Value for the high-pass cutoff frequency, in Hz, used for bandpass filtering. Default: 0.005
* **LOWPASS** : Value for the low-pass cutoff frequency, in Hz, used for bandpass filtering. Default: 0.1
* **MultiThreading** : If enabled, uses parallel processing for transforming fMRI data onto the grayordinate system and GPDF non local means filtering. If disabled, parallel processing is not used. {0,1}. Default: 1
* **memory** : Specifies the amount of RAM (in gigabytes) available for running for transforming fMRI data onto grayordinate
* **EnableShapeMeasures** : Enable SCT shape measure computation (cortical thickness using anisotropic Laplacian, shape index and curvatures). This step can take up to 1 hr per scan.
* **T1SpaceProcessing** : 1: T1 native space will be used for T1 preprocessing. 0: T1 will resample images to 1mm isotropic for preprocessing.
* **FSLRigid** : If enabled, BFP uses FSL’s rigid registration (FLIRT) during processing. If not enabled, BFP uses BrainSuite’s BDP affine registration. FLIRT is run with 6 degrees of freedom, trilinear interpolation, and the correlation ratio cost function (Jenkinson et al., 2002). BrainSuite’s affine registration tool is set to run with 6 degrees of freedom, linear interpolation, and the INVERSION cost function, which is optimized to align the inverted contrasts of T1W and fMRI images (Bhushan et al., 2015). Options: {0,1}. Default: 0
* **SimRef** : Specifies the type of reference volume used for coregistration and motion correction. If enabled, SimRef will be used, which calculates the pair-wise structural similarity index (SSIM) between every tenth time point and all other time points (Wang et al., 2004; Hore & Ziou, 2010). The time point with the highest mean SSIM is chosen as the reference image. If not enabled, all volumes are averaged together to create a mean image. {0,1}. Default: 1
* **BPoption** : If enabled, BFP applies 3dBandpass (updated function with quadratic detrending). If not enabled, BFP applies 3dFourier and linear detrending. Details are found in the AFNI documentation 3 . Options: {0,1}. Default: 1
* **RunDetrend** : Enables detrending. Options: {0,1}. Default: 1
* **RunNSR** : Enables nuisance signal regression. Options: {0,1}. Default: 1
* **scbPath** : SCB file is used by tNLM filtering. Set this path somewhere there is a lot of space.
* **T1mask** : If enabled, BFP uses the T1w mask to threshold fMRI data, which may be useful for data with high signal dropout. Options: {0,1}. Default: 1
* **epit1corr** : If enabled, BFP performs distortion correction using constrained non-linear registration between the nonuniformity-corrected T1w-image and the reference fMRI image. This is useful for data in cases where a B0 field map is not available. Options: {0,1}. Default: 1
* **epit1corr_mask** : Specifies the EPI masking method used by BFP during EPI distortion correction. 0: use T1w-based mask; 1: use BDP liberal; 2: use BDP aggressive; 3: use AFNI 3dAutomask plus two-voxel dilation. Options: {0,1,2,3}. Default: 2
* **epit1corr_rigidsim** : Specifies the cost function(s) used by BFP during EPI distortion correction. Available methods are INVERSION (inversion), INVERSION followed by normalized mutual-information based refinement (Bhushan et al., 2015) (bdp), mutual information (mi), correlation ratio (cr), and squared difference (sd). Options: {bdp, inversion, mi, cr, sd}. Default: mi
* **epit1corr_bias** : If enabled, BFP performs bias field correction on the distortion-corrected data. Options: {0,1}. Default: 1
* **epit1corr_numthreads** : Specifies the number of threads used for T1w-based distortion correction.
