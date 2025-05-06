import rdflib
from rdflib import Graph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import FOAF, XSD
import requests
from SPARQLWrapper import SPARQLWrapper, JSON

class KnowledgeGraphLoader:
    def __init__(self, fuseki_url="http://localhost:3030"):
        self.fuseki_url = fuseki_url
        self.dataset = "testkg"
        self.sparql_endpoint = f"{fuseki_url}/{self.dataset}/sparql"
        self.update_endpoint = f"{fuseki_url}/{self.dataset}/update"
        self.g = Graph()
        
        # Define namespaces
        self.ex = Namespace("http://example.org/")
        self.g.bind("ex", self.ex)
        self.g.bind("foaf", FOAF)
    
    def create_sample_data(self):
        """Create some sample triples for a knowledge graph"""
        # Add people
        self.g.add((self.ex.Alice, RDF.type, FOAF.Person))
        self.g.add((self.ex.Alice, FOAF.name, Literal("Alice Smith")))
        self.g.add((self.ex.Alice, FOAF.age, Literal(30, datatype=XSD.integer)))
        
        self.g.add((self.ex.Bob, RDF.type, FOAF.Person))
        self.g.add((self.ex.Bob, FOAF.name, Literal("Bob Johnson")))
        self.g.add((self.ex.Bob, FOAF.age, Literal(25, datatype=XSD.integer)))
        
        # Add relationships
        self.g.add((self.ex.Alice, self.ex.knows, self.ex.Bob))
        self.g.add((self.ex.Alice, self.ex.worksAt, self.ex.TechCorp))
        
        # Add organizations
        self.g.add((self.ex.TechCorp, RDF.type, self.ex.Organization))
        self.g.add((self.ex.TechCorp, self.ex.name, Literal("Tech Corporation")))
        
        return self.g
    
    def save_to_file(self, filename="/data/sample_data.ttl"):
        """Save the graph to a Turtle file"""
        # print(self.g)
        self.g.serialize(destination=filename, format="turtle")
        print(f"Data saved to {filename}")
    
    def load_from_file(self, filename="/data/sample_data.ttl"):
        """Load data from a Turtle file"""
        self.g = Graph()
        self.g.parse(filename, format="turtle")
        print(f"Loaded {len(self.g)} triples from {filename}")
        return self.g
    
    def upload_to_fuseki(self):
        """Upload the graph to Fuseki server"""
        data = self.g.serialize(format="turtle")
        # print(data)
        # Upload data
        headers = {"Content-Type": "text/turtle"}
        response = requests.post(
            f"{self.fuseki_url}/{self.dataset}/data", 
            data=data, 
            headers=headers
        )
        # print(response)
        if response.status_code == 200 or response.status_code == 201:
            print(f"Successfully uploaded {len(self.g)} triples to Fuseki")
            return True
        else:
            print(response)
            print(f"Failed to upload data: {response.status_code}")
            return False

if __name__ == "__main__":
    loader = KnowledgeGraphLoader()
    
    # Create sample data
    loader.create_sample_data()
    
    # Save to file
    loader.save_to_file()

    #load from file
    loader.load_from_file()
    
    # Upload to Fuseki
    loader.upload_to_fuseki()