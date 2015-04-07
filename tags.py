#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import xml.etree.ElementTree as ET
import pprint
import re
"""
Your task is to explore the data a bit more.
Before you process the data and add it into MongoDB, you should
check the "k" value for each "<tag>" and see if they can be valid keys in MongoDB,
as well as see if there are any other potential problems.

We have provided you with 3 regular expressions to check for certain patterns
in the tags. As we saw in the quiz earlier, we would like to change the data model
and expand the "addr:street" type of keys to a dictionary like this:
{"address": {"street": "Some value"}}
So, we have to see if we have such tags, and if we have any tags with problematic characters.
Please complete the function 'key_type'.
"""

TEST_OSMFILE = 'tags.example.osm'

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')


def key_type(element, keys):
    if element.tag == "tag":
        # YOUR CODE HERE
        key = element.attrib['k']
        # check each character for problem chars
        for ch in key:
            if problemchars.match(ch):
                keys['problemchars'] += 1
                break
        else:
            if lower_colon.match(key):
                keys['lower_colon'] += 1
            elif lower.match(key):
                keys['lower'] += 1
            else:
                keys['other'] += 1
        
    return keys

def process_map(filename):
    # counters for different types of issues
    keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)

    return keys



def main(fname, test=True):
    # You can use another testfile 'map.osm' to look at your solution
    # Note that the assertions will be incorrect then.
    keys = process_map(fname)
    pprint.pprint(keys)
    if test:
        assert keys == {'lower': 5, 'lower_colon': 0, 'other': 1, 'problemchars': 1}

if __name__ == "__main__":
    test, fname = True, TEST_OSMFILE
    if len(sys.argv) == 2 and sys.argv[1] != TEST_OSMFILE:
        test, fname = False, sys.argv[1]
    main(fname, test=test)
