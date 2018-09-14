import lxml.etree as etree
import sys
import requests
import os
import string
from StringIO import StringIO
import hashlib
import urllib2
import copy

class ATOMMetadata:
    
    template = None
    root = None
    tree = None
    namespaces={'a':'http://www.w3.org/2005/Atom',
                'b':'http://www.georss.org/georss',
                'c':'http://purl.org/dc/terms/',
                'd':'http://purl.org/dc/elements/1.1/',
                'e':'http://www.opengis.net/eop/2.1',
                'o':'http://www.opengis.net/opt/2.1'}
    
    def __init__(self, template = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'atom_metadata.xml')):
        
        self.template = template
        self.tree = etree.parse(template)
        self.root = self.tree.getroot()
    
    def update_text(self, xpath, text):
        
        el = self.root.xpath(xpath, namespaces=self.namespaces)
        el[0].text = text
    
    
    def set_title(self, title):

        self.update_text('/a:feed/a:entry/a:title', 
                         title)
        
    def set_identifier(self, identifier):

        self.update_text('/a:feed/a:entry/d:identifier', 
                         identifier)
        
        
    def set_bbox(self,bbox):
        
        self.update_text('/a:feed/a:entry/b:box', 
                         bbox)
        
        
    def set_spatial(self, wkt):
        
        self.update_text('/a:feed/a:entry/c:spatial', 
                         wkt)
        
        
    def set_productType(self, pt):
        
        self.update_text('/a:feed/a:entry/e:productType', 
                         pt)
    
    
    def set_polygon(self, polygon):
        
        self.update_text('/a:feed/a:entry/b:polygon', 
                         polygon)
        
        
    def set_date(self, start_date,end_date):
        
        self.update_text('/a:feed/a:entry/d:date',
                        '%s/%s' %(start_date,end_date))
                         
    
    def set_onlineResource(self, download_URL, hostname):
        
        enclosure_elem = self.root.xpath('/a:feed/a:entry/a:link[@title="TITLE"]', 
                             namespaces={'a':'http://www.w3.org/2005/Atom'})

        enclosure_elem[0].attrib['title'] =  'Download via %s server' %hostname
        enclosure_elem[0].attrib['href'] =  download_URL
        
        
    def metadata(self):
                         
        return etree.tostring(self.tree, pretty_print=True)   
    
    def write(self, atom_file):
        
        xml_file = open(atom_file, 'w')
        xml_file.write(etree.tostring(self.tree, pretty_print=True))    
        