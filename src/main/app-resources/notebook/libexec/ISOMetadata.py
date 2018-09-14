import lxml.etree as etree
import sys
import requests
import os
import string
from StringIO import StringIO
import hashlib
import urllib2
import copy

class ISOMetadata:
    
    template = None
    root = None
    tree = None
    iso_namespaces = { 'A':'http://www.isotc211.org/2005/gmd',
                   'B':'http://www.isotc211.org/2005/gco',
                   'C':'http://www.opengis.net/gml'
                 }
    
    def __init__(self, template = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'iso_metadata.xml')):
        
        self.template = template
        self.tree = etree.parse(template)
        self.root = self.tree.getroot()
    
    def update_text(self, xpath, text):
        
        #print 'setting: ', text
        el = self.root.xpath(xpath, namespaces=self.iso_namespaces)    
        el[0].text = text
    
    
    def update_elem_text(self, xml_elem, xpath, text):
        
        el = xml_elem.xpath(xpath, namespaces=self.iso_namespaces)
        el[0].text = text
    
    
    def get_element_copy(self, ref_path):
         
        return copy.deepcopy(self.root.find(ref_path, self.iso_namespaces))
    
        
    def add_element_root_based_path(self, ref_path, xml_element):

        els = self.root.findall(ref_path, self.iso_namespaces)
    
        first_el = self.root.find(ref_path, self.iso_namespaces)

        first_el_index = self.root.index(first_el)
  
        els[0].getparent().insert(first_el_index + len(els), xml_element)

        
    def add_element(self, ref_path, xml_element):

        ref_path_list = ref_path.split('/')
       
        sub_els = list()
        
        sub_els =[{'index':self.root.index(self.root.findall(ref_path_list[0], self.iso_namespaces)[-1]), 
                   'last_element': self.root.findall(ref_path_list[0], self.iso_namespaces)[-1]}]
        
        for i in range(1,len(ref_path_list)):
            # navigate the elements tree to reach the last given position of the required ref_path
            el = sub_els[i-1]['last_element'].findall(ref_path_list[i], self.iso_namespaces)[-1]
            ind = sub_els[i-1]['last_element'].index(el)
            sub_els.append({'index':ind+1, 'last_element' : el})
            
        sub_els[-1]['last_element'].getparent().insert(sub_els[-1]['index'],xml_element)
        
        
    def set_identifier(self, identifier):

        self.update_text('//A:MD_Metadata/A:fileIdentifier/B:CharacterString', 
                         identifier)
        
        self.update_text('//A:MD_Metadata/A:identificationInfo/' +
                         'A:MD_DataIdentification/A:citation/' +
                         'A:CI_Citation/A:identifier/A:RS_Identifier/' +
                         'A:code/B:CharacterString', 
                         identifier)
    
    
    def set_organisation(self, organisation):
        
        self.update_text('//A:MD_Metadata/A:contact/A:CI_ResponsibleParty' +
                         '/A:organisationName/B:CharacterString',
                         organisation)
        
        self.update_text('//A:MD_Metadata/A:identificationInfo/' +
                         'A:MD_DataIdentification/A:pointOfContact/' +
                         'A:CI_ResponsibleParty/A:organisationName/B:CharacterString',
                         organisation)
    
    def set_contact(self, contact):
    
        self.update_text('//A:MD_Metadata/A:contact/A:CI_ResponsibleParty/' + 
                         'A:contactInfo/A:CI_Contact/A:address/' + 
                         'A:CI_Address/A:electronicMailAddress/B:CharacterString',
                         contact)
        
        self.update_text('//A:MD_Metadata/A:identificationInfo/' +
                         'A:MD_DataIdentification/A:pointOfContact/' +
                         'A:CI_ResponsibleParty/A:contactInfo/A:CI_Contact/' +
                         'A:address/A:CI_Address/A:electronicMailAddress/B:CharacterString',
                         contact)

        
    def fillin_spatialReprInfo(self, sp_Repr_info_el, spatial_info):
        
        self.update_elem_text(sp_Repr_info_el, 
                              '//A:spatialRepresentationInfo/' +
                              'A:MD_Georectified/' +
                              'A:cornerPoints/' +
                              'C:Point[@C:id=\"NW_corner\"]/' +
                              'C:pos',
                              spatial_info['nw_corner'])
        
        self.update_elem_text(sp_Repr_info_el,
                              '//A:spatialRepresentationInfo/' +
                              'A:MD_Georectified/' +
                              'A:cornerPoints/' +
                              'C:Point[@C:id=\"SE_corner\"]/' +
                              'C:pos', 
                              spatial_info['se_corner'])
        
        self.update_elem_text(sp_Repr_info_el, 
                              '//A:spatialRepresentationInfo/' +
                              'A:MD_Georectified/A:axisDimensionProperties/' +
                              'A:MD_Dimension[A:dimensionName/' +
                              'A:MD_DimensionNameTypeCode/text()=\"Row\"]/A:dimensionSize/B:Integer', 
                              spatial_info['row_size'])
        
        self.update_elem_text(sp_Repr_info_el, 
                              '//A:spatialRepresentationInfo/' +
                              'A:MD_Georectified/A:axisDimensionProperties/' +
                              'A:MD_Dimension[A:dimensionName/' +
                              'A:MD_DimensionNameTypeCode/text()=\"Column\"]/' +
                              'A:dimensionSize/B:Integer', 
                               spatial_info['col_size'])
        
        self.update_elem_text(sp_Repr_info_el, 
                              '//A:spatialRepresentationInfo/' +
                              'A:MD_Georectified/A:axisDimensionProperties/' +
                              'A:MD_Dimension[A:dimensionName/' +
                              'A:MD_DimensionNameTypeCode/text()=\"Column\"]/' +
                              'A:resolution/B:Length', 
                              spatial_info['col_res'])

        self.update_elem_text(sp_Repr_info_el, 
                              '//A:spatialRepresentationInfo/' +
                              'A:MD_Georectified/A:axisDimensionProperties/' +
                              'A:MD_Dimension[A:dimensionName/' +
                              'A:MD_DimensionNameTypeCode/text()=\"Row\"]/' +
                              'A:resolution/B:Length', 
                               spatial_info['row_res'])
        
    
    def set_spatialReprInfo_elems(self, spatial_infos, bands_ref_list):
        
        ref_path = 'A:spatialRepresentationInfo'
        
        #update first element
        spatial_info = spatial_infos[bands_ref_list[0]]

        self.set_nw_corner(spatial_info['nw_corner'])
        self.set_se_corner(spatial_info['se_corner'])
        self.set_row_size(spatial_info['row_size'])
        self.set_col_size(spatial_info['col_size'])
        self.set_row_res(spatial_info['row_res'])
        self.set_col_res(spatial_info['col_res'])
        
        #insert all other required properly filled in elements
        for band in bands_ref_list[1:]:
            
            spatial_info = spatial_infos[band]
            
            # get the element copy
            sp_Repr_info_el = self.get_element_copy(ref_path)
            
            # fill in the element with the proper values
            self.fillin_spatialReprInfo(sp_Repr_info_el, spatial_info)
            
            # add the current element to the previous one
            self.add_element(ref_path, sp_Repr_info_el)
            
        
    def set_spatial_resolutions(self, sp_res):
        
        ref_path = 'A:identificationInfo/A:MD_DataIdentification/A:spatialResolution'
        
        #update first element
        self.update_text('//A:MD_Metadata/A:identificationInfo/' \
                         'A:MD_DataIdentification/A:spatialResolution/' \
                         'A:MD_Resolution/A:distance/B:Distance',
                         sp_res[0])
        
        #insert all other required elements
        for sp in sp_res[1:]:
            
            # get the element copy
            sp_resolution_el = self.get_element_copy(ref_path)
            
            # fill in the element with the proper values
            xpath = '//A:spatialResolution/A:MD_Resolution/A:distance/B:Distance'
            self.update_elem_text(sp_resolution_el, xpath, sp)
            
            # add the current element to the previous one
            self.add_element(ref_path, sp_resolution_el)
            
        
    def set_date(self, date):
        
        self.update_text('//A:MD_Metadata/A:dateStamp/B:Date',
                        date)
        
        
    def set_creation_date(self, datetime):
        
        self.update_text('//A:MD_Metadata/A:identificationInfo/' +
                         'A:MD_DataIdentification/A:citation/' + 
                         'A:CI_Citation/A:date/A:CI_Date/A:date/B:DateTime',
                        datetime)

    def set_row_size(self, row_size):
        
        self.update_text('//A:MD_Metadata/A:spatialRepresentationInfo/' +
                         'A:MD_Georectified/A:axisDimensionProperties/' + 
                         'A:MD_Dimension[A:dimensionName/' + 
                         'A:MD_DimensionNameTypeCode/text()=\"Row\"]/' +
                         'A:dimensionSize/B:Integer',
                         row_size)
        
    def set_col_size(self, col_size):
        
        self.update_text('//A:MD_Metadata/A:spatialRepresentationInfo/' +
                         'A:MD_Georectified/A:axisDimensionProperties/' + 
                         'A:MD_Dimension[A:dimensionName/' + 
                         'A:MD_DimensionNameTypeCode/text()=\"Column\"]/' +
                         'A:dimensionSize/B:Integer',
                         col_size) 
    
    
    def set_col_res(self, col_res):
        
        self.update_text('//A:MD_Metadata/A:spatialRepresentationInfo/' +
                         'A:MD_Georectified/A:axisDimensionProperties/' + 
                         'A:MD_Dimension[A:dimensionName/' + 
                         'A:MD_DimensionNameTypeCode/text()=\"Column\"]/' +
                         'A:resolution/B:Length',
                         col_res)
        
        
    def set_row_res(self, row_res):
        
        self.update_text('//A:MD_Metadata/A:spatialRepresentationInfo/' +
                         'A:MD_Georectified/A:axisDimensionProperties/' + 
                         'A:MD_Dimension[A:dimensionName/' + 
                         'A:MD_DimensionNameTypeCode/text()=\"Row\"]/' +
                         'A:resolution/B:Length',
                         row_res)
    
    
    def set_pixel_size(self, pixel_size):
        
        self.update_text('//A:MD_Metadata/A:spatialRepresentationInfo/' +
                         'A:MD_Georectified/A:axisDimensionProperties/' + 
                         'A:MD_Dimension[A:dimensionName/' + 
                         'A:MD_DimensionNameTypeCode/text()=\"Column\"]/' +
                         'A:resolution/B:Length',
                         pixel_size)
        
        self.update_text('//A:MD_Metadata/A:spatialRepresentationInfo/' +
                         'A:MD_Georectified/A:axisDimensionProperties/' + 
                         'A:MD_Dimension[A:dimensionName/' + 
                         'A:MD_DimensionNameTypeCode/text()=\"Row\"]/' +
                         'A:resolution/B:Length',
                         pixel_size)
        
        self.update_text('//A:MD_Metadata/A:identificationInfo/' +
                         'A:MD_DataIdentification/A:spatialResolution/' +
                         'A:MD_Resolution/A:distance/B:Distance',
                         pixel_size)
                         
        
    def set_nw_corner(self, nw_corner):
        
        self.update_text('//A:MD_Metadata/A:spatialRepresentationInfo/A:MD_Georectified/' +
                         'A:cornerPoints/C:Point[@C:id=\"NW_corner\"]/C:pos',
                         nw_corner)    
    
    def set_se_corner(self, se_corner):
        
        self.update_text('//A:MD_Metadata/A:spatialRepresentationInfo/A:MD_Georectified/' +
                         'A:cornerPoints/C:Point[@C:id=\"SE_corner\"]/C:pos',
                         se_corner)  

    def set_epsg_code(self, epsg_code):
        
        self.update_text('//A:MD_Metadata/A:referenceSystemInfo/' + 
                         'A:MD_ReferenceSystem/A:referenceSystemIdentifier/' +
                         'A:RS_Identifier/A:code/B:CharacterString',
                         epsg_code)   
    
    def set_title(self, title):
        
        self.update_text('//A:MD_Metadata/A:identificationInfo/' +
                         'A:MD_DataIdentification/A:citation/' +
                         'A:CI_Citation/A:title/B:CharacterString',
                         title)        
   
    def set_abstract(self, abstract):
        
        self.update_text('//A:MD_Metadata/A:identificationInfo/' +
                         'A:MD_DataIdentification/A:abstract/B:CharacterString',
                        abstract)    
    
    def set_min_lon(self, min_lon):
        
        self.update_text('//A:MD_Metadata/A:identificationInfo/' + 
                         'A:MD_DataIdentification/A:extent/' + 
                         'A:EX_Extent/A:geographicElement/A:EX_GeographicBoundingBox/' + 
                         'A:westBoundLongitude/B:Decimal',
                        min_lon)
        
    def set_max_lon(self, max_lon):
        
        self.update_text('//A:MD_Metadata/A:identificationInfo/' + 
                         'A:MD_DataIdentification/A:extent/' + 
                         'A:EX_Extent/A:geographicElement/A:EX_GeographicBoundingBox/' + 
                         'A:eastBoundLongitude/B:Decimal',
                        max_lon)    

    def set_min_lat(self, min_lat):
        
        self.update_text('//A:MD_Metadata/A:identificationInfo/' + 
                         'A:MD_DataIdentification/A:extent/' + 
                         'A:EX_Extent/A:geographicElement/A:EX_GeographicBoundingBox/' + 
                         'A:southBoundLatitude/B:Decimal',
                        min_lat)
        
    def set_max_lat(self, max_lat):
        
        self.update_text('//A:MD_Metadata/A:identificationInfo/' + 
                         'A:MD_DataIdentification/A:extent/' + 
                         'A:EX_Extent/A:geographicElement/A:EX_GeographicBoundingBox/' + 
                         'A:northBoundLatitude/B:Decimal',
                        max_lat)
        
    def set_start_date(self, start_date):
        
        self.update_text('//A:MD_Metadata/A:identificationInfo/' +
                         'A:MD_DataIdentification/A:extent/A:EX_Extent/' + 
                         'A:temporalElement/A:EX_TemporalExtent/'  +
                         'A:extent/C:TimePeriod/C:begin/' +
                         'C:TimeInstant/C:timePosition',
                        start_date)
        
    def set_end_date(self, end_date):
        
        self.update_text('//A:MD_Metadata/A:identificationInfo/' +
                         'A:MD_DataIdentification/A:extent/A:EX_Extent/' + 
                         'A:temporalElement/A:EX_TemporalExtent/'  +
                         'A:extent/C:TimePeriod/C:end/' +
                         'C:TimeInstant/C:timePosition',
                        end_date)
    
    def set_data_type(self, data_type):
        
        self.update_text('//A:MD_Metadata/A:contentInfo/A:MD_CoverageDescription/' +
                         'A:dimension/A:MD_RangeDimension/A:sequenceIdentifier/' +
                         'B:MemberName/B:attributeType/B:TypeName/B:aName/B:CharacterString',
                        data_type)
        
    def set_data_format(self, data_format):
        
        self.update_text('//A:MD_Metadata/A:distributionInfo/A:MD_Distribution/' +
                         'A:distributionFormat/A:MD_Format/A:name/B:CharacterString',
                        data_format)        
    
    def set_responsible_party(self, party):
        
        self.update_text('//A:MD_Metadata/A:distributionInfo/' +
                         'A:MD_Distribution/A:distributor/A:MD_Distributor/' +
                         'A:distributorContact/A:CI_ResponsibleParty/' + 
                         'A:organisationName/B:CharacterString',
                        party)   
    
    
    def set_data_quality(self, data_quality):
        
        self.update_text('//A:MD_Metadata/A:dataQualityInfo/' +
                         'A:DQ_DataQuality/A:lineage/A:LI_Lineage/' + 
                         'A:statement/B:CharacterString',
                        data_quality)
    
    def set_lineage_template(self, template_str):
        
        ref_path = 'A:dataQualityInfo/A:DQ_DataQuality/A:lineage/A:LI_Lineage/A:statement'
        first_el = self.root.find(ref_path, self.iso_namespaces)
        #/text()=\"template\"',
        self.update_text('//A:MD_Metadata/A:dataQualityInfo/' +
                         'A:DQ_DataQuality/A:lineage/A:LI_Lineage/' + 
                         'A:statement/B:CharacterString',
                         template_str)

        
    def set_pa(self, pa):
        
        self.update_text('//A:MD_Metadata/A:identificationInfo//' + 
                         'A:MD_DataIdentification/A:extent/A:EX_Extent/' +
                         'A:geographicElement/A:EX_GeographicDescription/' + 
                         'A:geographicIdentifier/A:MD_Identifier/A:code/B:CharacterString',
                        pa)
    
    def set_onlineResource(self, download_URL):
        
        self.update_text('//A:MD_Metadata/A:distributionInfo/A:MD_Distribution/' +
                         'A:transferOptions/A:MD_DigitalTransferOptions/A:onLine/A:CI_OnlineResource/' +
                         'A:linkage/A:URL',
                        download_URL)
        
        
    def metadata(self):
                         
        return etree.tostring(self.tree, pretty_print=True)   
    
    def write(self, iso_file):
        
        xml_file = open(iso_file, 'w')
        xml_file.write(etree.tostring(self.tree, pretty_print=True))    
        