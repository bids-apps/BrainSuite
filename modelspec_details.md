
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

