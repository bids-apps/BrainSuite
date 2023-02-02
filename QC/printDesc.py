# -*- coding: utf-8 -*-
'''
Copyright (C) 2023 The Regents of the University of California

Created by Yeun Kim

This file is part of the BrainSuite BIDS App

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
import json

def printDesc(dataDesc, specs):

    struct= '<h3><b>BSE</b></h3>\n' \
            'autoBSE = {autoBSE}<br>\n' \
            'diffusion iterations= = {diffusionIterations}<br>\n' \
            'diffusionc constant = {diffusionConstant}<br>\n' \
            'edgeDetection constant = {edgeDetectionConstant}<br>\n' \
            'skip BSE = {skipBSE}<br>\n ' \
            '<h3><b>BFC</b></h3>\n' \
            'iterative mode = {iterativeMode}<br>\n ' \
            '<h3><b>PVC</b></h3>\n spatial prior = {spatialPrior}<br>\n ' \
            '<h3><b>Cerebrum</b></h3>\n' \
            'cost function = {costFunction}<br>\n use centroids = {useCentroids}<br>\n ' \
            'linear convergence = {linearConvergence}<br>\n' \
            'warp convergence = {warpConvergence}<br>\n warp level = {warpLevel}<br>\n ' \
            '<h3><b>Inner cortex</b></h3>\n tissue frraction threshold = {tissueFractionThreshold}<br>\n ' \
            '<h3><b>SVReg</b></h3>\n' \
            'atlas = {atlas}<br>\n single thread = {singleThread}<br>\n cache folder = {cacheFolder}<br>\n' \
            '<h3><b>Smoothing level</b></h3>\n ' \
            'smooth surf = {smoothSurf}<br>' \
            'smooth vol = {smoothVol}<br>'.format(
        autoBSE=specs.autoParameters,
        diffusionIterations=specs.diffusionIterations,
        diffusionConstant=specs.diffusionConstant,
        edgeDetectionConstant=specs.edgeDetectionConstant,
        skipBSE=specs.skipBSE,
        iterativeMode=specs.iterativeMode,
        spatialPrior=specs.spatialPrior,
        costFunction=specs.costFunction,
        useCentroids=specs.useCentroids,
        linearConvergence=specs.linearConvergence,
        warpConvergence=specs.warpConvergence,
        warpLevel=specs.warpLevel,
        tissueFractionThreshold=specs.tissueFractionThreshold,
        atlas=specs.atlas,
        singleThread=specs.singleThread,
        cacheFolder=specs.cache,
        smoothSurf = specs.smoothsurf,
        smoothVol = specs.smoothvol

    )

    print(struct)

    datadesc = json.load(open(dataDesc))


    for key, value in datadesc.items():
        desc = '<h3><b>{0}</b></h3>\n{1}<br>\n'.format(key, value)
        print(desc)