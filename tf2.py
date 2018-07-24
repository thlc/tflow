#!/usr/bin/env python3
# coding: utf8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import argparse
import tempfile

baseurl = "http://diffusion-numerique.info-routiere.gouv.fr/tipitrafic/TraficMarius/"

def main():
    parser = argparse.ArguemntParser(description='Traffic data analyser')
    parser.add_argument('-u', '--user', help='username', required=True, type=str, action='store')
    parser.add_argument('-p', '--password', help='password', required=True, type=str, action='store')
    parser.add_arguemnt('-d', '--workdir', default='./data', type=str, action='store')
    parser.add_argument('-I', '--init', type=str, action='store')

    args = parser.parse_args()

#   if ! -d $workdir then init();
#   if args.-I then init();

    fetch_data(parser)
