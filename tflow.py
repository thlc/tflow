#!/usr/bin/env python3
# coding: utf8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import argparse
import tempfile
import sys
import os
import sqlite3
import requests
import re
import time
import xml.dom.minidom
from xml.dom.minidom import parse
from time import mktime
from datetime import datetime
from dateutil.parser import parse
from bs4 import BeautifulSoup

# loglevels
DEBUG    = 3
INFO     = 2
WARNING  = 1
ERROR    = 0

baseurl = "http://diffusion-numerique.info-routiere.gouv.fr/tipitrafic/"
args = None

def die(err):
    print(err)
    sys.exit(42)

# fixme level
def log(level, msg):
    print(msg)

def init_workdir(args):
    # sqlite + RRD init
    if os.path.isdir(args.workdir):
        die("fatal: workdir already exists")
    os.mkdir(args.workdir) and log(DEBUG, "created workdir %s" % args.workdir)
    os.mkdir(args.workdir + '/rrd') and log (DEBUG, "created rrd subdir")
    conn = sqlite3.connect(args.workdir + '/tflow.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE timestamp (last DATETIME)''')
    c.execute('''INSERT INTO timestamp (last) VALUES (DATETIME('1970-01-01 00:00:00'))''')
    conn.commit()
    conn.close()
    log(DEBUG, "created SQLite database successfully")

def init_rrd(args, sensor_name):
    # init args.workdir+"/rrd/"+${sensor_name}.rrd
    True


# get the last timestamp that we processed
def get_last_ts():
    conn = sqlite3.connect(args.workdir + '/tflow.db')
    c = conn.cursor()
    c.execute('''SELECT last FROM timestamp;''')
    r = c.fetchone()
    conn.commit()
    conn.close()
    return parse(r[0])

def process_measurement(m, ts):
    sensor = m.getElementsByTagName('predefinedLocationReference')[0].getAttribute('id')
    flow = m.getElementsByTagName('vehicleFlowRate')[0].firstChild.data
    occupancy = m.getElementsByTagName('percentage')[0].firstChild.data 
    speed = m.getElementsByTagName('speed')[0].firstChild.data 

    print('sensor: %s flow: %s  occ: %s  speed: %s' % (sensor, flow, occupancy, speed))

# process a single DATEX2 file into RRD
def process_file(file):
    dom = xml.dom.minidom.parseString(file)

    pub = dom.getElementsByTagName('payloadPublication')[0]
    pubtime = (pub.getElementsByTagName('publicationTime'))[0].firstChild.data
    print("pubtime: %s" % pubtime)
    for child in pub.childNodes:
        if child.nodeType == child.ELEMENT_NODE and child.tagName == 'siteMeasurements':
            process_measurement(child, pubtime)

    True

def fetch_sixmin(sixmin_url):
    print("working on " + sixmin_url)
    xml = requests.get(sixmin_url, auth=(args.user, args.password)).text
    process_file(xml)
    sys.exit(0) # tmp

def fetch_day(url, last_ts):
    print("working on " + url)
    day = get_page_contents(url, '.xml')
    for sixmin in day:
        m = re.search('.*/frmar_DataTR_([0-9-_]+)\.xml$', sixmin)
        if m == None:
            continue
        else:
            ts = m.group(1)
            parsed_ts = datetime.fromtimestamp(mktime(time.strptime(ts, "%Y%m%d_%H%M%S")))
            if parsed_ts > last_ts:
                fetch_sixmin(sixmin)
            else:
                print("skipping sixmin " + ts)


# fetch all the missing data
def fetch_data(network = 'TraficMarius'):
    last_ts = get_last_ts()

    # get all directories from the root
    basedir_days = get_page_contents(baseurl + network, '/')

    for day in basedir_days:
        m = re.search('.*/([0-9-_]+)/$', day)
        if m == None:
            continue
        else:
            day_ts = m.group(1)
            # 2018-07-25_09
            parsed_ts = datetime.fromtimestamp(mktime(time.strptime(day_ts, '%Y-%m-%d_%H')))
            if parsed_ts > last_ts:
                fetch_day(day, last_ts)
            else:
                print("skipping " + day_ts)


# parses the output of an Apache DirectoryIndex page
# returns an array of links
def get_page_contents(url, ext):
    page = requests.get(url, auth=(args.user, args.password)).text
    soup = BeautifulSoup(page, 'html.parser')
    return [ url + '/' + node.get('href') for node in soup.find_all('a') if node.get('href').endswith(ext) ]



def main():
    parser = argparse.ArgumentParser(description='Traffic data analyser')
    parser.add_argument('-u', '--user', help='username', type=str, action='store')
    parser.add_argument('-p', '--password', help='password', type=str, action='store')
    parser.add_argument('-d', '--workdir', default='./data', type=str, action='store')
    parser.add_argument('-I', '--init', action='store_true')
    parser.add_argument('-C', '--catchup', help='catchup with old data', action='store_true')

    global args
    args = parser.parse_args()

    if args.init:
        init_workdir()
        sys.exit(0)

    if not os.path.isdir(args.workdir):
        log("error: %s doesn't exist" % args.workdir)
        sys.exit(1)

    fetch_data()

if __name__ == "__main__":
    main()
