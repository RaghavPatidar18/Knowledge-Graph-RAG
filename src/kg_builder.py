import os
import json
from rdflib import Graph, Literal, RDF, URIRef, Namespace, BNode
from rdflib.namespace import FOAF, XSD, RDFS

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class KnowledgeGraphBuilder:
    def __init__(self):
        self.g = Graph()
        
        # Define namespaces
        self.ex = Namespace("http://example.org/")
        self.schema = Namespace("http://schema.org/")
        
        # Bind namespaces
        self.g.bind("ex", self.ex)
        self.g.bind("schema", self.schema)
        
    
    def create_uri_for_entity(self, entity_id, entity_type):
        """Create a URI for an entity based on its ID and type"""
        # Clean the entity ID to ensure valid URI
        clean_id = entity_id.replace(" ", "_").replace(",", "").replace(".", "")
        return self.ex[entity_type+"/"+clean_id]
        # Map entity types to namespaces
        # if entity_type in ["PERSON", "PER"]:
        #     return self.ex["person/" + clean_id]
        # elif entity_type in ["ORG", "ORGANIZATION"]:
        #     return self.ex["organization/" + clean_id]
        # elif entity_type in ["LOC", "GPE", "LOCATION"]:
        #     return self.ex["location/" + clean_id]
        # elif entity_type in ["DATE", "TIME"]:
        #     return self.ex["date/" + clean_id]
        # else:
        #     return self.ex["concept/" + clean_id]
    
    def build_from_extracted_data(self, knowledge_data=None):
        """Build knowledge graph from extracted data"""
        if knowledge_data is None:
            knowledge_data = os.path.join(base_dir, "data/extracted/combined_knowledge.json")
        if isinstance(knowledge_data, str):
            # If input is a file path
            with open(knowledge_data, 'r') as f:
                knowledge_data = json.load(f)
        
        # Add entities to graph
        entity_uris = {}
        for entity_id, entity_info in knowledge_data["entities"].items():
            entity_type = entity_info["type"]
            entity_text = entity_info["text"]
            
            # Create URI for entity
            entity_uri = self.create_uri_for_entity(entity_id, entity_type)
            entity_uris[entity_id] = entity_uri
            
            # Add entity to graph
            self.g.add((entity_uri, RDF.type, self.ex[entity_type]))
            self.g.add((entity_uri, RDFS.label, Literal(entity_text)))
        # print(entity_uris)
        # Add relations to graph
        for relation in knowledge_data["relations"]:
            source_id = relation["source"]
            target_id = relation["target"]
            relation_type = relation["type"]
            
            if source_id in entity_uris and target_id in entity_uris:
                source_uri = entity_uris[source_id]
                target_uri = entity_uris[target_id]
                
                # Create URI for relation
                relation_uri = self.ex[relation_type]
                
                # Add relation to graph
                self.g.add((source_uri, relation_uri, target_uri))
                
                # Add provenance (sentence)
                if "sentence" in relation:
                    stmt_node = BNode()
                    self.g.add((stmt_node, RDF.type, RDF.Statement))
                    self.g.add((stmt_node, RDF.subject, source_uri))
                    self.g.add((stmt_node, RDF.predicate, relation_uri))
                    self.g.add((stmt_node, RDF.object, target_uri))
                    self.g.add((stmt_node, RDFS.comment, Literal(relation["sentence"])))
                    
        # print("Graph is like :->>>>>>>",self.g)
        print(f"Created knowledge graph with {len(self.g)} triples")
        return self.g
    
    def save_graph(self, output_path=None):
        
        if output_path is None:
            output_path = os.path.join(base_dir, "data/knowledge_graphs/knowledge_graph.ttl")

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save graph
        self.g.serialize(destination=output_path, format="turtle")
        print(f"Saved knowledge graph to {output_path}")
    
    def load_graph(self, input_path):
        """Load knowledge graph from file"""
        self.g = Graph()
        self.g.parse(input_path, format="turtle")
        print(f"Loaded knowledge graph with {len(self.g)} triples")
        return self.g

if __name__ == "__main__":
    builder = KnowledgeGraphBuilder()
    
    # Build knowledge graph from extracted data
    builder.build_from_extracted_data()
    
    # Save knowledge graph
    builder.save_graph()