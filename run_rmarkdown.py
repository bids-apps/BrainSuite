#!/usr/local/miniconda/bin/python
# -*- coding: utf-8 -*-
'''
Copyright (C) 2023 The Regents of the University of California

Created by Yeun Kim

This file is part of the BrainSuite BIDS App.

The BrainSuite BIDS App is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public License
as published by the Free Software Foundation, version 2.1.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
'''

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