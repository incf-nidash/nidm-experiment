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
            self.schema_text = "<div id=\""+term_prefix+"\"><h1>"+term_prefix+"</h1><ul class=\"term_list\">"
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
                self.schema_text += "<details><summary>"+prov_link+"</summary><ul>"
            children = self.owl.get_direct_children(prov)
            children = self.owl.sorted_by_labels(children)

            for child in children:
                if prov == None:
                    parents = self.owl.get_direct_parents(child)
                    if len(parents) > 0:
                        continue

                self.get_hierarchy(child)
            self.schema_text += "</ul></details>"
    
    def get_hierarchy(self, uri, level=1):
        # hier_str = '-' * level
        # hier_str += str(self.owl.get_label(uri))
        # print(hier_str)

        term_link = self.term_link_schema(uri)
        
        children = self.owl.get_direct_children(uri)
        children = self.owl.sorted_by_labels(children)
        if len(children) <= 0:
            self.schema_text += "<li>"+term_link+"</li>"
            return None
        
        self.schema_text += "<details><summary>"+term_link+"</summary><ul>"
        for child in children:
            self.get_hierarchy(child, level+1)
        self.schema_text += "</ul></details>"

    def create_specification(self, prefix):
        classes = self.owl.get_classes(prefix=prefix, but=self.already_defined_classes)
        classes_by_types = self.owl.get_class_names_by_prov_type(classes, prefix=prefix, but=self.already_defined_classes)
        self.already_defined_classes += classes

        all_classes = \
            classes_by_types[PROV['Activity']] + \
            classes_by_types[PROV['Entity']] + \
            classes_by_types[PROV['Agent']] + \
            classes_by_types[None]

        print(self.get_top_uri(classes_by_types))

        for class_uri in all_classes:
            definition = self.owl.get_definition(class_uri)
            self.create_class_section(class_uri, definition)
        
        self.add_type_section(OWL['DatatypeProperty'])
        self.add_type_section(OWL['AnnotationProperty'])
        self.add_type_section(OWL['ObjectProperty'])
        self.add_type_section(OWL['NamedIndividual'])

    def get_top_uri(self, classes_by_types):
        all_classes = \
            classes_by_types[PROV['Activity']] + \
            classes_by_types[PROV['Entity']] + \
            classes_by_types[PROV['Agent']] + \
            classes_by_types[None]

        prov_types = [PROV['Activity'], PROV['Entity'], PROV['Agent'], None]

        top_uri = []
        for prov in prov_types:
            print('prov: '+str(prov))
            for uri in classes_by_types[prov]:
                print('-- '+self.owl.get_label(uri))
                children = self.owl.get_direct_children(uri)
                for child in children:
                    print('---- '+self.owl.get_label(child))
            print('')

        # for uri in all_classes:
        #     print(self.owl.get_label(uri))
        #     parents = list(self.owl.get_direct_parents(uri))
                
        #     for p in parents:
        #          print("parent -- "+self.owl.get_label(p))
        #     #print(parents)
        #     print('')
        #     if len(parents) <= 0:
        #         top_uri.append(self.owl.get_label(uri))
        return top_uri

    def add_type_section(self, rdf_type):
        entries = self.get_type_entries(rdf_type)
        
        if entries:
            for entry in entries:
                # print(entry)
                self.create_class_section(entry, self.owl.get_definition(entry))
    
    def get_type_entries(self, rdf_type):
        entries = self.owl.all_of_rdf_type(rdf_type, but_type=OWL['Class'])
        if entries:
            filtered = list()
            for entry in entries:
                pre = self.owl.get_label(entry).split(":")[0]
                if pre.lower() == self.term_prefix:
                    filtered.append(entry)
            if filtered:
                return filtered
        return False
    
    def has_type_entries(self, rdf_type):
        entries = self.owl.all_of_rdf_type(rdf_type, but_type=OWL['Class'])
        if entries:
            for entry in entries:
                pre = self.owl.get_label(entry).split(":")[0]
                if pre.lower() == self.term_prefix:
                    return True
        return False
 
    def format_definition(self, definition):
        definition = str(definition)
        #print "into format_definition"

        # Capitalize first letter, format markdown and end with dot
        if definition:
            definition = definition[0].upper() + definition[1:]
            
            # Replace links specified in markdown by html
            definition = markdown2.markdown(definition).replace("<p>", "").replace("</p>", "")
            definition = definition[0:-1]

            definition += "."

        return definition

    def term_link_schema(self, term_uri):
        definition = str(self.owl.get_definition(term_uri))
        href = ""
        if self.owl.is_external_namespace(term_uri):
            href = " href =\""+str(term_uri)+"\""
        else: #target link fix
            term_uri_prefix = self.owl.get_label(term_uri).split(":")[0]
            html_file = term_uri_prefix+".html"
            if term_uri_prefix == "nidm":
                html_file = "index.html"
            href = " href =\"./"+html_file+"#"+self.owl.get_name(term_uri).lower()+"\""
        
        # if text is None:
        #     text = self.owl.get_label(term_uri)

        class_name = self.owl.get_label(term_uri)
        term_link = "<a tag=\""+class_name+"\""+href+" description=\""+definition+"\" target=\"_blank\">"+class_name+"</a>"

        self.owl.get_direct_children(term_uri)

        #"""<a href="#Communicate" tag="Communicate"
        # description="Convey knowledge of or information about something."
        # role="button" class="list-group-item level-2" data-toggle="collapse"
        # aria-expanded="true" name="schemaNode">Communicate</a>""""

        self.schema_done.append(class_name)

        return term_link

    def create_class_section(self, class_uri, definition):
        class_label = self.owl.get_label(class_uri)
        class_name = self.owl.get_name(class_uri)
        definition = self.format_definition(definition)
        
        if (not class_label.startswith(self.term_prefix.lower()+':')):
            return
           
        #self.schema_text += "<section id=\""+class_name.lower()+"\">"+class_uri+": "+definition+"</section>"
        #"""<a href="#Communicate" tag="Communicate" description="Convey knowledge of or information about something." role="button" class="list-group-item level-2" data-toggle="collapse" aria-expanded="true" name="schemaNode">Communicate</a>""""
        self.schema_text += "<li>"+self.term_link_schema(class_uri)+"</li>"

    def add_schema(self):
        if self.schema_file != None:
            schema_file = os.path.join(DOC_FOLDER, self.schema_file)
        schema_open = codecs.open(schema_file, 'a', "utf-8")
        schema_open.write(self.schema_text+"\n</ul>\n</div>\n")
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
