# AUM
# Shree Ganeshaya Namaha

##########################################################################################################################
## SCRIPT TO PREPROCESS THE FUNCTIONAL SCAN
## parameters are passed from 0_preprocess.sh
## This is based on batch_process.sh script
## Written by the Underpants Gnomes (a.k.a Clare Kelly, Zarrar Shehzad, Maarten Mennes & Michael Milham)
## for more information see www.nitrc.org/projects/fcon_1000
##
##########################################################################################################################

import os
import subprocess
import nibabel as nib
import numpy as np
from scipy.ndimage.filters import convolve


def func_preproc(t1, fmri, func_dir, TR, nuisance_template, FWHM, hp, lp, FSLRigidReg):
	n_vols = subprocess.check_output(['3dinfo', '-nv', '{}.nii.gz'.format(fmri)])
	n_vols = float(n_vols)
	TRstart = 0
	TRend = int(n_vols-1)
	sigma = float(FWHM)/2.3548

	usc_rigid_reg_bin = os.path.join('/bfp_ver2p19', 'usc_rigid_reg.sh')
	transform_data_affine_bin = os.path.join('/bfp_ver2p19', 'transform_data_affine.sh')

	bname = os.path.basename(fmri)
	bname = os.path.splitext(bname)[0]
	bname = os.path.splitext(bname)[0] # just in case double extension e.g.) .nii.gz
	example = '{}_example'.format(bname)

	############################################################################################
	##---START OF SCRIPT----------------------------------------------------------------------##
	############################################################################################
	print('---------------------------------------')
	print('BFP fMRI PREPROCESSING !')
	print('---------------------------------------')

	cwd = os.getcwd()
	os.chdir(func_dir)
	## 1. Dropping first TRs
	print('Dropping first TRs')
	os.system('3dcalc -a '+fmri+'.nii.gz['+str(TRstart)+'..'+str(TRend)+"] -expr 'a' -prefix "+fmri+'_dr.nii.gz')

	## 2. Deoblique
	print('Deobliquing')
	os.system('3drefit -deoblique '+fmri+'_dr.nii.gz')

	## 3. Reorient into fsl friendly space (what AFNI calls RPI)
	print('Reorienting')
	os.system('3dresample -orient RPI -inset '+fmri+'_dr.nii.gz -prefix '+fmri+'_ro.nii.gz')

	## 4. Motion correct to average of timeseries
	print('Motion correcting')
	os.system('3dTstat -mean -prefix '+fmri+'_ro_mean.nii.gz '+fmri+'_ro.nii.gz')
	os.system('3dvolreg -Fourier -twopass -base '+fmri+'_ro_mean.nii.gz -zpad 4 -prefix '+fmri+'_mc.nii.gz -1Dfile '+fmri+'_mc.1D '+fmri+'_ro.nii.gz')

	## 5. Remove skull/edge detect
	print('Skull stripping')
	os.system('3dAutomask -prefix '+fmri+'_mask.nii.gz -dilate 1 '+fmri+'_mc.nii.gz')
	os.system('3dcalc -a '+fmri+'_mc.nii.gz -b '+fmri+"_mask.nii.gz -expr 'a*b' -prefix "+fmri+'_ss.nii.gz')

	## 6. Get eighth image for use in registration
	print('Getting example_func for registration')
	os.system('3dcalc -a '+fmri+"_ss.nii.gz[7] -expr 'a' -prefix "+example+'_func.nii.gz')

	## 7. Spatial smoothing
	print('Spatial smoothing')
	os.system('fslmaths '+fmri+'_ss.nii.gz -kernel gauss '+str(sigma)+' -fmean -mas '+fmri+'_mask.nii.gz '+fmri+'_sm.nii.gz')

	## 8. Grandmean scaling
	print('Grand-mean scaling')
	os.system('fslmaths '+fmri+'_sm.nii.gz -ing 10000 '+fmri+'_gms.nii.gz -odt float')

	## 9. Temporal filtering
	print('Band-pass filtering')
	os.system('3dFourier -lowpass '+str(lp)+' -highpass '+str(hp)+' -retrend -prefix '+fmri+'_filt.nii.gz '+fmri+'_gms.nii.gz')

	## 10. Detrending
	print('Removing linear and quadratic trends')
	os.system('3dTstat -mean -prefix '+fmri+'_filt_mean.nii.gz '+fmri+'_filt.nii.gz')
	os.system('3dDetrend -polort 2 -prefix '+fmri+'_dt.nii.gz '+fmri+'_filt.nii.gz')
	os.system('3dcalc -a '+fmri+'_filt_mean.nii.gz -b '+fmri+"_dt.nii.gz -expr 'a+b' -prefix "+fmri+'_pp.nii.gz')

	## 11. Create Mask
	print('Generating mask of preprocessed data')
	os.system('fslmaths '+fmri+'_pp.nii.gz -Tmin -bin '+fmri+'_pp_mask.nii.gz -odt char')

	## 12.1 FUNC->T1
	if FSLRigidReg > 0:
		print('Using FSL rigid registration')
		os.system('flirt -ref '+t1+'.bfc.nii.gz -in '+example+'_func.nii.gz -out '+example+'_func2t1.nii.gz -omat '+example+'_func2t1.mat -cost corratio -dof 6 -interp trilinear')
		# Create mat file for conversion from subject's anatomical to functional
		os.system('convert_xfm -inverse -omat t12'+example+'_func.mat '+example+'_func2t1.mat')
	else:
		print('Using USC rigid registration')
		m = fmri+'_mask.nii.gz'
		mm = nib.load(m)
		img = mm.get_fdata()
		affine = mm.affine
		header = mm.header
		kernel = np.ones((3,3,3), dtype=np.float64)
		img = (convolve(img, kernel) > 0).astype(int) # convolve then change to binary
		mmf = fmri+'_mask_dilate.nii.gz'
		nib.save(nib.Nifti1Image(img, affine, header), mmf)
		moving_filename = example+'_func.nii.gz'
		static_filename = t1+'.bfc.nii.gz'
		output_filename = example+'_func2t1.nii.gz'
		subprocess.call([usc_rigid_reg_bin, moving_filename, static_filename, output_filename, 'inversion', mmf])

	## 12.2 FUNC->standard (3mm)
	if FSLRigidReg > 0:
		os.system('flirt -ref standard.nii.gz -in '+example+'_func.nii.gz -out '+example+'_func2standard.nii.gz -omat '+example+'_func2standard.mat -cost corratio -dof 6 -interp trilinear')
		# Create mat file for conversion from subject's anatomical to functional
		os.system('convert_xfm -inverse -omat standard2'+example+'_func.mat '+example+'_func2standard.mat')
	else:
		moving_filename = example+'_func.nii.gz'
		static_filename = 'standard.nii.gz'
		output_filename = example+'_func2standard.nii.gz'
		subprocess.call([usc_rigid_reg_bin, moving_filename, static_filename, output_filename, 'inversion', mmf])

	## 13. 
	nuisance_dir = os.path.join(func_dir, 'nuisance_{}'.format(bname))

	print(' --------------------------------------------')
	print(' !!!! RUNNING NUISANCE SIGNAL REGRESSION !!!!')
	print(' --------------------------------------------')

	## 14. Make nuisance directory
	subprocess.call(['mkdir', '-p', nuisance_dir])

	## 15. Seperate motion parameters into seperate files
	print('Splitting up subject motion parameters')
	os.system("awk '{print $1}' "+fmri+'_mc.1D > '+nuisance_dir+'/mc1.1D')
	os.system("awk '{print $2}' "+fmri+'_mc.1D > '+nuisance_dir+'/mc2.1D')
	os.system("awk '{print $3}' "+fmri+'_mc.1D > '+nuisance_dir+'/mc3.1D')
	os.system("awk '{print $4}' "+fmri+'_mc.1D > '+nuisance_dir+'/mc4.1D')
	os.system("awk '{print $5}' "+fmri+'_mc.1D > '+nuisance_dir+'/mc5.1D')
	os.system("awk '{print $6}' "+fmri+'_mc.1D > '+nuisance_dir+'/mc6.1D')

	### Exctract signal for global, csf, and wm
	## 16. Global
	print('Extracting global signal for subject')
	os.system('3dmaskave -mask '+fmri+'_pp_mask.nii.gz -quiet '+fmri+'_pp.nii.gz > '+nuisance_dir+'/global.1D')

	## 17. csf
	if FSLRigidReg > 0:
		os.system('flirt -ref '+example+'_func.nii.gz -in '+t1+'.pvc.label.nii.gz -out '+t1+'.func.pvc.label.nii.gz -applyxfm -init t12'+example+'_func.mat -interp nearestneighbour')
	else:
		subprocess.call([transform_data_affine_bin, '{}.pvc.label.nii.gz'.format(t1), 's', '{}.func.pvc.label.nii.gz'.format(t1), '{}_func.nii.gz'.format(example), '{}.bfc.nii.gz'.format(t1), '{}_example_func2t1.rigid_registration_result.mat'.format(fmri), 'nearest'])
	print('Extracting signal from csf')
	os.system('fslmaths '+t1+'.func.pvc.label.nii.gz -thr 5.5 -bin '+t1+'.func.csf.mask.nii.gz')
	os.system('fslmaths '+t1+'.func.pvc.label.nii.gz -thr 2.5 -uthr 3.5 -bin '+t1+'.func.wm.mask.nii.gz')
	os.system('3dmaskave -mask '+t1+'.func.csf.mask.nii.gz -quiet '+fmri+'_pp.nii.gz > '+nuisance_dir+'/csf.1D')

	## 18. wm
	print('Extracting signal from white matter for subject')
	os.system('3dmaskave -mask '+t1+'.func.wm.mask.nii.gz -quiet '+fmri+'_pp.nii.gz > '+nuisance_dir+'/wm.1D')

	## 19. Generate mat file (for use later), create fsf file
	print('Modifying model file')
	os.system('sed -e s:nuisance_dir:"'+nuisance_dir+'":g <'+nuisance_template+' >'+nuisance_dir+'/temp1')
	os.system('sed -e s:nuisance_model_outputdir:"'+nuisance_dir+'/residuals.feat":g <'+nuisance_dir+'/temp1 >'+nuisance_dir+'/temp2')
	os.system('sed -e s:nuisance_model_TR:"'+str(TR)+'":g <'+nuisance_dir+'/temp2 >'+nuisance_dir+'/temp3')
	os.system('sed -e s:nuisance_model_numTRs:"'+str(n_vols)+'":g <'+nuisance_dir+'/temp3 >'+nuisance_dir+'/temp4')
	os.system('sed -e s:nuisance_model_input_data:"'+func_dir+'/'+fmri+'_pp.nii.gz":g <'+nuisance_dir+'/temp4 >'+nuisance_dir+'/nuisance.fsf')

	## 20. Run feat model
	print('Running feat model')
	os.system('feat_model '+nuisance_dir+'/nuisance')
	minVal = subprocess.check_output(['3dBrickStat', '-min', '-mask', '{}_pp_mask.nii.gz'.format(fmri), '{}_pp.nii.gz'.format(fmri)])
	minVal = str(float(minVal)) # format for next line	

	## 21. Get residuals
	print('Running film to get residuals')
	os.system('film_gls --rn='+nuisance_dir+'/stats+ --noest --sa --ms=5 --in='+fmri+'_pp.nii.gz --pd='+nuisance_dir+'/nuisance.mat --thr='+minVal)

	## 22. Demeaning residuals and adding 100
	print('Demeaning residuals and adding 100')
	os.system('3dTstat -mean -prefix '+nuisance_dir+'/stats+/res4d_mean.nii.gz '+nuisance_dir+'/stats+/res4d.nii.gz')
	os.system('3dcalc -a '+nuisance_dir+'/stats+/res4d.nii.gz -b '+nuisance_dir+"/stats+/res4d_mean.nii.gz -expr '(a-b)+100' -prefix "+fmri+'_res.nii.gz')

	## 23. Resampling residuals to MNI space
	print('Resampling residuals to MNI space')
	if FSLRigidReg > 0:
		os.system('flirt -ref '+func_dir+'/standard -in '+fmri+'_res -out '+fmri+'_res2standard -applyxfm -init '+func_dir+'/'+example+'_func2standard.mat -interp trilinear')
	else:
		subprocess.call([transform_data_affine_bin, '{}_res.nii.gz'.format(fmri), 'm', '{}_res2standard.nii.gz'.format(fmri), '{}_func.nii.gz'.format(example), 'standard.nii.gz', '{}_example_func2standard.rigid_registration_result.mat'.format(fmri), 'linear'])

	## Done!
	os.chdir(cwd)
