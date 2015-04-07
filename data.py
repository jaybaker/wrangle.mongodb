#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import xml.etree.ElementTree as ET
import pprint
import re
import codecs
import json
"""
Your task is to wrangle the data and transform the shape of the data
into the model we mentioned earlier. The output should be a list of dictionaries
that look like this:

{
"id": "2406124091",
"type: "node",
"visible":"true",
"created": {
          "version":"2",
          "changeset":"17206049",
          "timestamp":"2013-08-03T16:43:42Z",
          "user":"linuxUser16",
          "uid":"1219059"
        },
"pos": [41.9757030, -87.6921867],
"address": {
          "housenumber": "5157",
          "postcode": "60625",
          "street": "North Lincoln Ave"
        },
"amenity": "restaurant",
"cuisine": "mexican",
"name": "La Cabana De Don Luis",
"phone": "1 (773)-271-5176"
}

You have to complete the function 'shape_element'.
We have provided a function that will parse the map file, and call the function with the element
as an argument. You should return a dictionary, containing the shaped data for that element.
We have also provided a way to save the data in a file, so that you could use
mongoimport later on to import the shaped data into MongoDB. 

Note that in this exercise we do not use the 'update street name' procedures
you worked on in the previous exercise. If you are using this code in your final
project, you are strongly encouraged to use the code from previous exercise to 
update the street names before you save them to JSON. 

In particular the following things should be done:
- you should process only 2 types of top level tags: "node" and "way"
- all attributes of "node" and "way" should be turned into regular key/value pairs, except:
    - attributes in the CREATED array should be added under a key "created"
    - attributes for latitude and longitude should be added to a "pos" array,
      for use in geospacial indexing. Make sure the values inside "pos" array are floats
      and not strings. 
- if second level tag "k" value contains problematic characters, it should be ignored
- if second level tag "k" value starts with "addr:", it should be added to a dictionary "address"
- if second level tag "k" value does not start with "addr:", but contains ":", you can process it
  same as any other tag.
- if there is a second ":" that separates the type/direction of a street,
  the tag should be ignored, for example:

<tag k="addr:housenumber" v="5158"/>
<tag k="addr:street" v="North Lincoln Avenue"/>
<tag k="addr:street:name" v="Lincoln"/>
<tag k="addr:street:prefix" v="North"/>
<tag k="addr:street:type" v="Avenue"/>
<tag k="amenity" v="pharmacy"/>

  should be turned into:

{...
"address": {
    "housenumber": 5158,
    "street": "North Lincoln Avenue"
}
"amenity": "pharmacy",
...
}

- for "way" specifically:

  <nd ref="305896090"/>
  <nd ref="1719825889"/>

should be turned into
"node_refs": ["305896090", "1719825889"]
"""

TEST_OSMFILE = 'data.example.osm'

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]
ADDRESS_MARKER = 'addr:'

streettype_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", 
    "Square", "Lane", "Road", "Trail", "Parkway", "Commons"]

BETTER_STREET_NAMES = {}
PREFIX_MAP = (('St', 'Street'), ('Rd', 'Road'), ('Dr', 'Drive'), 
    ('Ave', 'Avenue'), ('Ln', 'Lane'))
# add a '.' to all the abbreviations
for prefix_map in PREFIX_MAP:
    BETTER_STREET_NAMES[prefix_map[0]] = prefix_map[1]
    BETTER_STREET_NAMES[prefix_map[0] + '.'] = prefix_map[1]

STREET_DIRECTIONS = {}
DIRECTIONS_MAP = (('N', 'North'), ('W', 'West'), 
        ('S', 'South'), ('E', 'East'))
for mapping in DIRECTIONS_MAP:
    STREET_DIRECTIONS[mapping[0] + ' '] = mapping[1] + ' '
    STREET_DIRECTIONS[mapping[0] + '.' + ' '] = mapping[1] + ' '

city_has_state_re = re.compile(r'\w*(,?\s+[Tt][Xx])$|\w*(,?\s+[Tt]exas)$') 


class ElementShaper(object):
    def __init__(self, element):
        self.element = element

    def lat_lon(self, key, value):
        if key in ('lat', 'lon'):
            val = float(value)
            if key == 'lat': 
                self.lat = val
            elif key == 'lon':
                self.lon = val
            return True
        return False

    def created_property(self, key, value):
        if key in CREATED:
            if not hasattr(self, 'created'):
                self.created = {}
            self.created[key] = value
            return True
        return False

    def update_website(self, url):
        normalized_url = url
        if not url.startswith('http://'):
            normalized_url += 'http://'
        return normalized_url

    def iterate_attributes(self):
        """ Iterate through all xml element attributes """
        for k, v in self.element.attrib.iteritems():
            if not self.lat_lon(k, v) and not self.created_property(k, v):
                if k == 'website':
                    self.node[k] = self.update_website(v)
                self.node[k] = v

        if hasattr(self, 'lat') and hasattr(self, 'lon'):
            self.node['pos'] = [self.lat, self.lon]
        self.node['created'] = self.created

    def update_street_name(self, name):
        for abbreviation, mapped_val in BETTER_STREET_NAMES.iteritems():
            if name.endswith(abbreviation):
                better_name = BETTER_STREET_NAMES[abbreviation]
                name = name.replace(abbreviation, better_name)

        for direction, mapped_val in STREET_DIRECTIONS.iteritems():
            if name.startswith(direction):
                better_name = STREET_DIRECTIONS[direction]
                name = name.replace(direction, better_name)
        return name

    def update_city_name(self, name):
        m = city_has_state_re.match(name)
        if m is not None:
            which_group = 1 if m.group(1) else 2
            old = name
            name = name.replace(m.group(which_group), '')
            print '%s replaced with %s' % (old,name)
        if not name.istitle():
            if name != 'McKinney': # sort of brute forcing this here
                old = name
                name = name.title()
                print '%s replaced with %s' % (old,name)
        return name

    def check_address(self, key, val):
        if not hasattr(self, 'address'):
            self.address = {}

        # if part of address
        if key.startswith(ADDRESS_MARKER):
            prop = key[len(ADDRESS_MARKER):]
            if ':' in prop: 
                # extended address; not interested
                pass
            else:
                if prop == 'street': # if is street name
                    self.address[prop] = self.update_street_name(val)
                elif prop == 'city':
                    self.address[prop] = self.update_city_name(val)
                else:
                    self.address[prop] = val
            return True

        return False # not a constituent of address


    def iterate_children(self):
        node_refs = []
        for tag in self.element.iter():
            # only interested in tags and node refs
            if tag.tag not in ('tag', 'nd'): continue
            # handle node refs
            if tag.tag == 'nd':
                node_refs.append(tag.attrib['ref'])
                continue

            key, value = tag.attrib['k'], tag.attrib['v']
            if problemchars.match(key): continue
            if not self.check_address(key, value):
                # place all other tags right on the node
                self.node[key] = value

        if node_refs:
            self.node['node_refs'] = node_refs
            # if this is a way, is it open or closed?
            if self.element.tag == "way":
                is_closed = len(node_refs) > 1 and node_refs[0] == node_refs[-1]
                self.node['open'] = not is_closed
        if hasattr(self, 'address'):
            self.node['address'] = self.address

    def shape(self):
        self.node = {}
        if self.element.tag == "node" or self.element.tag == "way":
            self.node['type'] = self.element.tag
            self.iterate_attributes()
            self.iterate_children()
            return self.node
        else:
            return None


def process_map(file_in, test=False):
    # You do not need to change this file
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            shaper = ElementShaper(element)
            el = shaper.shape()
            if el:
                data.append(el)
                if test:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data

def main(fname, test=True):
    # NOTE: if you are running this code on your computer, with a larger dataset, 
    # call the process_map procedure with pretty=False. The pretty=True option adds 
    # additional spaces to the output, making it significantly larger.
    data = process_map(fname, test=test)
    
    if test:
        pprint.pprint(data)
        correct_first_elem = {
            "id": "261114295", 
            "visible": "true", 
            "type": "node", 
            "pos": [41.9730791, -87.6866303], 
            "created": {
                "changeset": "11129782", 
                "user": "bbmiller", 
                "version": "7", 
                "uid": "451048", 
                "timestamp": "2012-03-28T18:31:23Z"
            }
        }
        assert data[0] == correct_first_elem
        assert data[-1]["address"] == {
                                        "street": "West Lexington Street", 
                                        "housenumber": "1412"
                                        }
        assert data[-1]["node_refs"] == [ "2199822281", "2199822390",  "2199822392", "2199822369", 
                                        "2199822370", "2199822284", "2199822281"]

if __name__ == "__main__":
    test, fname = True, TEST_OSMFILE
    if len(sys.argv) == 2 and sys.argv[1] != TEST_OSMFILE:
        test, fname = False, sys.argv[1]
    main(fname, test=test)
