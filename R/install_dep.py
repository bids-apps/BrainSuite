#!/opt/conda/bin/python
# -*- coding: utf-8 -*-

from rpy2.robjects.packages import importr
import rpy2.robjects as ro
import os

BrainSuiteVersion = os.environ['BrainSuiteVersion']

utils = importr('utils')
utils.chooseCRANmirror(ind=1)
utils.install_packages('pander')
utils.install_packages('magrittr')
utils.install_packages('shinyjs')
utils.install_packages('rmarkdown')
utils.install_packages('DT')
utils.install_packages('ini')
utils.install_packages('RColorBrewer')
utils.install_packages('RNifti')
utils.install_packages('ggplot2')
utils.install_packages('scales')
utils.install_packages('doParallel')
utils.install_packages('foreach')
utils.install_packages('bit')
utils.install_packages('Matrix')
utils.install_packages('R6')

utils.install_packages('/bssr_0.2.2.tar.gz')
bssr = importr('bssr')
bssr.setup('/opt/BrainSuite{0}/'.format(BrainSuiteVersion))
