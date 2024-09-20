import os
import codecs
import glob
from nidm_owl_reader import OwlReader
from nidm_constants import *
import logging

logging.basicConfig(filename='debug.log', level=logging.DEBUG, filemode='w')
logger = logging.getLogger(__name__)

class OwlNidmHtml:
    def __init__(self, term_infos, import_files, type="class"):
        self.schema_file = "schema_"+type+".html"
        self.type = type

        self.create_schema_file()
        self.section_open = 0
        self.already_defined_classes = list()

        for terms in term_infos:
            owl_file = terms['owl_file']
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
            
            self.schema_text = ""
            self.schema_done = []

            if type == "class":
                self.create_schema_class_spec()
            elif type == "datatype":
                self.create_schema_type_spec(OWL['DatatypeProperty'])
            elif type == "annotation":
                self.create_schema_type_spec(OWL['AnnotationProperty'])
            elif type == "object":
                self.create_schema_type_spec(OWL['ObjectProperty'])
            elif type == "individual":
                self.create_schema_type_spec(OWL['NamedIndividual'])

            self.add_schema()
        
        self.schema_footer()

    def get_top_prop_level(self, terms):
        top = []

        for term in terms:
            parents = self.get_prop_parents(term)
            parents = self.owl.sorted_by_labels(parents)
            if len(parents) <= 0:
                top.append(term)

        return top

    def create_schema_class_spec(self):
        prov_types = [OWL['Thing'], None]

        for prov in prov_types:
            # print('prov: '+str(prov))
            if prov != None:
                prov_link = self.owl.get_label(prov)
                prov_name = self.owl.get_name(prov)
                prov_def = self.format_definition(self.owl.get_definition(prov))
                text_break = "</br>------------------------</br>"
                prov_def += text_break + prov_name
                if not prov_def:
                    prov_def = "<i>Definition not found</i>"
                self.schema_text += "<a class='list-group-item' data-bs-toggle='collapse' role='button' href=\"#"+prov_name+"\" description=\""+prov_def+"\" id=\""+prov_name+"_\" aria-expanded='true'>"+prov_link+"</a>"
                self.schema_text += "<div class='list-group multi-collapse level-1 show' id=\""+prov_name+"\">"
            
            children = self.owl.get_direct_children(prov)
            children = self.owl.sorted_by_labels(children)

            for child in children:
                if prov == None:
                    parents = self.owl.get_direct_parents(child)
                    if len(parents) > 0:
                        continue

                self.get_hierarchy_subclass(child, path=prov_name)
            self.schema_text += "</div>"
    
    def create_schema_type_spec(self, rdf_type):
        terms = self.owl.all_of_rdf_type(rdf_type, but_type=OWL['Class'])
        terms = self.get_top_prop_level(terms)

        for term in terms:
            term_link = self.owl.get_label(term)
            term_name = self.owl.get_name(term)
            term_def = self.format_definition(self.owl.get_definition(term))
            text_break = "</br>------------------------</br>"
            term_def += text_break + term_name
            if not term_def:
                term_def = "<i>Definition not found</i>"

            children = self.get_prop_children(term)
            children = self.owl.sorted_by_labels(children)
            
            if len(children) <= 0:
                term_def = self.clean_definition(term_def)
                self.schema_text += "<a description=\""+term_def+"\" role=\"button\" class=\"list-group-item\" tag=\""+term_name+"\" id=\""+term_name+"\">"+term_link+"</a>"
                continue

            self.schema_text += "<a class='list-group-item' data-bs-toggle='collapse' role='button' href=\"#"+term_name+"\" description=\""+term_def+"\" aria-expanded='true' id=\""+term_name+"_\">"+term_link+"</a>"
            self.schema_text += "<div class='list-group multi-collapse level-1 show' id=\""+term_name+"\">"
            for child in children:
                self.get_hierarchy_subprop(child, path=term_name)
            self.schema_text += "</div>"

        self.schema_text += "</div>"

    def get_prop_children(self, term):
        children = set()

        for child_name in self.owl.graph.subjects(RDFS['subPropertyOf'], term):
            if not self.owl.is_deprecated(child_name):
                children.add(child_name)

        return children

    def get_prop_parents(self, term):
        parents = set()
        for parent_name in self.owl.graph.objects(term, RDFS['subPropertyOf']):
            parents.add(parent_name)
        return parents

    def get_hierarchy_subclass(self, uri, level=1, path=""):
        class_label = self.owl.get_label(uri)
        self.schema_done.append(class_label)
        
        class_name = self.owl.get_name(uri)
        definition = self.format_definition(self.owl.get_definition(uri))
        
        if not definition:
            definition = "<i>Definition not found</i>"
        description = definition

        text_break = "</br>------------------------</br>"
        description += text_break

        # term_info = self.generate_info(uri)
        # if term_info:
        #     description = definition+text_break+term_info
        description = self.clean_definition(description)

        path += " / "+class_name
        description += path

        children = self.owl.get_direct_children(uri)
        children = self.owl.sorted_by_labels(children)
        if len(children) <= 0:
            self.schema_text += "<a description=\""+description+"\" role=\"button\" class=\"list-group-item\" tag=\""+class_name+"\" id=\""+class_name+"\">"+class_label+"</a>"
            return None
        
        hier_level = "level-"+str(level+1)
        self.schema_text += "<a href=\"#"+class_name+"\" description=\""+description+"\" role=\"button\" data-bs-toggle=\"collapse\" class=\"list-group-item\" tag=\""+class_name+"\" aria-expanded='false' id=\""+class_name+"_\">"+class_label+"</a>"
        self.schema_text += "<div class=\"list-group multi-collapse "+hier_level+" collapse\" id=\""+class_name+"\">"

        for child in children:
            self.get_hierarchy_subclass(child, level+1, path)

        self.schema_text += "</div>"

    def get_hierarchy_subprop(self, uri, level=1, path=""):
        prop_label = self.owl.get_label(uri)
        self.schema_done.append(prop_label)
        
        prop_name = self.owl.get_name(uri)
        definition = self.format_definition(self.owl.get_definition(uri))
        
        if not definition:
            definition = "<i>Definition not found</i>"
        description = definition

        text_break = "</br>------------------------</br>"
        description += text_break

        # term_info = self.generate_info(uri)
        # if term_info:
        #     description = definition+text_break+term_info
        
        description = self.clean_definition(description)

        path += "/"+prop_name
        description += path

        children = self.get_prop_children(uri)
        children = self.owl.sorted_by_labels(children)
        if len(children) <= 0:
            self.schema_text += "<a description=\""+description+"\" role=\"button\" class=\"list-group-item\" tag=\""+prop_name+"\" id=\""+prop_name+"\">"+prop_label+"</a>"
            return None
        
        hier_level = "level-"+str(level+1)
        self.schema_text += "<a href=\"#"+prop_name+"\" description=\""+description+"\" role=\"button\" data-bs-toggle=\"collapse\" class=\"list-group-item\" tag=\""+prop_name+"\" aria-expanded='false' id=\""+prop_name+"_\">"+prop_label+"</a>"
        self.schema_text += "<div class=\"list-group multi-collapse "+hier_level+" collapse\" id=\""+prop_name+"\">"

        for child in children:
            self.get_hierarchy_subprop(child, level+1, path)

        self.schema_text += "</div>"

    def clean_definition(self, definition):
        definition = definition.replace('"', '&quot;')
        definition = definition.replace('\"', '&quot;')
        definition = definition.replace('_', '&#95;')
        definition = definition.replace('<em>', '&#95;')
        definition = definition.replace('</em>', '&#95;')
        definition = definition.replace("'", '&apos;')
        return definition

    def format_definition(self, definition):
        try:
            definition = definition.decode("utf-8")
        except AttributeError:
            pass
        # Capitalize first letter, format markdown
        if definition:
            definition = definition[0].upper() + definition[1:]
            definition = definition.replace("<p>", "").replace("</p>", "")
        return definition

    def generate_info(self, class_uri):
        text = self.owl.get_label(class_uri)+" is"

        nidm_class = self.owl.get_nidm_parent(class_uri)
        if nidm_class:
            text += " a "+self.owl.get_label(nidm_class)
        else:
            prov_class = self.owl.get_prov_class(class_uri)
            if prov_class:
                text += " a "+self.owl.get_label(prov_class)
            else:
                #look in NIDM file
                nidm_file = os.path.join(TERMS_FOLDER, 'nec.owl')
                nidm_owl = OwlReader(nidm_file)
                nidm_subclass = self.get_nidm_subclass(class_uri, nidm_owl)
                if nidm_subclass:
                    text += " a "+self.owl.get_label(nidm_subclass)

        class_children = self.owl.get_direct_children(class_uri)
        if class_children:
            text += " and "
            text += " has the following child"
            if len(class_children) > 1:
                text += "ren"
            text += ": " + \
                         self.linked_listing(class_children)
        
        return text

    def get_nidm_subclass(self, class_uri, nidm_owl):
        nidm_subclasses = nidm_owl.get_direct_parents(class_uri)
        for nidm_subclass in nidm_subclasses:
            return nidm_subclass
        return False

    def linked_listing(self, uri_list, prefix="", suffix="", sort=True):

        #print "into linked_listing"

        linked_listing = prefix

        if sort:
            uri_list = self.owl.sorted_by_labels(uri_list)

        for i, uri in enumerate(uri_list):
            if i == 0:
                sep = ""
            elif i == len(uri_list):
                sep = " and "
            else:
                sep = ", "
            linked_listing += sep+self.owl.get_label(uri)

        return linked_listing+suffix

    def add_schema(self):
        if self.schema_file != None:
            schema_file = os.path.join(DOC_FOLDER, self.schema_file)
        schema_open = codecs.open(schema_file, 'a', "utf-8")
        schema_open.write(self.schema_text+"\n</div>")
        schema_open.close()

    def create_schema_file(self):
        if self.schema_file != None:
            schema_file = os.path.join(DOC_FOLDER, self.schema_file)

        if self.type == "class":
            title = "NIDM Class Browser"
            ttype = "Class"
        if self.type == "datatype":
            title = "NIDM Datatype Property Browser"
            ttype = "Datatype"
        if self.type == "annotation":
            title = "NIDM Annotation Property Browser"
            ttype = "Annotation"
        if self.type == "object":
            title = "NIDM Object Property Browser"
            ttype = "Object"
        if self.type == "individual":
            title = "NIDM Named Individual Browser"
            ttype = "Individual"

        schema_open = codecs.open(schema_file, 'w', "utf-8")
        schema_open.write("""
        <!DOCTYPE html>
        <html lang="en-us">
        <head>
            <meta charset="UTF-8">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3" crossorigin="anonymous">
            <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>

            <link rel="stylesheet" href="https://ajax.googleapis.com/ajax/libs/jqueryui/1.12.1/themes/smoothness/jquery-ui.css">
            <script src="https://ajax.googleapis.com/ajax/libs/jqueryui/1.12.1/jquery-ui.min.js"></script>

            <link rel="stylesheet" type="text/css" href="stylesheet/schema.css" media="screen">
            <script type="text/javascript" src="stylesheet/schema.js"></script>

            <link rel="stylesheet" type="text/css" href="stylesheet/normalize.css" media="screen">
            <link href='https://fonts.googleapis.com/css?family=Open+Sans:400,700' rel='stylesheet' type='text/css'>
            <link rel="stylesheet" type="text/css" href="stylesheet/stylesheet.css" media="screen">
            <link rel="stylesheet" type="text/css" href="stylesheet/github-light.css" media="screen">
        </head>
        <body>
            <section class="page-header">
                <h1 class="project-name">Schema Browser: """+ttype+"""</h1>
                <a href="schema_class.html" class="btn">Class</a>
                <a href="schema_datatype.html" class="btn">Datatype Property</a>
                <a href="schema_annotation.html" class="btn">Annotation Property</a>
                <a href="schema_object.html" class="btn">Object Property</a>
                <a href="schema_individual.html" class="btn">Named Individual</a>
                <a href="index.html" class="btn">Term Resolution Page</a>
            </section>
            <div class=\"container-fluid\"><section id=\"viewer\">
                <div id="autobox">
                    Search """+ttype+""": <input type="text" id="termSearch" />
                </div>
                
                <h2>"""+title+"""</h2>
                <div class=\"row\">
                <div class=\"col-5\"><div id='schema' class='list-group list-group-root well'>
        """)
        #<div id="info_box">test</div>
        #""")
        schema_open.close()

    def schema_footer(self):
        if self.schema_file != None:
            schema_file = os.path.join(DOC_FOLDER, self.schema_file)

        schema_open = codecs.open(schema_file, 'a', "utf-8")
        schema_open.write("""
                <div class="col-7">
                    <div id="infoBoard" class="border border-primary rounded">
                        <h4 id="title">Term</h4>
                        <p id="description">Definition</p>
                    </div>
                </div>
            </div>
            </section>
            <section class="main-content">
            <footer class="site-footer">
                <span class="site-footer-owner"><a href="https://github.com/incf-nidash/nidm-experiment">NIDM-Experiment</a> is maintained by <a href="https://github.com/wolfborg">wolfborg</a>.</span>
                <span class="site-footer-credits">This page was generated by <a href="https://pages.github.com">GitHub Pages</a> using the <a href="https://github.com/jasonlong/cayman-theme">Cayman theme</a> by <a href="https://twitter.com/jasonlong">Jason Long</a>.</span>
            </footer>   
            </section>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-ka7Sk0Gln4gmtz2MlQnikT1wXgYsOg+OMhuP+IlRH9sENBO0LRn5q+8nbTov4+1p" crossorigin="anonymous"></script>
        </body>
        </html>
        """)
        schema_open.close()


RELPATH = os.path.dirname(os.path.abspath(__file__))
NIDM_ROOT = os.path.abspath(os.path.join(RELPATH ,'..'))
DOC_FOLDER = os.path.join(NIDM_ROOT, 'docs')
INCLUDE_FOLDER = os.path.join(DOC_FOLDER, 'include')
IMPORTS_FOLDER = os.path.abspath(os.path.join(NIDM_ROOT ,'imports'))
TERMS_FOLDER = os.path.join(NIDM_ROOT, 'terms')
RELEASED_TERMS_FOLDER = os.path.join(TERMS_FOLDER, 'releases')

def main():
    owl_file = os.path.join(TERMS_FOLDER, 'nec.owl')
    import_files = glob.glob(os.path.join(IMPORTS_FOLDER, '*.ttl'))

    # check the file exists
    assert os.path.exists(owl_file)

    term_infos = [
        {'prefix': [str(NIDM), 'nidm'], 'owl_file': owl_file},
    ]
    
    OwlNidmHtml(term_infos, import_files, "class")
    OwlNidmHtml(term_infos, import_files, "datatype")
    OwlNidmHtml(term_infos, import_files, "annotation")
    OwlNidmHtml(term_infos, import_files, "object")
    OwlNidmHtml(term_infos, import_files, "individual")

if __name__ == "__main__":
    main()
