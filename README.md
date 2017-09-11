# BrainSuite BIDS-App (Light-weight)
This is the BIDS-App version of BrainSuite17a (http://brainsuite.org/). 

## Description
BrainSuite is an open-source collection of software for processing structural and diffusion MRI, with planned enhancements to support functional MRI. This BIDS-App version of BrainSuite provides a portable, streamlined method of performing primary BrainSuite analysis workflows. 
These stages include: 
* Extracting cortical surface models from T1-weighted (T1w) MRI ([CSE](http://brainsuite.org/processing/surfaceextraction/)).
* Performing surface-constrained volumetric registration ([SVReg](http://brainsuite.org/processing/svreg/)) to rpoduce consistent surface and colume reigstrations to a labeled atlas.
* Processing diffusion weighted imaging (DWI) to correct image distortion, co-registering the DWI to the T1w scan, and fitting diffusion models to the DWI data ([BDP](http://brainsuite.org/processing/diffusion/)). 

## Usage
### Data input requirements
This App requires at least one T1w image. If no corresponding DWI data is found, the App will only run CSE and SVReg on the T1w(s). If there are corresponding DWI data (DWI image data, bval file, and bvec file), the App will grab the nearest DWI data (i.e. within sub-ID/ directory or sub-ID/ses directory) and will perform CSE, SVReg, and BDP. 

If there are unequal number of T1w data and DWI data, the App will process the T1w and DWI data in pairs until there are no matched pairs left. The pairs will be matched according to the run numbers (i.e. run-01). 

### Command line arguments
```
usage: run.py [-h]
              [--participant_label PARTICIPANT_LABEL [PARTICIPANT_LABEL ...]]
              [--stages {CSE,SVREG,BDP} [{CSE,SVREG,BDP} ...]]
              [--atlas {BSA,BCI}] [--singleThread] [-v]
              bids_dir output_dir {participant}

BrainSuite17a BIDS-App (T1w, dMRI)

positional arguments:
  bids_dir              The directory with the input dataset formatted
                        according to the BIDS standard.
  output_dir            The directory where the output files should be stored.
                        If you are running group level analysis this folder
                        should be prepopulated with the results of
                        theparticipant level analysis.
  {participant}         Level of the analysis that will be performed. Multiple
                        participant level analyses can be run independently
                        (in parallel) using the same output_dir.

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
  --atlas {BSA,BCI}     Atlas that is to be used for labeling in SVReg.
                        Default atlas: BCI-DNI. Options: BSA, BCI.
  --singleThread        Turns on single-thread mode for SVReg.
  -v, --version         show program's version number and exit

```
To run it in participant level mode:
```bash
docker run -ti --rm \
  -v /path/to/local/bids/input/dataset/:/data \
  -v /path/to/local/output/:/output \
  brainsuitebids \
  /data /output participant --participant_label 01
```
Where 01 is the "sub-01". User can supply multiple participant labels by listing them delimited by space (i.e. --participant_label 01 02). If ``` --stages ```stages is not specified, the default is to run all stages. 

User can remove ``` --participant_label <ids-list> ``` argument to have all subjects processed. 

All sessions will be processed. The output files will be located in the output folder specified.

## Support
Questions about usage can be submitted to http://forums.brainsuite.org/. 
Issues or suggestions can be directly submitted as an issue to this Github Repository.

## FYI
* BDP requires at least 6GB of memory. You may have to increase memory when you run the container. 
* Turn on single thread mode (``` --singleThread ```) if your machine cannot support MATLAB's parpool.
* BDP estimates tensors, FRT ODF, and FRACT ODF.
