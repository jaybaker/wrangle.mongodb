#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import xml.etree.ElementTree as ET
import pprint
import re
"""
Your task is to explore the data a bit more.
The first task is a fun one - find out how many unique users
have contributed to the map in this particular area!

The function process_map should return a set of unique user IDs ("uid")
"""

TEST_OSMFILE = 'users.example.osm'

def get_user(element):
    if 'user' in element.attrib:
        return element.attrib['user']
    return


def process_map(filename):
    users = set()
    for _, element in ET.iterparse(filename):
        user = get_user(element)
        if user:
            users.add(user)
    return users

def main(fname, test=True):
    users = process_map(fname)
    pprint.pprint(users)
    if test:
        assert len(users) == 6
    print '%i distinct users have contributed' % len(users)

if __name__ == "__main__":
    test, fname = True, TEST_OSMFILE
    if len(sys.argv) == 2 and sys.argv[1] != TEST_OSMFILE:
        test, fname = False, sys.argv[1]
    main(fname, test=test)
