#!/usr/bin/env python3
# coding: utf8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

# Copyright (c) 2018, Thomas Lecomte <thomas@netnix.in>
# All rights reserved.

import argparse
import tempfile
import sys
import os
import sqlite3
import requests
import re
import time
import rrdtool
import xml.dom.minidom
import strict_rfc3339

from xml.dom.minidom import parse
from time import mktime
from datetime import datetime
from dateutil.parser import parse
from bs4 import BeautifulSoup

# quick'n'dirty mapping for marseille
mapping=[ ('4', 'A50'),
          ('3', 'A50TC' ), # tronc commun (aubagne-marseille)
          ('1', 'A51' ),
          ('5', 'A55' ),
          ('7', 'A7S' ), # A7 jusqu'a ech A51
          ('8', 'A7TC' ), # A7 jusqu'a saint charles
          ('2', 'A507' ) # L2
        ]

# loglevels
DEBUG    = 3
INFO     = 2
WARNING  = 1
ERROR    = 0

loglevel = INFO

baseurl = "http://diffusion-numerique.info-routiere.gouv.fr/tipitrafic/"
args = None

def die(err):
    print(err)
    sys.exit(42)

# fixme level
def log(level, msg):
    global loglevel
    if level <= loglevel:
        print(msg)

def init_workdir():
    # sqlite + RRD init
    if os.path.isdir(args.workdir):
        die("fatal: workdir already exists")
    os.mkdir(args.workdir) and log(DEBUG, "created workdir %s" % args.workdir)
    os.mkdir(args.workdir + '/rrd') and log (DEBUG, "created rrd subdir")
    os.mkdir(args.workdir + '/graphs')
    conn = sqlite3.connect(args.workdir + '/tflow.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE timestamp (last INTEGER)''')
    c.execute('''INSERT INTO timestamp (last) VALUES (0)''')
    conn.commit()
    conn.close()
    log(DEBUG, "created SQLite database successfully")

# FIXME maintain one connection for the whole run

# get the last timestamp that we processed
def get_last_ts():
    conn = sqlite3.connect(args.workdir + '/tflow.db')
    c = conn.cursor()
    c.execute('''SELECT last FROM timestamp;''')
    r = c.fetchone()
    conn.commit()
    conn.close()
    return int(r[0])

def update_last_ts(ts):
    conn = sqlite3.connect(args.workdir + '/tflow.db')
    c = conn.cursor()
    c.execute("UPDATE timestamp SET last = %s" % ts)
    log(DEBUG, "[update_last_ts] updating to %s" % ts);
    conn.commit()
    conn.close()

def init_rrd(path, ts_start):
    log(DEBUG, "creating new RRD database (%s)" % path)
    rrdtool.create(path, '-b', ts_start,
                        '-s', '360',
                        'DS:vehicleFlow:GAUGE:360:0:10000',
                        'DS:occupancy:GAUGE:360:0:100',
                        'DS:speed:GAUGE:360:0:200',
                        'RRA:AVERAGE:0.8:1:240',
                        'RRA:AVERAGE:0.8:10:8100')

def update_rrd(sensor, ts, flow, occupancy, speed):
    rrdfilepath = args.workdir + '/rrd/' + sensor + '.rrd'
    if not os.path.isfile(rrdfilepath):
        # (minimum one second step)
        init_rrd(rrdfilepath, str(int(ts) - 1))
    log(DEBUG, "[%s] inserting data (%s,%s,%s) for ts %s" % (sensor, flow, occupancy, speed, ts))
    rrdtool.update(rrdfilepath, "%s:%s:%s:%s" % (ts, flow, occupancy, speed)) 

def process_measurement(m, ts):
    sensor = m.getElementsByTagName('predefinedLocationReference')[0].getAttribute('id')
    flow = int(m.getElementsByTagName('vehicleFlowRate')[0].firstChild.data)
    occupancy = float(m.getElementsByTagName('percentage')[0].firstChild.data)
    speed = float(m.getElementsByTagName('speed')[0].firstChild.data)

    s_prettyfwy = '<unknown>'

    s = re.search('([A-Za-z]{2})([0-9])([0-9]{2})\.([a-zA-Z][0-9])', sensor)
    if s == None:
        print("unmatched %s" % sensor)
    else:
        s_region = s.group(1)
        s_fwy = s.group(2)
        s_dept = s.group(3)
        s_sid = s.group(4)

        for m in mapping:
            if m[0] == s_fwy:
                s_prettyfwy = m[1]

    log(DEBUG, 'sensor: %s (%s) flow: %i  occ: %f  speed: %f' % (sensor, s_prettyfwy, flow, occupancy, speed))
    update_rrd(sensor, ts, flow, occupancy, speed)

# process a single DATEX2 file into RRD
def process_file(file):
    dom = xml.dom.minidom.parseString(file)

    pub = dom.getElementsByTagName('payloadPublication')[0]
    pubtime = (pub.getElementsByTagName('publicationTime'))[0].firstChild.data
    ts = str(int(strict_rfc3339.rfc3339_to_timestamp(pubtime)))
    update_last_ts(ts)
    log(INFO, "processing publication, timestamp [%s]" % (pubtime))
    for child in pub.childNodes:
        if child.nodeType == child.ELEMENT_NODE and child.tagName == 'siteMeasurements':
            process_measurement(child, ts)

def fetch_sixmin(sixmin_url):
    log(DEBUG, "[fetch_sixmin] fetching %s" % sixmin_url)
    xml = requests.get(sixmin_url, auth=(args.user, args.password)).text
    process_file(xml)

def fetch_day(url, last_ts):
    print("working on " + url)
    day = get_page_contents(url, '.xml')
    for sixmin in day:
        m = re.search('.*/frmar_DataTR_([0-9-_]+)\.xml$', sixmin)
        if m == None:
            continue
        else:
            ts = m.group(1)
            parsed_ts = int(mktime(time.strptime(ts, "%Y%m%d_%H%M%S")))
            log(DEBUG, "parsed_ts: %i last_ts: %i" % (parsed_ts, last_ts))
            if parsed_ts > last_ts:
                fetch_sixmin(sixmin)
            else:
                log(DEBUG, "[fetch_day] skipping sixmin " + ts)


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
            # 2018-07-25_09 - we append the minute '59' to get the whole hour
            parsed_ts = int(mktime(time.strptime(day_ts + '-59', '%Y-%m-%d_%H-%M')))
            log(DEBUG, "parsed_ts: %i last_ts: %i" % (parsed_ts, last_ts))
            if parsed_ts >= last_ts:
                fetch_day(day, last_ts)
            else:
                log(DEBUG, "[fetch_data] skipping " + day_ts)


# parses the output of an Apache DirectoryIndex page
# returns an array of links
def get_page_contents(url, ext):
    page = requests.get(url, auth=(args.user, args.password)).text
    soup = BeautifulSoup(page, 'html.parser')
    return [ url + '/' + node.get('href') for node in soup.find_all('a') if node.get('href').endswith(ext) ]

def gen_live_stats(rrdfile, sensor_name):
    m = rrdtool.graph('/dev/null', '--end', 'now', '--start', 'end-1h',
                  "DEF:vehicleFlow=%s:vehicleFlow:AVERAGE:step=360" % rrdfile,
                  "DEF:speed=%s:speed:AVERAGE:step=360" % rrdfile,
                  "DEF:occupancy=%s:occupancy:AVERAGE:step=360" % rrdfile,
                  "VDEF:vehicleLast=vehicleFlow,LAST",
                  "VDEF:occupancyLast=occupancy,LAST",
                  "VDEF:speedLast=speed,LAST",
                  "PRINT:vehicleLast:%.0lf",
                  "PRINT:occupancyLast:%.0lf",
                  "PRINT:speedLast:%.0lf")

    # m == (0, 0, ['289', '13', '75'])
    with open(args.outputdir + '/data/' + sensor_name, 'w') as f:
        f.write("%s %s %s\n" % (m[2][0], m[2][1], m[2][2]))

def draw_graph(rrdfile, sensor_name):
    g_range = '2d'
    height = '200'
    width = '400'
    scale = 0.03
    rrdtool.graph(args.outputdir + "/graphs/%s.png" % sensor_name,
                    '--end', 'now', '--start', "end-%s" % g_range,
                    '-E', '-N', '-h', height, '-l', '0', '-t',
                    sensor_name + ' | ' + str(time.strftime("%Y-%m-%d %H:%M", time.localtime())),
                    '-v', 'veh/h', '-X', '0', '-T' '20', '--right-axis', "%f:0" % scale,
                    '--right-axis-label', 'km/h | %',
		    "DEF:vehicleFlow=%s:vehicleFlow:AVERAGE:step=360" % rrdfile,
		    "DEF:speed=%s:speed:AVERAGE:step=360" % rrdfile,
                    "DEF:occupancy=%s:occupancy:AVERAGE:step=360" % rrdfile,
		    'CDEF:scaledFlow=vehicleFlow,10,*',
		    "CDEF:scaledSpeed=speed,%f,/" % scale,
                    "CDEF:scaledOccupancy=occupancy,%f,/" % scale,
		    'VDEF:vehicleAvg=vehicleFlow,AVERAGE',
		    'VDEF:vehicleMin=vehicleFlow,MINIMUM',
		    'VDEF:vehicleMax=vehicleFlow,MAXIMUM',
		    'VDEF:vehicleLast=vehicleFlow,LAST',
		    'VDEF:speedAvg=speed,AVERAGE',
		    'VDEF:speedMin=speed,MINIMUM',
		    'VDEF:speedMax=speed,MAXIMUM',
		    'VDEF:speedLast=speed,LAST',
		    'VDEF:occupancyAvg=occupancy,AVERAGE',
		    'VDEF:occupancyMin=occupancy,MINIMUM',
		    'VDEF:occupancyMax=occupancy,MAXIMUM',
		    'VDEF:occupancyLast=occupancy,LAST',
		    'LINE1:scaledFlow#0000FF:vehicleFlow    ',
		    'LINE1:scaledSpeed#FF0000:speed    ',
		    'LINE1:scaledOccupancy#00FF00:occupancy    \c',
		    'GPRINT:vehicleAvg:avg %4.0lf0 veh/h\t',
		    'GPRINT:vehicleMin:min %4.0lf0 veh/h\t',
		    'GPRINT:vehicleMax:max %4.0lf0 veh/h\t',
		    'GPRINT:vehicleLast:last %4.0lf0 veh/h\l',
		    'GPRINT:speedAvg:avg %4.0lf km/h \t',
		    'GPRINT:speedMin:min %4.0lf km/h \t',
		    'GPRINT:speedMax:max %4.0lf km/h \t',
		    'GPRINT:speedLast:last %4.0lf km/h \l',
		    'GPRINT:occupancyAvg:avg %4.0lf %%\t',
		    'GPRINT:occupancyMin:min %4.0lf %%\t',
		    'GPRINT:occupancyMax:max %4.0lf %%\t',
		    'GPRINT:occupancyLast:last %4.0lf %%     ')

def draw_graphs():
    for filename in os.listdir(args.workdir + '/rrd'):
        if filename.endswith('.rrd'):
            fullpath = args.workdir + '/rrd/' + filename;
            m = re.search('(.*)\.rrd$', filename)
            sensor_name = m.group(1).upper()
            log(DEBUG, "[draw_graphs] drawing %s" % filename)
            draw_graph(fullpath, sensor_name)
            log(DEBUG, "[draw_graphs] gen_live_stats %s" % filename)
            gen_live_stats(fullpath, sensor_name)
        else:
            continue


def main():
    parser = argparse.ArgumentParser(description='Traffic data analyser')
    parser.add_argument('-u', '--user', help='username', type=str, action='store')
    parser.add_argument('-p', '--password', help='password', type=str, action='store')
    parser.add_argument('-d', '--workdir', default='./data', type=str, action='store')
    parser.add_argument('-I', '--init', action='store_true')
    parser.add_argument('-C', '--catchup', help='catchup with old data', action='store_true')
    parser.add_argument('-g', '--graph', help='draw graphs', action='store_true')
    parser.add_argument('-G', '--graphonly', help='draw graphs only', action='store_true')
    parser.add_argument('-D', '--debug', help='debug', action='store_true')
    parser.add_argument('-o', '--outputdir', help='output dir for graphs and stats', action='store', type=str)

    global args
    args = parser.parse_args()

    global loglevel
    if args.debug:
        loglevel = DEBUG

    if args.init:
        init_workdir()
        sys.exit(0)

    if not os.path.isdir(args.workdir):
        log("error: %s doesn't exist" % args.workdir)
        sys.exit(1)

    if not args.graphonly:
        fetch_data()

    if args.graph:
        draw_graphs()

if __name__ == "__main__":
    main()
