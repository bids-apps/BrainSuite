# ||AUM||
import scipy.io as spio
import scipy as sp
import numpy as np
from fmri_methods_sipi import rot_sub_data
from surfproc import view_patch_vtk, patch_color_attrib
from dfsio import readdfs
import os
import glob
from brainsync import normalizeData, brainSync
from sklearn.manifold import MDS
import matplotlib.pyplot as plt
import h5py
#%%
# This is the name of the directory that contains the grayordinate files
p_dir = '/ImagePTE1/ajoshi/BFP_samples'
lst = glob.glob(p_dir + '/*.mat')
count1 = 0

# Get number of subjects
nsub = len(lst)
lst2 = list([])

for fname in lst:
    if not os.path.isfile(fname):
        continue
    df = spio.loadmat(fname)  #, 'r')
    d = df['dtseries']
    #   dataR = df['dataR']
    #   d = sp.concatenate((dataL, dataR), axis=1)
    d, _, _ = normalizeData(d)
    if count1 == 0:
        sub_data = sp.zeros((d.shape[0], d.shape[1], nsub))

    sub_data[:, :, count1] = d
    lst2.append(fname)
    count1 += 1
    print(count1, )

#%% Compute pairwise distance
nSub = count1
sub_data = sub_data[:, :, :nSub]

print(nSub)
dist_all_orig = sp.zeros([nSub, nSub])
dist_all_rot = dist_all_orig.copy()
#sub_data_orig = sub_data.copy()

for ind1 in range(nSub):
    for ind2 in range(nSub):
        dist_all_orig[ind1, ind2] = sp.linalg.norm(sub_data[:, :, ind1] -
                                                   sub_data[:, :, ind2])
        sub_data_rot, _ = brainSync(
            X=sub_data[:, :, ind1].T, Y=sub_data[:, :, ind2].T)
        dist_all_rot[ind1, ind2] = sp.linalg.norm(sub_data[:, :, ind1] -
                                                  sub_data_rot.T)
        print(ind1, ind2, dist_all_rot[ind1, ind2])

q = sp.argmin(dist_all_rot.sum(1))
print('The representative subject is: %s ' % lst2[q])
m = MDS(n_components=2, dissimilarity='precomputed')
e = m.fit_transform(dist_all_rot)
print(e)
fig, ax = plt.subplots()
ax.scatter(e[:, 0], e[:, 1])
for i in range(e.shape[0]):
    ax.annotate(lst2[i][30:37], (e[i, 0], e[i, 1]))

ax.set_title('MDS Plot of the subjects')
plt.savefig('MDS_plot_of_subjects.pdf')
print('Done')