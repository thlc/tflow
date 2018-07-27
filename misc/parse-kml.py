#!/usr/bin/env python3
# coding: utf8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

# Copyright (c) 2018, Thomas Lecomte <thomas@netnix.in>
# All rights reserved.

import argparse
import tempfile
import sys
import os
import requests
import re
import time
import xml.dom.minidom

from xml.dom.minidom import parse

def process_placemark(sensor):
    name = sensor.getElementsByTagName('name')[0].firstChild.data
    coords = sensor.getElementsByTagName('coordinates')[0].firstChild.data.strip()

    m = re.search('([A-Z][0-9])([A-Z])', name)
    realname = "L01.M%s13.%s" % (m.group(1), m.group(2))

# A502 1=aubagne 2=marseille
# A51  1=aix 2=marseille
# A50TC 1=aubagne 2=marseille
# A501  1=auriol 2=aubagne/mrs
# A7S   1=marseille 2=lyon
# A7TC  1=marseille 2=lyon/aix
# A55L  1=martigues 2=marseille


    print("%s1: %s" % (realname, coords))
    print("%s2: %s" % (realname, coords))


def parse_kml(file):
    dom = xml.dom.minidom.parse(file)

    for sensor in dom.getElementsByTagName('Placemark'):
        process_placemark(sensor)

def main():
    parser = argparse.ArgumentParser(description='Traffic data analyser')
    parser.add_argument('-f', '--file', help='file to parse', type=str, action='store', required=True)

    args = parser.parse_args()

    parse_kml(args.file)

if __name__ == "__main__":
    main()
