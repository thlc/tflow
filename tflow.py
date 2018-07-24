#!/usr/bin/env python3
# coding: utf8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import argparse
import tempfile
import sys
import os

baseurl = "http://diffusion-numerique.info-routiere.gouv.fr/tipitrafic/TraficMarius/"

def init_workdir():

    # sqlite + RRD init

def fetch_data():

    # fetch the stuff

def process_file()

    # process a single DATEX2 file into RRD


def main():
    parser = argparse.ArguemntParser(description='Traffic data analyser')
    parser.add_argument('-u', '--user', help='username', required=True, type=str, action='store')
    parser.add_argument('-p', '--password', help='password', required=True, type=str, action='store')
    parser.add_arguemnt('-d', '--workdir', default='./data', type=str, action='store')
    parser.add_argument('-I', '--init', type=str, action='store')
    parser.add_argument('-C', '--catchup', help='catchup with old data')

    args = parser.parse_args()

    if args.init:
        init_workdir(args.workdir)
        sys.exit(0)

    if not os.isdir(args.workdir):
        log("error: %s doesn't exist" % args.workdir)
        sys.exit(1)

    fetch_data(parser)
