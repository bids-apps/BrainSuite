import scipy.io as spio
import scipy as sp
from scipy import stats
import numpy as np
from BrainSync.fmri_methods_sipi import hotelling_t2
from BrainSync.surfproc_novtk import patch_color_attrib #, smooth_surf_function, smooth_patch #view_patch_vtk,
from BrainSync.dfsio import readdfs, writedfs
import os
from BrainSync.brainsync import normalizeData, brainSync
from statsmodels.sandbox.stats.multicomp import fdrcorrection0 as FDR
from sklearn.decomposition import PCA
from IPython import get_ipython
import csv
import io
import subprocess

BrainSuiteVersion = os.environ['BrainSuiteVersion']

def runGroupDiff(specs, outputdir):

    BFPPATH='/bfp_ver2p19'
    BrainSuitePath = '/BrainSuite{0}/svreg/'.format(BrainSuiteVersion)
    NDim = specs.ndim # Dimensionality reduction for analysis

    # study directory where all the grayordinate files lie
    p_dir = outputdir #input directory
    p_out = specs.resultdir #output directory
    CSVFILE = specs.tsv #csv file with demographics
    colsubj = 'participant_id' #subject IDs
    colcontrols = specs.controls # 1: controls for atlas; 0: subjects for testing
    colexclude = specs.exclude
    file_ext = specs.fileext #input file extension
    LenTime = specs.numtimepoints #number of timepoints

    ## DO WORK ##

    print(p_out)
    if not os.path.isdir(p_out):
        os.makedirs(p_out)

    lst = os.listdir(p_dir)
    count1 = 0
    nsub = 0

    # Read CSV File
    normSub = []
    normSubtest = []
    group1Sub = []
    group2Sub = []
    group3Sub = []
    with io.open(CSVFILE, newline='') as csvfile:
        creader = csv.DictReader(csvfile, delimiter='\t', quotechar='"')
        for row in creader:
            sub = row[colsubj]
            dx = row[colcontrols]
            qc = row[colexclude]
            fname = os.path.join(p_dir, sub + file_ext)
            print(fname)

            if not os.path.isfile(fname) or int(qc) != 0:
                continue

            if int(dx) == 0:
                normSub.append(sub)

            if int(dx) == 4:
                normSubtest.append(sub)

            if int(dx) == 1:
                group1Sub.append(sub)

    print('TSV file read\nThere are %d Controls, %d Group1, %d Combined subjects'
          % (len(normSub), len(group1Sub), len(group1Sub) + len(normSub)))

    NumNCforAtlas = len(normSub)
    normSubOrig = normSub

    # Read Normal Subjects for atlas
    normSub = normSub[:NumNCforAtlas]
    count1 = 0
    for sub in normSub:
        fname = os.path.join(p_dir, sub + file_ext)
        df = spio.loadmat(fname)
        data = df['dtseries'].T
        d, _, _ = normalizeData(data)

        if count1 == 0:
            sub_data = sp.zeros((LenTime, d.shape[1], len(normSub)))

        sub_data[:, :, count1] = d[:LenTime, ]
        count1 += 1
        print '%d, '% count1, ' '
        print(sub)
        if count1 == NumNCforAtlas:
            break

    print('done')

    # Create Average atlas by synchronizing everyones data to one subject
    atlas = 0;
    # q = 0
    count1 = 0
    nSub = len(normSub)

    dist_all_orig = sp.zeros([nSub, nSub])
    dist_all_rot = dist_all_orig.copy()

    for ind1 in range(NumNCforAtlas):
        for ind2 in range(NumNCforAtlas):
            dist_all_orig[ind1, ind2] = sp.linalg.norm(sub_data[:, :, ind1] - sub_data[:, :, ind2])
            sub_data_rot, _ = brainSync(X=sub_data[:, :, ind1], Y=sub_data[:, :, ind2])
            dist_all_rot[ind1, ind2] = sp.linalg.norm(sub_data[:, :, ind1] -sub_data_rot)
            print(ind1, ind2, dist_all_rot[ind1, ind2])

    q = sp.argmin(dist_all_rot.sum(1))

    for ind in range(nSub):
        Y2, _ = brainSync(X=sub_data[:, :, q], Y=sub_data[:, :, ind])
        atlas += Y2
        count1 += 1
        print '%d, ' % count1, ' '
        atlas /= (nSub)
        spio.savemat(p_out + '/Controls_avg_atlas.mat', {'atlas': atlas})

        print('done')

    # Compute PCA basis using atlas
    pca = PCA(n_components=NDim)
    pca.fit(np.transpose(atlas))
    # print(pca.explained_variance_ratio_)

    print('done')

    # %% Read Normal Subjects
    NumNC = len(normSubtest)
    print('There are total %d normal controls' % len(normSubOrig))
    print(' %d were used for generating atlas' % NumNCforAtlas)
    print(' another %d will be used as controls' % NumNC)
    # normSub = normSubOrig[NumNCforAtlas:]
    count1 = 0
    for sub in normSubtest:
        fname = os.path.join(p_dir, sub + file_ext)
        df = spio.loadmat(fname)
        data = df['dtseries'].T
        d, _, _ = normalizeData(data)
        if count1 == 0:
            sub_data = sp.zeros((LenTime, d.shape[1], NumNC))
        sub_data[:, :, count1] = d[:LenTime, ]
        count1 += 1
        print '%d, ' % count1, ' '
        print(sub)
        if count1 == NumNC:
            break
    np.savetxt(p_out + "/subj_controlstest.csv", normSubtest, delimiter=",", fmt='%s')
    print('done')

    # ### Use BrainSync
    # Synchronize the subject data to the atlas and perform PCA of the result. Then compute difference between atlas and the subject. This is the test statistic.

    diff = sp.zeros([sub_data.shape[1], NumNC])
    fNC = sp.zeros((NDim, sub_data.shape[1], NumNC))
    count1 = 0
    for ind in range(NumNC):
        Y2, _ = brainSync(X=atlas, Y=sub_data[:, :, ind])
        fNC[:, :, ind] = pca.transform(Y2.T).T
        diff[:, ind] = sp.sum((Y2 - atlas) ** 2, axis=0)
        count1 += 1
        print '%d, ' % count1, ' '

        spio.savemat(p_out + '/Controlstest_diff_avg_atlas.mat', {'diff': diff})

    # ### Read test Group

    ngroup1 = len(group1Sub)
    count1 = 0
    for sub in group1Sub:
        fname = os.path.join(p_dir, sub + file_ext)
        df = spio.loadmat(fname)
        data = df['dtseries'].T
        d, _, _ = normalizeData(data)
        if count1 == 0:
            sub_data = sp.zeros((LenTime, d.shape[1], ngroup1))
        sub_data[:, :, count1] = d[:LenTime, ]
        count1 += 1
        print '%d, ' % count1, ' '
        print(sub)
        if count1 == ngroup1:
            break
    np.savetxt(p_out + "/subj_testgroup.csv", group1Sub, delimiter=",", fmt='%s')
    print('done')

    # ### Perform PCA on the test subjects.
    # Use the same basis that was used for normal controls.


    # %% Atlas to normal subjects diff & Do PCA of ADHD
    diffgroup1 = sp.zeros([sub_data.shape[1], ngroup1])
    fgroup1 = sp.zeros((NDim, sub_data.shape[1], ngroup1))

    for ind in range(ngroup1):
        Y2, _ = brainSync(X=atlas, Y=sub_data[:, :, ind])
        fgroup1[:, :, ind] = pca.transform(Y2.T).T
        diffgroup1[:, ind] = sp.sum((Y2 - atlas) ** 2, axis=0)
        print '%d, ' % count1, ' '

        spio.savemat(p_out + '/Group1_diff_atlas.mat', {'diffgroup1': diffgroup1})
        print('done')

    # ### Read surfaces for visualization

    lsurf = readdfs(BFPPATH + '/supp_data/bci32kleft.dfs')
    # lsurf.faces = lsurf.faces[:, (1, 3, 2)]
    rsurf = readdfs(BFPPATH + '/supp_data/bci32kright.dfs')
    # rsurf.faces = rsurf.faces[:, (1, 3, 2)]
    a = spio.loadmat(BFPPATH + '/supp_data/USCBrain_grayord_labels.mat')
    labs = a['labels']

    lsurf.attributes = np.zeros((lsurf.vertices.shape[0]))
    rsurf.attributes = np.zeros((rsurf.vertices.shape[0]))
    # lsurf = smooth_patch(lsurf, iterations=1500)
    # rsurf = smooth_patch(rsurf, iterations=1500)
    labs[sp.isnan(labs)] = 0
    diff = diff * (labs.T > 0)
    diffgroup1 = diffgroup1 * (labs.T > 0)

    nVert = lsurf.vertices.shape[0]

    # ### Visualize the norm of the difference of Normal Controls from the atlas, at each point on the cortical surface

    lsurf.attributes = np.sqrt(np.sum((diff), axis=1))
    lsurf.attributes = lsurf.attributes[:nVert] / 50
    rsurf.attributes = np.sqrt(np.sum((diff), axis=1))
    rsurf.attributes = rsurf.attributes[nVert:2 * nVert] / 50
    lsurf = patch_color_attrib(lsurf, clim=[0, .15])
    rsurf = patch_color_attrib(rsurf, clim=[0, .15])
    writedfs(p_out + '/RH_diff_control.dfs', rsurf)
    writedfs(p_out + '/LH_diff_control.dfs', lsurf)

    lsurf.attributes = np.sqrt(np.sum((diffgroup1), axis=1))
    lsurf.attributes = lsurf.attributes[:nVert] / 50
    rsurf.attributes = np.sqrt(np.sum((diffgroup1), axis=1))
    rsurf.attributes = rsurf.attributes[nVert:2 * nVert] / 50
    lsurf = patch_color_attrib(lsurf, clim=[0, .15])
    rsurf = patch_color_attrib(rsurf, clim=[0, .15])
    writedfs(p_out + '/RH_diff_group1.dfs', rsurf)
    writedfs(p_out + '/LH_diff_group1.dfs', lsurf)

    lsurf.attributes = np.sqrt(np.sum((diffgroup1), axis=1)) - np.sqrt(np.sum((diff), axis=1))
    rsurf.attributes = np.sqrt(np.sum((diffgroup1), axis=1)) - np.sqrt(np.sum((diff), axis=1))
    lsurf.attributes = lsurf.attributes[:nVert] / 50
    rsurf.attributes = rsurf.attributes[nVert:2 * nVert] / 50

    lsurf = patch_color_attrib(lsurf, clim=[-0.01, 0.01])
    rsurf = patch_color_attrib(rsurf, clim=[-0.01, 0.01])
    writedfs(p_out + '/RH_group1_normal_diff.dfs', rsurf)
    writedfs(p_out + '/LH_group1_normal_diff.dfs', lsurf)

    pv = sp.zeros(diff.shape[0])
    for vind in range(diff.shape[0]):
        _, pv[vind] = stats.ranksums(diff[vind, :], diffgroup1[vind, :])

    t, pvfdr = FDR(pv[labs[0, :] > 0])

    lsurf.attributes = 1 - pv
    rsurf.attributes = 1 - pv
    lsurf.attributes = lsurf.attributes[:nVert]
    rsurf.attributes = rsurf.attributes[nVert:2 * nVert]

    lsurf = patch_color_attrib(lsurf, clim=[0.95, 1.0])
    rsurf = patch_color_attrib(rsurf, clim=[0.95, 1.0])
    writedfs(p_out + '/RH_group1_normal_pval.dfs', rsurf)
    writedfs(p_out + '/LH_group1_normal_pval.dfs', lsurf)

    # fa = sp.transpose(fgroup1, axes=[0, 2, 1])
    # fc = sp.transpose(fNC, axes=[0, 2, 1])
    #
    # labs = sp.squeeze(labs)
    # pv, t2 = hotelling_t2(fa[:, :, (labs > 0)], fc[:, :, (labs > 0)])
    #
    # lsurf.attributes = sp.zeros((labs.shape[0]))
    # lsurf.attributes[labs > 0] = 1.0 - pv
    # lsurf = patch_color_attrib(lsurf, clim=[0.95, 1.0])
    #
    # rsurf.attributes = sp.zeros((labs.shape[0]))
    # rsurf.attributes[labs > 0] = 1.0 - pv
    #
    # rsurf = patch_color_attrib(rsurf, clim=[0.95, 1.0])
    #
    # writedfs(p_out + '/RH_multigroup1_normal_pval.dfs', rsurf)
    # writedfs(p_out + '/LH_multigroup1_normal_pval.dfs', lsurf)

    # ### Autocrop all the generated images and render
    # This assumes imagemagick installed on your linux machine. Otherwise use your own method to batch autocrop the images.


    # subprocess.call('mogrify -trim +repage *.png')