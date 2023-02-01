# BrainSuite BIDS App 
## Overview
The BrainSuite BIDS App provides a portable, streamlined method for performing BrainSuite (http://brainsuite.org) workflows to processing and analyze anatomical, diffusion, and functional MRI data. This release of BrainSuite BIDS-App is based on [version 21a of BrainSuite](http://brainsuite.org/brainsuite21a).
The BrainSuite BIDS-App implements three major BrainSuite pipelines for subject-level analysis, as well as corresponding group-level analysis functionality.

### Subject-Level Analysis
The BrainSuite Anatomical Pipeline (BAP) processes T1-weighted (T1w) MRI to generate brain surfaces and volumes that are consistently registered and labeled according to a reference anatomical atlas. The major stages in BAP include:

* Cortical surface extraction ([CSE](http://brainsuite.org/processing/surfaceextraction/)).
* Cortical thickness estimation based on partial volume estimates and the anisotropic diffusion equation ().
* Surface-constrained volumetric registration ([SVReg](http://brainsuite.org/processing/svreg/)) to generate a mapping to a labeled reference atlas and label the cortical surface and brain volume.
* Mapping of cortical thickness estimates to the atlas space
* Computation of subject-level statistics (e.g., mean GM volume within ROIs, cortical thickness within surface ROIs)

The BrainSuite Diffusion Pipeline ([BDP](http://brainsuite.org/processing/diffusion/)) performs several steps to process diffusion MRI. These include:

* Processing of diffusion weighted imaging (DWI) to correct image distortion (based on either field maps or nonlinear registration to a corresponding T1-weighted MRI).
* Coregistration of the DWI to the T1w scan.
* Fitting of diffusion tensor models to the DWI data.
* Fitting of orientation distribution functions to the DWI data (using FRT, FRACT, GQI, 3D-SHORE, or ERFO as appropriate).
* Computation of diffusion indices (FA, MD, AxD, RD, GFA).

The BrainSuite Functional Pipeline ([BFP](http://brainsuite.org/bfp/)) processes resting-state and task-based fMRI data.

* BFP processes 4D fMRI datasets using a combination of tools from AFNI, FSL, BrainSuite and additional in-house tools developed for BrainSuite.
* Performs motion correction and outlier detection.
* Registers the fMRI data to the corresponding T1w anatomical data.
* Generates a representation of the fMRI data in grayordinate space in preparation for group-level analysis.

### Group-level Statistical Analysis
* Group-level statistical analysis of structural data is performed using the BrainSuite Statistics Toolbox in R ([bssr](http://brainsuite.org/bssr/)). Bssr supports the following analyses:
    * tensor based morphometry (TBM) analysis of voxel-wise magnitudes of the 3D deformation fields of MRI images registered to the atlas
    * cortical surface analysis of the vertex-wise thickness in the atlas space
    * diffusion parameter maps analysis (e.g., fractional anisotropy, mean diffusivity, radial diffusivity)
    * region of interest (ROI)-based analysis of average gray matter thickness, surface area, and gray matter volume within cortical ROIs
* Group-level statistical analysis of fMRI data (functional connectivity) is performed using [BrainSync](https://github.com/ajoshiusc/bfp/tree/master/src/BrainSync), a tool that temporally aligns spatially registered fMRI datasets for direct timeseries comparisons between subjects.
    * atlas-based linear modeling using a reference dataset created from multiple input datasets.
    * atlas-free pairwise testing of all pairs of subjects is performed and used as test statistics for regression or group difference studies.

### BrainSuite Dashboard
* The Quality Control (QC) component of the BrainSuite BIDS App generates snapshots of key stages in the participant-level workflows for quick visualization and assessment.
* The BrainSuite Dashboard provides a browser-based interface for visualizing the QC outputs in real-time while a set of BrainSuite BIDS App instances are running.


# Usage
### Data input requirements
The BrainSuite BIDS App requires at least one T1w image. If no corresponding DWI data or fMRI are found, the BrainSuite BIDS App will only run CSE and SVReg on the T1w(s). 

* **Required**: T1w NIFTI image (BIDS format).
* (Optional): DWI NIFTI image, fMRI NIFTI image (BIDS format).

### Prerequisites
* Imaging data must be formatted and organized according to the [BIDS standard](https://bids-specification.readthedocs.io/en/stable/).
* If you have not yet installed Docker, install Docker from [here](https://docs.docker.com/install/).
* (Optional but may be required for multi-user computers). Install [Singularity](https://sylabs.io/guides/3.5/user-guide/quick_start.html). This will allow you to run the Singularity version of the BIDS-App. Then, convert the Docker image to Singularity image:
```
docker run -v /var/run/docker.sock:/var/run/docker.sock \
-v /tmp/test:/output \
--privileged -t --rm \
quay.io/singularity/docker2singularity \
yeunkim/brainsuitebidsapp:stable
```

### Command line arguments
```bash
usage: run.py [-h]
              [--stages {CSE,SVREG,BDP,BFP,QC,DASHBOARD,ALL} [{CSE,SVREG,BDP,BFP,QC,DASHBOARD,ALL} ...]]
              [--preprocspec PREPROCSPEC]
              [--participant_label PARTICIPANT_LABEL [PARTICIPANT_LABEL ...]]
              [--skipBSE] [--atlas {BSA,BCI-DNI,USCBrain}] [--singleThread]
              [--TR TR] [--fmri_task_name FMRI_TASK_NAME [FMRI_TASK_NAME ...]]
              [--ignore_suffix IGNORE_SUFFIX] [--QCdir QCDIR]
              [--QCsubjList QCSUBJLIST] [--localWebserver] [--port PORT]
              [--bindLocalHostOnly] [--modelspec MODELSPEC]
              [--analysistype {STRUCT,FUNC,ALL}] [--rmarkdown RMARKDOWN]
              [--ignoreSubjectConsistency] [--bidsconfig [BIDSCONFIG]]
              [--cache CACHE] [--ncpus NCPUS] [--maxmem MAXMEM] [-v]
              bids_dir output_dir {participant,group}

BrainSuite21a BIDS-App (T1w, dMRI, rs-fMRI). Copyright (C) 2022 The Regents of
the University of California Dept. of Neurology, David Geffen School of
Medicine, UCLA.

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
  --stages {CSE,SVREG,BDP,BFP,QC,DASHBOARD,ALL} [{CSE,SVREG,BDP,BFP,QC,DASHBOARD,ALL} ...]
                        Participant-level processing stage to be run. Space
                        delimited list. Default is ALL which does not include
                        DASHBOARD. CSE runs Cortical Surface Extractor. SVREG
                        runs Surface-constrained Volumetric registration. BDP
                        runs BrainSuite Diffusion Pipeline. BFP runs
                        BrainSuite Functional Pipeline. QC runs BrainSuite QC
                        and generates status codes and snapshots. DASHBOARD
                        runs the real-time monitoring that is required for
                        BrainSuite Dashboard to update real-time.
  --preprocspec PREPROCSPEC
                        Optional. BrainSuite preprocessing parameters.Path to
                        JSON file that contains preprocessing specifications.
  --cache CACHE         Nipype cache output folder.
  --ncpus NCPUS         Number of cpus allocated for running subject-level
                        processing.
  --maxmem MAXMEM       Maximum memory (in GB) that can be used at once.
  -v, --version         show program's version number and exit

Options for selectively running specific datasets:
  --participant_label PARTICIPANT_LABEL [PARTICIPANT_LABEL ...]
                        The label of the participant that should be analyzed.
                        The label corresponds to sub-<participant_label> from
                        the BIDS spec (so it does not include "sub-"). If this
                        parameter is not provided all subjects should be
                        analyzed. Multiple participants can be specified with
                        a space separated list.

Command line arguments for BrainSuite Anatomical Pipeline (BAP). For more parameter options, please edit the preprocspecs.json file:
  --skipBSE             Skips BSE stage when running CSE. Please make sure
                        there are sub-ID_T1w.mask.nii.gz files in the subject
                        folders.
  --atlas {BSA,BCI-DNI,USCBrain}
                        Atlas that is to be used for labeling in SVReg.
                        Default atlas: BCI-DNI. Options: BSA, BCI-DNI,
                        USCBrain.
  --singleThread        Turns on single-thread mode for SVReg.This option can
                        be useful when machines run into issues with the
                        parallel processing tool from Matlab (Parpool).

Command line arguments for BrainSuite Functional Pipeline (BFP). For more parameter options, please edit the preprocspecs.json file:
  --TR TR               Repetition time of MRI (in seconds).
  --fmri_task_name FMRI_TASK_NAME [FMRI_TASK_NAME ...]
                        fMRI task name to be processed during BFP. The name
                        should only containthe contents after "task-". E.g.,
                        restingstate.
  --ignore_suffix IGNORE_SUFFIX
                        Optional. Users can define which suffix to ignore in
                        the output folder. E.g., if input T1w is sub-01_ses-
                        A_acq-highres_run-01_T1w.nii.gz,and user would like to
                        ignore the "acq-highres" suffix portion, then user can
                        type "--ignore_suffix acq", which will render
                        sub-01_ses-A_run-01 output folders.

Options for BrainSuite QC and Dashboard:
  --QCdir QCDIR         Designate directory for QC Dashboard.
  --QCsubjList QCSUBJLIST
                        For QC purposes, optional subject list (txt format,
                        individual subject ID separated by new lines; subject
                        ID without "sub-" is required (i.e. 001). This is
                        helpfulin displaying only the thumbnails of the queued
                        subjects when running on clusters/compute nodes.
  --localWebserver      Launch local webserver for QC.
  --port PORT           Port number for QC webserver.
  --bindLocalHostOnly   When running local web server through this app, the
                        server binds to all of the IPs on the machine. If you
                        would like to only bind to the local host, please use
                        this flag.

Arguments and options for group-level stage. --modelspec is required for groupmode:
  --modelspec MODELSPEC
                        Optional. Only for group analysis level.Path to JSON
                        file that contains statistical model specifications.
  --analysistype {STRUCT,FUNC,ALL}
                        Group analysis type: structural (T1 or DWI)or
                        functional (fMRI). Options: STRUCT, FUNC, ALL.
  --rmarkdown RMARKDOWN
                        Optional. Executable Rmarkdown file that uses bssr
                        forgroup analysis stage. If this argument is
                        specified, BrainSuite BIDS-App will run this Rmarkdown
                        instead of using the content found in
                        modelspec.json.Path to R Markdown file that contains
                        bssr analysis commands.

Options for bids-validator:
  --ignoreSubjectConsistency
                        Reduces down the BIDS validator log and the associated
                        memory needs. This is often helpful forlarge datasets.
  --bidsconfig [BIDSCONFIG]
                        Configuration of the severity of errors for BIDS
                        validator. If no path is specified, a default path of
                        .bids-validator-config.json(relative to the input bids
                        directory) file is used

```
### Participant-level usage ###
To run it in participant level mode:
```bash
docker run -ti --rm \
  -v /path/to/local/bids/input/dataset/:/data \
  -v /path/to/local/output/:/output \
  bids/brainsuite \
  /data /output participant --participant_label 01
```
Where 01 is the "sub-01". User can supply multiple participant labels by listing them delimited by space (i.e. --participant_label 01 02). If ``` --stages ```stages is not specified, the default is to run all stages, which includes CSE, SVReg, BDP, BFP, and QC.

User can remove ``` --participant_label <ids-list> ``` argument to have all subjects processed. 
All sessions will be processed. The output files will be located in the output folder specified.

For the functional pipeline, you will need to define the TR (repetition time in seconds for the fMRI data) using ```--TR``` command. If this is not called, then the default value of 2 will be used. 

If you would like to **modify parameters** for the participant-level run, you can do so by modifying the parameters in a preprocspecs.json file. [Full instructions and details are written here](preprocspec_details.md).

### QC and BrainSuite Dashboard usage ###
Adding "QC" to the stages (```--stages QC```) generates snapshots of key stages in the participant-level workflow. QC is included in the participant-level workflow as a default.

To run QC and BrainSuite Dashboard along with your processing for real-time updates, you will need to launch a separate instance of the BrainSuite BIDS App image. 


### Running real-time QC and BrainSuite Dashboard without a web server ###
If your institution does not have a running web server, you can launch a local web server using BrainSuite BIDS App by adding the flag ```--localWebserver```. 
You will also need to expose a port to the image; for example:

```bash
docker run -ti --rm \
  -p 8080:8080
  -v /path/to/local/bids/input/dataset/:/data \
  -v /path/to/local/output/:/output \
  bids/brainsuite \
  /data /output participant --stages DASHBOARD --localWebserver
```
where ```-p 8080:8080``` tells the Docker to expose port local host's port 8080 to Docker container's port 8080. 
Stages include DASHBOARD, which indicates that the BIDS App will launch the BrainSuite Dashboard.

### Running real-time QC and BrainSuite Dashboard with an existing web server ###
If your institution has a running web server and you would like to serve using this web server, you do not need to expose ports or start a local web server. 
Instead, all you need to do is to set the path to the QC output directory; this location must be where the web server will be serving from.

```bash
docker run -ti --rm \
  -v /path/to/local/bids/input/dataset/:/data \
  -v /path/to/local/output/:/output \
  bids/brainsuite \
  /data /output participant --stages DASHBOARD --QCdir /path/to/QC/output
```

You can also specify a list of subjects you would like to selectively QC by using the --QCsubjList argument (see usage above).


### Group-level analysis usage ###

#### Pre-requisite ####
* A TSV file containing data that is to be used for group analysis. The file must contain a column with a column header “**participant_id**” with the subject ID listed. An example demographics file can be found [here](sample_demographics.tsv). 
* A JSON file containing the specifications for group level analysis. Sample JSON file is provided with the source code ([BrainSuite/sample_modelspec.json](sample_modelspec.json))

Explanation on all the fields in the modelspec.json file are found [here](modelspec_details.md).

To run group-level mode:
```bash
docker run -ti --rm \
  -v /path/to/local/bids/input/dataset/:/data \
  -v /path/to/local/output/:/output \
  bids/brainsuite \
  /data /output group --modelspec modelspec.json
```

## Support
Questions about usage can be submitted to http://forums.brainsuite.org/. 
Issues or suggestions can be directly submitted as an issue to this Github Repository.


## Acknowledgments ##
This project is supported by NIH Grant R01-NS074980.

## Licenses ## 
The BrainSuite BIDS App makes use of several freely available software packages. Details on the licenses for each of these are provide in the files within the LICENSES directory of this repository.