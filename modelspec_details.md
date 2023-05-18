# Model specification file for group-level stage
To run group-level analysis, a JSON format model specification is required. A sample modelspec.json file is found here ([BrainSuite/sample_modelspec.json](https://bitbucket.org/brainsuite/brainsuite-bids-app/src/master/sample_modelspec.json)).

To run group-level mode:

```
docker run -ti --rm
  -v /path/to/local/bids/input/dataset/:/data
  -v /path/to/local/output/:/output
  bids/brainsuite
  /data /output group --modelspec modelspec.json
 ```

### Group level analysis for anatomical and diffusion data ###
For parameters whose options are Boolean values, 1 (True) and 0 (False) are used, e.g., 1 enables an option and 0 disables it.

* **tsv_fname** : Specifies the TSV file containing demographic data and/or clinical variables that will be used for group analysis
* **out_dir** : Output directory location where statistical analysis results will be stored. This folder will be created if it does not exist
* **measure** : Specifies the imaging measure of interest. Available options are: cortical thickness measures from surface files (cbm); tensor-based morphometry using the Jacobian determinant of the deformation map from subject to atlas (tbm); ROI-based analysis using scalar summary statistics (roi); DTI parametric maps (dbm). Options: {cbm, tbm, roi, dbm}
* **test** : Specifies the model. Available options are: ANOVA (anova); correlations test (corr); t-test (ttest). Options: {anova, corr, ttest}
* **main_effect** : Specifies the main predictor variable for ANOVA. Used only if test=anova. This value must match the corresponding column header in the TSV file specified in the tsv_fname field.
* **covariates** : Specifies the covariates for ANOVA. Used only if test=anova. Values must match column headers from the TSV file in the tsv_fname field. Must be in list form and can contain multiple elements.
* **corr_var** : (Specifies the variable for correlation test. Used only if test=corr.
* **group_var** : Specifies the group variable for paired t-test. Used only if test=ttest and paired=1.
* **paired** : Specifies the t-test type. If enabled (1), then paired t-test will be performed.  If disabled (0), then unpaired t-test will be performed. Used only if test=ttest.
* **smooth** : Specifies the smoothing level used for cbm,  tbm, and dbm.  The smoothing levels must match the levels used during preprocessing. For example, if surface smoothing levels were set to 2.0mm for participant-level processing, then cbm’s smoothing level should be set to 2.
* **mult_comp** : Specifies the method for multiple comparison correction. Used only if measure is cbm, tbm, or dbm. Available options are: FDR (fdr); max-T permutation test (perm). Options: {fdr, perm}
* **niter** : Specifies the number of iterations for the permutation method. Only used if mult_comp=perm.
* **pvalue** : Specifies the method for computing p-values. Options: parametric, perm. Available options are: parametric method, which is the classical p-value method (parametric); permutation method, which is the Freedman-Lane method (Freedman & Lane, 1983) (perm). Options: {parametric, perm}
* **roiid** : BrainSuite ROI ID number for ROI analysis. Only used if measure= roi. Must be in list format. Multiple IDs can be listed. For example, to study the left (641) and right thalamus (640): \[640,641].
* **hemi** : (For measure: cbm) Hemisphere selection. Options: {left, right, both}.
* **maskfile** : (For measure: tbm, dbm) If mask file is specified, then only the regions within the mask will be considered for statistical analysis. The mask file must be in the same space as the atlas that was used to register the subjects during SVReg.
* **atlas** : Atlas file. Default is the atlas that was used to run SVReg.
* **roimeas** : (For measure: roi) ROI measure of interest. Available options are: average GM thickness in cortical regions (gmthickness); average GM volume (gmvolume); average wm volume (wmvolume). Options: {gmthickness, gmvolume, wmvolume}.
* **dbmmeas** : (For measure: dbm) Diffusion measure of interest. Options: {FA, MD, axial, radial, mADC, FRT_GFA}.
* **exclude_col** :User can specify column header name in the TSV file (the same TSV file in the tsv_fname field). This column must exist in the TSV file for each subject/row, in which 0 indicates no exclusion and 1 indicates exclusion

##### Functional data analysis #####
* **tsv_fname** : Specifies the TSV file containing demographic data and/or clinical variables that will be used for group analysis
* **out_dir** : Output directory location where statistical analysis results will be stored. This folder will be created if it does not exist
* **file_ext** : Input file suffix, which is the BFP output in grayordinate space, e.g., ’-rest_bold.32k.GOrd.filt.mat’.
* **lentime** : Number of timepoints in the fMRI data.
* **matchT** : If some subjects have less than timepoints (’lentime’), enabling this field will add zero values to match number of timepoints. Options: {0, 1}
* **stat_test** : Model to be run. Options:{atlas-linear, atlas-group, pairwise-linear}.
* **pw_pairs** : (For stat_test: pairwise-linear) Number of random pairs to measure
* **pw_fdr** : (For stat_test: pairwise-linear) Multiple comparisons correction method. If enabled (1), FDR correction will be used. If disabled (0), max-T permutations will be used
* **pw_perm** : (For stat_test: pairwise-linear and pw_fdr: 0) Number of permutations used for max-T permutation method.
* **outname** : File prefixes for statistical output files.
* **sig_alpha** : P-value significance level (alpha).
* **smooth_iter** : Level of smoothing applied on brain surface outputs.
* **save_surfaces** : If enabled (1), save surface files. If disabled (0), do not save surface files. Options: {True, False}
* **save_figures** : If enabled (1), to save PNG snapshots of the surface files. If disabled (0), does not save. Options: {True, False}
* **atlas_groupsync** : If enabled, an atlas is generated by first performing group alignment of fMRI data and then averaging over the entire group. If disabled, a reference atlas is created by identifying one representative subject. Options: {True, False}
* **atlas_fname** : File name of user-defined atlas. Variable should be called atlas_data. Leave empty if no user-defined atlas should be used
* **test_all** : If enabled (1), subjects used for atlas generation are included during hypothesis testing. If disabled (0), subjects used for atlas creation are excluded from testing your hypothesis. Options: {True, False}
* **colvar_main** : For linear regression or group testing, the main effect of study.
* **colvar_reg1** : For group comparisons. assign all rows with zero values if running linear regression. Control up to 2 variables by linearly regressing out the effect. If you only have less than 2 variable you would like to regression out, you can create and assign a dummy column(s) with zero values for all rows.
* **colvar_reg2** : See explanation for colvar_reg1.
* **colvar_exclude** : User can specify column header name in the TSV file (the same TSV file in the tsv_fname field). This column must exist in the TSV file for each subject/row, in which 0 indicates no exclusion and 1 indicates exclusion
* **colvar_atlas** : User can specify column header name in the TSV file (the same TSV file in the tsv_fname field). This column must exist in the TSV file for each subject/row, 1 subjects that would be used to create a representative functional atlas, and 0 otherwise
