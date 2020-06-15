""" This module contains helpful utility function for running statistics using BFP """

import configparser
config = configparser.ConfigParser()
import csv
import os
import sys
import scipy.io as spio
import scipy as sp
from tqdm import tqdm
sys.path.append('../BrainSync')
from bin.deprecated.brainsync import normalizeData
import io


def readConfig(fname):
    config.read(fname)
    section = config.sections()

    class cf:
        pass

    #class demo:
    #pass
    for ii in range(len(section)):
        v = config.options(section[ii])
        for i in range(len(v)):
            #print(str(section[ii]) + ': '+ str(v[i]))
            setattr(cf, v[i], config.get(section[ii], v[i]))

            #if section[ii] == 'demographics':
            #   setattr(demo, v[i], config.get(section[ii],v[i]))

    return cf


def read_demoCSV(csvfname, data_dir, file_ext, colsubj, colvar_exclude,
                 colvar_atlas, colvar_main, colvar_reg1, colvar_reg2):
    ''' loads csv file containing subjects' demographic information
        csv file should contain the following 5 columns for: subjectID, subjects to exclude (1=exclude), main effect variable, and 2 covariates to control for.
        if less than 2 covariates, create columns where all subjects have value of 1 so regression has no effect. '''
    # print(csvfname, data_dir, file_ext, colsubj, colvar_exclude,
    #              colvar_atlas, colvar_main, colvar_reg1, colvar_reg2)
    file = open(csvfname)
    numline = len(file.readlines())
    subN = numline - 1

    sub_ID = []
    sub_fname = []
    subAtlas_idx = []
    reg_var = []
    reg_cvar1 = []
    reg_cvar2 = []
    count1 = 0
    pbar = tqdm(total=subN)
    lst = os.listdir(data_dir)
    # with open(csvfname, newline='') as csvfile:
    #     creader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
    with io.open(csvfname, newline='') as csvfile:
        creader = csv.DictReader(csvfile, delimiter='\t', quotechar='"')
        for row in creader:
            sub = row[colsubj]
            fname = os.path.join(data_dir, sub + "/func/" + sub + file_ext)
            # print(fname)
            if not os.path.isfile(fname) or int(row[colvar_exclude]) != 0:
                fname = os.path.join(data_dir, sub + file_ext)
                if not os.path.isfile(fname) or int(row[colvar_exclude]) != 0:
                    continue

            rvar = row[colvar_main]
            rcvar1 = row[colvar_reg1]
            rcvar2 = row[colvar_reg2]
            if rcvar2 == 'F':
                rcvar2 = 1

            if rcvar2 == 'M':
                rcvar2 = 0

            subAtlas_idx.append(row[colvar_atlas])
            sub_fname.append(fname)
            sub_ID.append(sub)
            reg_var.append(float(rvar))
            reg_cvar1.append(float(rcvar1))
            reg_cvar2.append(float(rcvar2))
            count1 += 1
            pbar.update(1)
            if count1 == subN:
                break

    pbar.close()
    print('CSV file read\nThere are %d subjects' % (len(sub_ID)))

    return sub_ID, sub_fname, subAtlas_idx, reg_var, reg_cvar1, reg_cvar2


def read_demoCSV_list(csv_fname):
    with open(csv_fname, 'r') as infile:
        # read the file as a dictionary for each row ({header : value})
        reader = csv.DictReader(infile)
        data = {}
        for row in reader:
            for header, value in row.items():
                try:
                    data[header].append(value)
                except KeyError:
                    data[header] = [value]
    return data


def load_bfp_data(sub_fname, LenTime):
    ''' sub_fname: list of filenames of .mat files that contains Time x Vertex matrix of subjects' preprocessed fMRI data '''
    ''' LenTime: number of timepoints in data. this should be the same in all subjects '''
    ''' Outputs 3D matrix: Time x Vector x Subjects '''
    count1 = 0
    subN = len(sub_fname)
    print('loading data for ' + str(subN) + ' subjects')
    pbar = tqdm(total=subN)
    for ind in range(subN):
        fname = sub_fname[ind]
        df = spio.loadmat(fname)
        data = df['dtseries'].T
        if int(data.shape[0]) != LenTime:
            print(sub_fname[ind] +
                  ' does not have the correct number of timepoints')
        d, _, _ = normalizeData(data)

        if count1 == 0:
            sub_data = sp.zeros((LenTime, d.shape[1], subN))

        sub_data[:, :, count1] = d[:LenTime, ]
        count1 += 1
        pbar.update(1)
        if count1 == subN:
            break

    pbar.close()

    print('loaded data for ' + str(subN) + ' subjects')
    return sub_data


def write_text_timestamp(fname, msg):
    if os.path.isfile(fname):
        file = open(fname, "a")
        file.write("\n")
    else:
        file = open(fname, "w")
    import datetime
    dt = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")
    file.write(dt + "\n")
    file.write(msg + "\n")
    file.close()
    print(msg)