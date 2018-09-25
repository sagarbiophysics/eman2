#
# Copyright (C) 2016  Thorsten Wagner (thorsten.wagner@mpi-dortmund.mpg.de)
#

# source code in this file under either license. However, note that the
# complete EMAN2 and SPARX software packages have some GPL dependencies,
# so you are responsible for compliance with the licenses of these packages
# if you opt to use BSD licensing. The warranty disclaimer below holds
# in either instance.
#
# This complete copyright notice must be included in any revised version of the
# source code. Additional authorship citations may be added, but existing
# author citations must be preserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

from __future__ import print_function
import argparse
from json import dump
import subprocess


argparser = argparse.ArgumentParser(
    description='crYOLO boxmanager',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

argparser.add_argument(
    'target_dir',
    type=str,
    help='Specifiy the path to your config file.')

argparser.add_argument(
    '--box_dir',
    type=str,
    help='Specifiy the path to your config file.')

def main():
    # Read arguments
    args = argparser.parse_args()

    target_dir = args.target_dir
    box_dir = args.box_dir
    call = ['python', 'cryolo_boxmanager.py']
    if target_dir:
        input_argument = "-i=" + str(target_dir)
        call.append(input_argument)
        if box_dir:
            box_argument = "-b=" + str(box_dir)
            call.append(box_argument)
    subprocess.check_call(call)


