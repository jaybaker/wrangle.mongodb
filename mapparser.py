#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Your task is to use the iterative parsing to process the map file and
find out not only what tags are there, but also how many, to get the
feeling on how much of which data you can expect to have in the map.
The output should be a dictionary with the tag name as the key
and number of times this tag can be encountered in the map as value.

Note that your code will be tested with a different data file than the 'example.osm'
"""
import sys
import xml.etree.ElementTree as ET
import pprint

TEST_OSMFILE = 'mapparser.example.osm'

def count_tags(filename):
    # YOUR CODE HERE
    counts = {}
    tree = ET.parse(filename)
    root = tree.getroot()
    print 'root is %s' % root.tag
    #counts[root.tag] = 1 # this counts the root
    for child in root.iter():
        counts.setdefault(child.tag, 0)
        counts[child.tag] += 1
    
    return counts


def main(fname, test=True):
    tags = count_tags(fname)
    pprint.pprint(tags)
    if test:
        assert tags == {'bounds': 1,
                        'member': 3,
                        'nd': 4,
                        'node': 20,
                        'osm': 1,
                        'relation': 1,
                        'tag': 7,
                        'way': 1}

    

if __name__ == "__main__":
    test, fname = True, TEST_OSMFILE
    if len(sys.argv) == 2 and sys.argv[1] != TEST_OSMFILE:
        test, fname = False, sys.argv[1]
    main(fname, test=test)
