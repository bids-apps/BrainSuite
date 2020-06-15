# ||AUM||
import scipy.io as spio
import scipy as sp
import numpy as np
from fmri_methods_sipi import hotelling_t2
from surfproc import view_patch_vtk, patch_color_attrib, smooth_surf_function, smooth_patch
from dfsio import readdfs
import os
from brainsync import normalizeData, brainSync
from statsmodels.sandbox.stats.multicomp import fdrcorrection0 as FDR
from sklearn.decomposition import PCA
import csv

BFPPATH = '/home/ajoshi/coding_ground/bfp'
BrainSuitePath = '/home/ajoshi/BrainSuite17a/svreg'
NDim = 31
#%%

p_dir = '/deneb_disk/ADHD_Peking_gord'
lst = os.listdir(p_dir)
count1 = 0
nsub = 0

#%% Read CSV File
normSub = [];adhdCombinedSub=[];adhdHyperactiveSub=[];adhdInattentive=[];
with open('/deneb_disk/ADHD_Peking_bfp/Peking_all_phenotypic.csv', newline='') as csvfile:    
    creader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
    for row in creader:
        dx = row['DX']
        sub = row['ScanDir ID']
        qc = row['QC_Rest_1']
        fname = os.path.join(p_dir, sub + '_rest_bold.32k.GOrd.mat')

        if not os.path.isfile(fname) or int(qc) != 1:
            continue

        if int(dx) == 0:
            normSub.append(sub)

        if int(dx) == 1:
            adhdCombinedSub.append(sub)

        if int(dx) == 2:
            adhdHyperactiveSub.append(sub)

        if int(dx) == 3:
            adhdInattentive.append(sub)

        print(sub, dx, qc)


normSubOrig = normSub

#%% Read Normal Subjects
normSub = normSub[:50]
count1 = 0
for sub in normSub:
    fname = os.path.join(p_dir, sub + '_rest_bold.32k.GOrd.mat')
    df = spio.loadmat(fname)
    data = df['dtseries'].T
    d, _, _ = normalizeData(data)

    if count1 == 0:
        sub_data = sp.zeros((235, d.shape[1], len(normSub)))

    sub_data[:, :, count1] = d[:235, ]
    count1 += 1
    print(count1, )
    if count1 == 50:
        break

#%% Create Average atlas by synchronizing everyones data to one subject
atlas = 0; q=3
nSub = len(normSub)
for ind in range(nSub):
    Y2, _ = brainSync(X=sub_data[:, :, q], Y=sub_data[:, :, ind])
    atlas += Y2
atlas /= (nSub)
spio.savemat('ADHD_avg_atlas.mat', {'atlas':atlas})

#%% Compute PCA basis using atlas

pca = PCA(n_components=NDim)
pca.fit(atlas.T)
print(pca.explained_variance_ratio_)



#%% Read Normal Subjects
normSub = normSubOrig[50:135]
count1 = 0
for sub in normSub:
    fname = os.path.join(p_dir, sub + '_rest_bold.32k.GOrd.mat')
    df = spio.loadmat(fname)
    data = df['dtseries'].T
    d, _, _ = normalizeData(data)
    if count1 == 0:
        sub_data = sp.zeros((235, d.shape[1], 50))
    sub_data[:, :, count1] = d[:235,]
    count1 += 1
    print(count1, )
    if count1 == 50:
        break

#%% Do PCA of Normal Controls
#%% Atlas to normal subjects diff
diff = sp.zeros([sub_data.shape[1],50])
fNC = sp.zeros((NDim, sub_data.shape[1], 50))
for ind in range(50):
    Y2, _ = brainSync(X=atlas, Y=sub_data[:, :, ind])
    fNC[:, :, ind] = pca.transform(Y2.T).T
    diff[:, ind] = sp.sum((Y2 - atlas) ** 2, axis=0)
    print(ind,)

spio.savemat('ADHD_diff_avg_atlas.mat', {'diff': diff})

#%% Read ADHD Inattentive
#del sub_data
count1 = 0
for sub in adhdInattentive:
    fname = os.path.join(p_dir, sub + '_rest_bold.32k.GOrd.mat')
    df = spio.loadmat(fname)
    data = df['dtseries'].T
    d, _, _ = normalizeData(data)
    if count1 == 0:
        sub_data = sp.zeros((235, d.shape[1], 50))
    sub_data[:, :, count1] = d[:235,]
    count1 += 1
    print(count1, )
    if count1 == 50:
        break


#%% Atlas to normal subjects diff & Do PCA of ADHD
diffAdhdInatt = sp.zeros([sub_data.shape[1],50])
fADHD = sp.zeros((NDim, sub_data.shape[1], 50))

for ind in range(50):
    Y2, _ = brainSync(X=atlas, Y=sub_data[:, :, ind])
    fADHD[:, :, ind] = pca.transform(Y2.T).T
    diffAdhdInatt[:, ind] = sp.sum((Y2 - atlas) ** 2, axis=0)
    print(ind,)

spio.savemat('ADHD_diff_adhd_inattentive.mat', {'diffAdhdInatt': diffAdhdInatt})

#%% Read surfaces for visualization

lsurf = readdfs('/home/ajoshi/coding_ground/bfp/supp_data/bci32kleft.dfs')
rsurf = readdfs('/home/ajoshi/coding_ground/bfp/supp_data/bci32kright.dfs')
a=spio.loadmat('/home/ajoshi/coding_ground/bfp/supp_data/USCBrain_grayord_labels.mat')
labs=a['labels']
lsurf.attributes = np.zeros((lsurf.vertices.shape[0]))
rsurf.attributes = np.zeros((rsurf.vertices.shape[0]))
lsurf=smooth_patch(lsurf,iterations=1500)
rsurf=smooth_patch(rsurf,iterations=1500)
labs[sp.isnan(labs)]=0
diff=diff*(labs.T>0)
diffAdhdInatt=diffAdhdInatt*(labs.T>0)

nVert = lsurf.vertices.shape[0]

#%% Visualization of normal diff from the atlas
lsurf.attributes = np.sqrt(np.sum((diff), axis=1))
lsurf.attributes = lsurf.attributes[:nVert]/50
rsurf.attributes = np.sqrt(np.sum((diff), axis=1))
rsurf.attributes = rsurf.attributes[nVert:2*nVert]/50
lsurf = patch_color_attrib(lsurf, clim=[0,.2])
rsurf = patch_color_attrib(rsurf, clim=[0,.2])

view_patch_vtk(lsurf, azimuth=100, elevation=180, roll=90,
               outfile='l1normal.png', show=1)
view_patch_vtk(rsurf, azimuth=-100, elevation=180, roll=-90,
               outfile='r1normal.png', show=1)

#%% Visualization of ADHD diff from the atlas
lsurf.attributes = np.sqrt(np.sum((diffAdhdInatt), axis=1))
lsurf.attributes = lsurf.attributes[:nVert]/50
rsurf.attributes = np.sqrt(np.sum((diffAdhdInatt), axis=1))
rsurf.attributes = rsurf.attributes[nVert:2*nVert]/50
lsurf = patch_color_attrib(lsurf, clim=[0, .2])
rsurf = patch_color_attrib(rsurf, clim=[0, .2])

view_patch_vtk(lsurf, azimuth=100, elevation=180, roll=90,
               outfile='l1adhd.png', show=1)
view_patch_vtk(rsurf, azimuth=-100, elevation=180, roll=-90,
               outfile='r1adhd.png', show=1)

#%%
lsurf.attributes = np.sqrt(np.sum((diffAdhdInatt), axis=1))-np.sqrt(np.sum((diff), axis=1))
rsurf.attributes = np.sqrt(np.sum((diffAdhdInatt), axis=1))-np.sqrt(np.sum((diff), axis=1))
lsurf.attributes = lsurf.attributes[:nVert]/50
rsurf.attributes = rsurf.attributes[nVert:2*nVert]/50

#lsurf.attributes = smooth_surf_function(lsurf,lsurf.attributes,1,1)
#rsurf.attributes = smooth_surf_function(rsurf,rsurf.attributes,1,1)
lsurf = patch_color_attrib(lsurf, clim=[-0.005, 0.005])
rsurf = patch_color_attrib(rsurf, clim=[-0.005, 0.005])

view_patch_vtk(lsurf, azimuth=100, elevation=180, roll=90,
               outfile='l1adhd_normal_diff.png', show=1)
view_patch_vtk(rsurf, azimuth=-100, elevation=180, roll=-90,
               outfile='r1adhd_normal_diff.png', show=1)

#%%
pv = sp.zeros(diff.shape[0])
for vind in range(diff.shape[0]):
    _, pv[vind] = sp.stats.ranksums(diff[vind,:], diffAdhdInatt[vind,:])

#%%

t, pvfdr = FDR(pv[labs[0, :] > 0])

lsurf.attributes = 1-pv
rsurf.attributes = 1-pv
lsurf.attributes = lsurf.attributes[:nVert]
rsurf.attributes = rsurf.attributes[nVert:2*nVert]
lsurf.attributes = smooth_surf_function(lsurf, lsurf.attributes, .3, .3)
rsurf.attributes = smooth_surf_function(rsurf, rsurf.attributes, .3, .3)

lsurf = patch_color_attrib(lsurf, clim=[0.7, 1.0])
rsurf = patch_color_attrib(rsurf, clim=[0.7, 1.0])

view_patch_vtk(lsurf, azimuth=-90, elevation=180, roll=-90,
               outfile='l1adhd_normal_pval.png', show=1)
view_patch_vtk(lsurf, azimuth=100, elevation=180, roll=90,
               outfile='l2adhd_normal_pval.png', show=1)

view_patch_vtk(rsurf, azimuth=90, elevation=180, roll=90,
               outfile='r1adhd_normal_pval.png', show=1)
view_patch_vtk(rsurf, azimuth=-100, elevation=180, roll=-90,
               outfile='r2adhd_normal_pval.png', show=1)

#%%

fa = sp.transpose(fADHD, axes=[0, 2, 1])
fc = sp.transpose(fNC, axes=[0, 2, 1])
#fa = fa * 
#fc = fc * (labs > 0)
labs=sp.squeeze(labs)
pv, t2 = hotelling_t2(fa[:, :, (labs > 0)], fc[:, :, (labs > 0)])
lsurf.attributes=sp.zeros((labs.shape[0]))
lsurf.attributes[labs>0] = 1.0 - pv
lsurf.attributes = smooth_surf_function(lsurf, lsurf.attributes[:nVert], 1, 1)
lsurf = patch_color_attrib(lsurf, clim=[0.7, 1.0])
view_patch_vtk(lsurf, azimuth=90, elevation=180, roll=90,
               outfile='l1multiadhd_normal_pval.png', show=1)
view_patch_vtk(lsurf, azimuth=-100, elevation=180, roll=-90,
               outfile='l2multiadhd_normal_pval.png', show=1)

rsurf.attributes = sp.zeros((labs.shape[0]))
rsurf.attributes[labs > 0] = 1.0 - pv
rsurf.attributes = smooth_surf_function(rsurf,
                                        rsurf.attributes[nVert:2*nVert], 1, 1)
rsurf = patch_color_attrib(rsurf, clim=[0.7, 1.0])
view_patch_vtk(rsurf, azimuth=90, elevation=180, roll=90,
               outfile='r1multiadhd_normal_pval.png', show=1)
view_patch_vtk(rsurf, azimuth=-100, elevation=180, roll=-90,
               outfile='r2multiadhd_normal_pval.png', show=1)




#%% Automatic Classification of subtypes


