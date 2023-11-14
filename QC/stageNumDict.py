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

    'BDPMASK': 17,
    'EDDY': 18,
    'BDP': 19,
    'APPLYMAPFA' : 20,
    'APPLYMAPMD' : 21,
    'APPLYMAPAXIAL' : 22,
    'APPLYMAPRADIAL': 23,
    'APPLYMAPMADC': 24,
    'APPLYMAPFRTGFA': 25,

    'SMOOTHVOLFA' : 26,
    'SMOOTHVOLMD' : 27,
    'SMOOTHVOLAXIAL' : 28,
    'SMOOTHVOLRADIAL': 29,
    'SMOOTHVOLMADC': 30,
    'SMOOTHVOLFRTGFA': 31,

    'BFP': 32
})

stageGroups = {
    'CSE': [
        'BSE',
        'BFC',
        'PVC',
        'CEREBRO',
        'CORTEX',
        'SCRUBMASK',
        'TCA',
        'DEWISP',
        'DFS',
        'PIALMESH',
        'HEMISPLIT',
        'THICKPVC'
            ],
    'SVREG': [
        'SVREG',
        'SMOOTHSURFLEFT',
        'SMOOTHSURFRIGHT',
        'SMOOTHVOLJAC'
    ],
    'BDP': [
        'BDPMASK',
        'EDDY',
        'BDP'
    ],
    'FSLEDDY': [
        'BDPMASK',
        'EDDY'
    ],
    'SVREG+BDP': [
        'APPLYMAPFA',
        'APPLYMAPMD',
        'APPLYMAPAXIAL' ,
        'APPLYMAPRADIAL',
        'APPLYMAPMADC',
        'APPLYMAPFRTGFA',
        'SMOOTHVOLFA',
        'SMOOTHVOLMD',
        'SMOOTHVOLAXIAL',
        'SMOOTHVOLRADIAL',
        'SMOOTHVOLMADC',
        'SMOOTHVOLFRTGFA'
    ],
    'BFP': [
        'BFP'
    ]
}
