import nibabel as nib
import numpy as np
import argparse

def makeMask(inputFile, roi):
    fileprefix = inputFile.split('.')[0]
    nii = nib.load(inputFile)
    output=fileprefix + '.pvc.edge.mask.nii.gz'

    data = nii.get_data()

    for i in roi:
        data[data == int(i)] = 255

    data[data < 255] = 0

    recon = nib.Nifti1Image(data.astype(np.int8), nii._affine)
    nib.save(recon, output)

def parse_args():
    parser = argparse.ArgumentParser(description='Create mask using ROI IDs from BrainSuite.')
    parser.add_argument('inputFile', help='Input label volume.')
    parser.add_argument('--roi', help='ROI label numbers you would like to convert to 255.',
                       nargs="+")

    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    fileprefix = args.inputFile.split('.')[0]
    nii = nib.load(args.inputFile)
    output=fileprefix + '.pvc.edge.mask.nii.gz'

    data = nii.get_data()

    for i in args.roi:
        data[data == int(i)] = 255

    data[data < 255] = 0

    recon = nib.Nifti1Image(data.astype(np.int8), nii._affine)
    nib.save(recon, output)

if __name__ == '__main__':
 main()
