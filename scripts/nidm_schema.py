from msilib import schema
import os
import codecs
import collections
import sys
import glob
from nidm_owl_reader import OwlReader
from nidm_constants import *
from rdflib import RDF
import markdown2
import cgi
import logging

logging.basicConfig(filename='debug.log', level=logging.DEBUG, filemode='w')
logger = logging.getLogger(__name__)

class OwlNidmHtml:
    def __init__(self, term_infos, import_files, spec_name, schema_file=None):
        self.name = spec_name
        self.component = self.name.lower().replace("-", "_")
        self.section_open = 0
        self.already_defined_classes = list()

        for terms in term_infos:
            prefix, term_prefix = terms['prefix']
            owl_file = terms['owl_file']

            self.prefix = prefix
            self.term_prefix = term_prefix

            self.owl = OwlReader(owl_file, import_files)
            self.owl.graph.bind('owl', 'http://www.w3.org/2002/07/owl#')
            self.owl.graph.bind('dct', 'http://purl.org/dc/terms/')
            self.owl.graph.bind('dicom', 'http://purl.org/nidash/dicom#')
            self.owl.graph.bind('nidm', 'http://purl.org/nidash/nidm#')
            self.owl.graph.bind('bids', 'http://purl.org/nidash/bids#')
            self.owl.graph.bind('onli', 'http://neurolog.unice.fr/ontoneurolog/v3.0/instrument.owl#')
            self.owl.graph.bind('pato', 'http://purl.obolibrary.org/obo/pato#')
            self.owl.graph.bind('prov', 'http://www.w3.org/ns/prov')
            self.owl.graph.bind('qibo', 'http://www.owl-ontologies.com/Ontology1298855822.owl')
            self.owl.graph.bind('sio', 'http://semanticscience.org/resource/')
            
            #self.classes = self.split_process(owl_file)

            self.schema_file = schema_file
            self.schema_text = "<h1>NIDM Class Browser</h1><div id='schema' class='list-group list-group-root well'>"
            self.schema_done = []

            #self.create_specification(prefix)
            self.create_schema_spec()
            self.add_schema()

    def create_schema_spec(self):
        classes = self.owl.get_classes(but=self.already_defined_classes)
        classes_by_types = self.owl.get_class_names_by_prov_type(classes, but=self.already_defined_classes)
        self.already_defined_classes += classes

        all_classes = \
            classes_by_types[PROV['Activity']] + \
            classes_by_types[PROV['Entity']] + \
            classes_by_types[PROV['Agent']] + \
            classes_by_types[None]

        prov_types = [PROV['Activity'], PROV['Entity'], PROV['Agent'], None]

        for prov in prov_types:
            # print('prov: '+str(prov))
            if prov != None:
                prov_link = self.owl.get_label(prov)
                prov_name = self.owl.get_name(prov)
                self.schema_text += "<a class='list-group-item' data-bs-toggle='collapse' role='button' href=\"#"+prov_name+"\" aria-expanded='true'>"+prov_link+"</a>"
                self.schema_text += "<div class='list-group multi-collapse level-1 show' id=\""+prov_name+"\">"
            children = self.owl.get_direct_children(prov)
            children = self.owl.sorted_by_labels(children)

            for child in children:
                if prov == None:
                    parents = self.owl.get_direct_parents(child)
                    if len(parents) > 0:
                        continue

                self.get_hierarchy(child)
            self.schema_text += "</div>"

        # self.add_type_section(OWL['DatatypeProperty'])
        # self.add_type_section(OWL['AnnotationProperty'])
        # self.add_type_section(OWL['ObjectProperty'])
        # self.add_type_section(OWL['NamedIndividual'])
    
    def get_hierarchy(self, uri, level=1):
        # hier_str = '-' * level
        # hier_str += str(self.owl.get_label(uri))
        # print(hier_str)

        class_label = self.owl.get_label(uri)
        self.schema_done.append(class_label)
        
        class_name = self.owl.get_name(uri)
        definition = str(self.owl.get_definition(uri))
        
        children = self.owl.get_direct_children(uri)
        children = self.owl.sorted_by_labels(children)
        if len(children) <= 0:
            self.schema_text += "<a description=\""+definition+"\" role=\"button\" class=\"list-group-item\" tag=\""+class_name+"\">"+class_label+"</a>"
            return None
        
        hier_level = "level-"+str(level+1)
        self.schema_text += "<a href=\"#"+class_name+"\"description=\""+definition+"\" role=\"button\" data-bs-toggle=\"collapse\" class=\"list-group-item\" tag=\""+class_name+"\" aria-expanded='false'>"+class_label+"</a>"
        self.schema_text += "<div class=\"list-group multi-collapse "+hier_level+" collapse\" id=\""+class_name+"\">"

        for child in children:
            self.get_hierarchy(child, level+1)

        self.schema_text += "</div>"

    def add_schema(self):
        if self.schema_file != None:
            schema_file = os.path.join(DOC_FOLDER, self.schema_file)
        schema_open = codecs.open(schema_file, 'a', "utf-8")
        schema_open.write(self.schema_text+"\n</div>")
        schema_open.close()
  

    # def split_process(self, owl_file):
    #     f = open(owl_file, "r")
    #     lines = f.readlines()
    #     f.close()
        
    #     classes = []
    #     for x in lines:
    #         x = x.strip()
    #         if x != "" and x[0] != "#" and x[0] != "@" and x[0] != "[":
    #             if "owl:Class" not in x:
    #                 continue
    #             #print(x)
    #             x = shlex.split(x)
    #             subject = x[0]
    #             if subject not in classes:
    #                 classes.append(subject)

    #     return classes

def create_schema_file(schema_file="schema.html"):
    if schema_file == "schema.html":
        schema_file = os.path.join(DOC_FOLDER, "schema.html")
    schema_open = codecs.open(schema_file, 'w', "utf-8")
    schema_open.write("""
    <!DOCTYPE html>
    <html lang="en-us">
    <head>
        <meta charset="UTF-8">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3" crossorigin="anonymous">
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
        <link rel="stylesheet" type="text/css" href="stylesheet/schema.css" media="screen">
        <script type="text/javascript" src="stylesheet/schema.js"></script>
    </head>
    <body>
    """)
    #<div id="info_box">test</div>
    #""")
    schema_open.close()

def schema_footer(schema_file="schema.html"):
    if schema_file == "schema.html":
        schema_file = os.path.join(DOC_FOLDER, "schema.html")
    schema_open = codecs.open(schema_file, 'a', "utf-8")
    schema_open.write("""
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-ka7Sk0Gln4gmtz2MlQnikT1wXgYsOg+OMhuP+IlRH9sENBO0LRn5q+8nbTov4+1p" crossorigin="anonymous"></script>
    </body>
    </html>
    """)
    schema_open.close()


RELPATH = os.path.dirname(os.path.abspath(__file__))
NIDM_ROOT = os.path.abspath(os.path.join(RELPATH ,'..'))
DOC_FOLDER = os.path.join(NIDM_ROOT, 'specs')
INCLUDE_FOLDER = os.path.join(DOC_FOLDER, 'include')
IMPORTS_FOLDER = os.path.abspath(os.path.join(NIDM_ROOT ,'imports'))
TERMS_FOLDER = os.path.join(NIDM_ROOT, 'terms')
RELEASED_TERMS_FOLDER = os.path.join(TERMS_FOLDER, 'releases')

def main():
    owl_file = os.path.join(TERMS_FOLDER, 'nidm-experiment.owl')
    import_files = glob.glob(os.path.join(IMPORTS_FOLDER, '*.ttl'))

    # check the file exists
    assert os.path.exists(owl_file)

    schema_file="schema.html"
    create_schema_file(schema_file=schema_file)

    term_infos = [
        {'prefix': [str(NIDM), 'nidm'], 'owl_file': os.path.join(TERMS_FOLDER, 'nidm-experiment.owl')},
        #{'prefix': [str(BIDS), 'bids'], 'owl_file': os.path.join(IMPORTS_FOLDER, 'bids_import.ttl')},
        #{'prefix': [str(DICOM), 'dicom'], 'owl_file': os.path.join(IMPORTS_FOLDER, 'dicom_import.ttl')},
        #{'prefix': [str(SIO), 'sio'], 'owl_file': os.path.join(IMPORTS_FOLDER, 'sio_import.ttl')},
        #{'prefix': [str(OBO), 'obo'], 'owl_file': os.path.join(IMPORTS_FOLDER, 'obo_import.ttl')},
        #{'prefix': [str(ONLI), 'onli'], 'owl_file': os.path.join(IMPORTS_FOLDER, 'ontoneurolog_instruments_import.ttl')},
    ]

    OwlNidmHtml(term_infos, import_files, "NIDM-Experiment", schema_file)

    #owlspec = OwlNidmHtml(owl_file, import_files, "NIDM-Experiment", prefix=str(NIDM), term_prefix="nidm", schema_file=schema_file)
    
    #component_name = "nidm-experiment"
    #owlspec.write_specification(component=component_name, version=nidm_version)

    
    #owl_file = os.path.join(IMPORTS_FOLDER, 'bids_import.ttl')
    #owl_process(owl_file, None, "BIDS", prefix=str(BIDS), term_prefix="bids", schema_file=schema_file)
    
    # owl_file = os.path.join(IMPORTS_FOLDER, 'dicom_import.ttl')
    # owl_process(owl_file, None, "DICOM", prefix=str(DICOM), term_prefix="dicom")

    # owl_file = os.path.join(IMPORTS_FOLDER, 'sio_import.ttl')
    # owl_process(owl_file, None, "SIO", prefix=str(SIO), term_prefix="sio")
    
    # owl_file = os.path.join(IMPORTS_FOLDER, 'obo_import.ttl')
    # owl_process(owl_file, None, "OBO", prefix=str(OBO), term_prefix="obo")

    #owl_file = os.path.join(IMPORTS_FOLDER, 'ontoneurolog_instruments_import.ttl')
    #owl_process(owl_file, None, "ONLI", prefix=str(ONLI), term_prefix="onli", schema_file=schema_file)

    schema_footer(schema_file="schema.html")

if __name__ == "__main__":
    main()
