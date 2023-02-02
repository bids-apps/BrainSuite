#!/usr/bin/env bash

# Copyright (C) 2023 The Regents of the University of California
#
# Created by Yeun Kim
#
# This file is part of the BrainSuite BIDS App
#
# The BrainSuite BIDS App is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation, version 2.1.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA


args=("$@")
i=${#args[*]}
inputFile="${args[0]}"
rois="${args[@]:1:$i}"

python /BrainSuite/QC/makeMask.py $inputFile --roi $rois
