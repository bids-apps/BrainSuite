# BrainSuite BIDS-App
This is the BIDS-App version of BrainSuite18a (http://brainsuite.org/). This BIDS-App version of BrainSuite provides a portable, streamlined method of performing primary BrainSuite analysis workflows.

## Description
BrainSuite is an open-source collection of software for processing structural and diffusion MRI, with planned enhancements to support functional MRI.
These stages include:
* Extracting cortical surface models from T1-weighted (T1w) MRI ([CSE](http://brainsuite.org/processing/surfaceextraction/)).
* Performing surface-constrained volumetric registration ([SVReg](http://brainsuite.org/processing/svreg/)) to rpoduce consistent surface and colume reigstrations to a labeled atlas.
* Processing diffusion weighted imaging (DWI) to correct image distortion, co-registering the DWI to the T1w scan, and fitting diffusion models to the DWI data ([BDP](http://brainsuite.org/processing/diffusion/)).
* Group-level statistical analysis using BrainSuite Statistics Toolbox in R (bssr).

## Usage
### Data input requirements
This App requires at least one T1w image. If no corresponding DWI data is found, the App will only run CSE and SVReg on the T1w(s). If there are corresponding DWI data (DWI image data, bval file, and bvec file), the App will grab the nearest DWI data (i.e. within sub-ID/ directory or sub-ID/ses directory) and will perform CSE, SVReg, and BDP.

If there are unequal number of T1w data and DWI data, the App will process the T1w and DWI data in pairs until there are no matched pairs left. The pairs will be matched according to the run numbers (i.e. run-01).

* **Required**: T1w image (BIDS/NIFTI format).
* (Optional): DWI image (BIDS/NIFTI format).

### Pre-requisites
* Make sure the imaging data are formatted and organized with respect to the [BIDS standard](http://bids.neuroimaging.io/bids_spec1.1.0.pdf).
* If you have not yet installed Docker, install Docker from [here](https://docs.docker.com/install/).

### Command line arguments
```
usage: run.py [-h]
              [--participant_label PARTICIPANT_LABEL [PARTICIPANT_LABEL ...]]
              [--stages {CSE,SVREG,BDP} [{CSE,SVREG,BDP} ...]]
              [--atlas {BSA,BCI,USCBrain}] [--modelspec MODELSPEC]
              [--singleThread] [--cache CACHE] [-v]
              bids_dir output_dir {participant,group}

BrainSuite18a BIDS-App (T1w, dMRI)

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
  --stages {CSE,SVREG,BDP} [{CSE,SVREG,BDP} ...]
                        Processing stage to be run. Space delimited list.
  --atlas {BSA,BCI,USCBrain}
                        Atlas that is to be used for labeling in SVReg.
                        Default atlas: BCI-DNI. Options: BSA, BCI, USCBrain.
  --modelspec MODELSPEC
                        Optional. Only for group analysis level.Path to JSON
                        file that contains statistical modelspecifications.
  --singleThread        Turns on single-thread mode for SVReg.
  --cache CACHE         Nipype cache output folder
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
![Sample JSON](http://brainsuite.org/wp-content/uploads/2018/05/examplemodspecJSON-e1525727233202.png)

#### Explanation of odelspec.json fields ####
* **tsv** : Name of the TSV file containing data that is to be used for group analysis.
* **measure** : Imaging measure of interest. Options: cbm, tbm, roi, dbm.
* **test** : Model to be run. Options: anova, corr, ttest.
* **main_effect** : (Only for ANOVA) Main predictor variable. Must match the column header in the TSV file in the “tsv” field.
* **covariates** : (Only for ANOVA) Covariates. Must match the column header in the TSV file in the “tsv” field.
* **corr_var** : (Only for Correlation test) Variable for correlation test.
* **group_var** : (Only for Paired t-test) Group variable. ** Not implemented yet.
* **paired** : (Only for Paired t-test) Group variable. ** Not implemented yet.
* **smooth** : Smoothing level for cbm, tbm, and dbm.
* **mult_comp** : Multiple comparison correction method. Options: fdr, perm. Default is fdr. perm method is the t-max permutation test method.
* **roiid** : ROI ID for roi analysis.
* **hemi** : Hemisphere for cbm. Options: left, right.
* **maskfile** : Mask file for tbm and dbm.
* **atlas** : Atlas file. Default is the atlas that was used to run SVReg.
* **roimeas** : ROI measure of interest. Options: gmthickness, gmvolume.
* **dbmmeas** : Diffusion measure of interest. Options: FA, AD, MD, RD, GFA, ADC.
* **results** : Output folder path for results. The path has to be relative to the path inside the Docker container.

## Support
Questions about usage can be submitted to http://forums.brainsuite.org/.
Issues or suggestions can be directly submitted as an issue to this Github Repository.

## FYI
* BDP requires at least 6GB of memory. You may have to increase memory when you run the container.
* Turn on single thread mode (``` --singleThread ```) if your machine cannot support MATLAB's parpool.
* BDP estimates tensors, FRT ODF, and FRACT ODF.

## Acknowledgments ##
This project is supported by NIH Grant R01-NS074980.
