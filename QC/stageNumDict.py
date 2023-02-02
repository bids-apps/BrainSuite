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
from collections import OrderedDict

stageNumDict = OrderedDict({
    'BSE': 1,
    'BFC': 2,
    'PVC': 3,
    'CEREBRO': 4,
    'CORTEX': 5,
    'SCRUBMASK': 6,
    'TCA': 7,
    'DEWISP': 8,
    'DFS': 9,
    'PIALMESH': 10,
    'HEMISPLIT': 11,
    'THICKPVC' : 12,

    'SVREG': 13,
    'SMOOTHSURFLEFT': 14,
    'SMOOTHSURFRIGHT': 15,
    'SMOOTHVOLJAC': 16,

    'BDP': 17,
    'APPLYMAPFA' : 18,
    'APPLYMAPMD' : 19,
    'APPLYMAPAXIAL' : 20,
    'APPLYMAPRADIAL': 21,
    'APPLYMAPMADC': 22,
    'APPLYMAPFRTGFA': 23,

    'SMOOTHVOLFA' : 24,
    'SMOOTHVOLMD' : 25,
    'SMOOTHVOLAXIAL' : 26,
    'SMOOTHVOLRADIAL': 27,
    'SMOOTHVOLMADC': 28,
    'SMOOTHVOLFRTGFA': 29,

    'BFP': 30
})