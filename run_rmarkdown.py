#!/opt/conda/bin/python
# -*- coding: utf-8 -*-

import sys
import rpy2
from rpy2.robjects.packages import importr
import rpy2.robjects as ro
import warnings
from rpy2.rinterface import RRuntimeWarning
warnings.filterwarnings("ignore", category=RRuntimeWarning)

def run_rmarkdown(rmdfile):
    rmd = importr('rmarkdown')
    rmd.render(rmdfile)