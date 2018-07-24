#!/usr/bin/env python3
# coding: utf8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import argparse
import tempfile
import sys
import os
import sqlite3

baseurl = "http://diffusion-numerique.info-routiere.gouv.fr/tipitrafic/TraficMarius/"

def die(err):
    print err
    sys.exit(42)

def log(level, msg):
    print msg

def init_workdir(args):
    # sqlite + RRD init
    if os.path.isdir(args.workdir):
        die("fatal: workdir already exists")
    os.mkdir(args.workdir) and log(DEBUG, "created workdir %s" % args.workdir)
    os.mkdir(args.workdir + '/rrd') and log (DEBUG, "created rrd subdir")
    conn = sqlite3.connect(args.workdir + '/tflow.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE timestamp (last DATETIME)''')
    conn.commit()
    conn.close()
    log(DEBUG, "created SQLite database successfully")

def init_rrd(args, sensor_name):
    # init args.workdir+"/rrd/"+${sensor_name}.rrd
    True

def fetch_data():
    # fetch the stuff
    True

def process_file():
    # process a single DATEX2 file into RRD
    True


def main():
    parser = argparse.ArgumentParser(description='Traffic data analyser')
    parser.add_argument('-u', '--user', help='username', required=True, type=str, action='store')
    parser.add_argument('-p', '--password', help='password', required=True, type=str, action='store')
    parser.add_argument('-d', '--workdir', default='./data', type=str, action='store')
    parser.add_argument('-I', '--init', action='store_true')
    parser.add_argument('-C', '--catchup', help='catchup with old data', action='store_true')

    args = parser.parse_args()

    if args.init:
        init_workdir(args)
        sys.exit(0)

    if not os.path.isdir(args.workdir):
        log("error: %s doesn't exist" % args.workdir)
        sys.exit(1)

    fetch_data(parser)

if __name__ == "__main__":
    main()
