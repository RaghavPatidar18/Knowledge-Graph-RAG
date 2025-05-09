import os
import requests
from rdflib import Graph
from SPARQLWrapper import SPARQLWrapper, JSON

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class KnowledgeGraphStore:
    def __init__(self, fuseki_url="http://localhost:3030", dataset="kg"):
        self.fuseki_url = fuseki_url
        self.dataset = dataset
        self.sparql_endpoint = f"{fuseki_url}/{dataset}/sparql"
        self.update_endpoint = f"{fuseki_url}/{dataset}/update"
        self.data_endpoint = f"{fuseki_url}/{dataset}/data"
    
    def upload_graph(self, graph=None, graph_file=None):
        """Upload a knowledge graph to Fuseki"""

        if graph_file is None:
            graph_file = os.path.join(base_dir, "data/knowledge_graphs/knowledge_graph.ttl")

        if graph is None and graph_file is None:
            raise ValueError("Either graph or graph_file must be provided")
        
        # Load graph from file if provided
        if graph is None and graph_file is not None:
            graph = Graph()
            graph.parse(graph_file, format="turtle")
        
        # Serialize the graph to Turtle format
        data = graph.serialize(format="turtle")
        
        # # Clear the dataset first (optional)
        # clear_query = "CLEAR ALL"
        # headers = {"Content-Type": "application/sparql-update"}
        # response = requests.post(self.update_endpoint, data=clear_query, headers=headers)
        
        # if response.status_code != 200:
        #     print(f"Failed to clear dataset: {response.status_code}")
        #     print(response.text)
        #     return False
        
        # Upload data
        headers = {"Content-Type": "text/turtle"}
        response = requests.post(self.data_endpoint, data=data.encode("utf-8"), headers=headers)
        
        if response.status_code == 200 or response.status_code == 201:
            print(f"Successfully uploaded {len(graph)} triples to Fuseki")
            return True
        else:
            print(f"Failed to upload data: {response.status_code}")
            print(response.text)
            return False
    
    def run_query(self, query):
        """Run a SPARQL query against the Fuseki endpoint"""
        sparql = SPARQLWrapper(self.sparql_endpoint)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        
        try:
            results = sparql.query().convert()
            return results
        except Exception as e:
            print(f"Error executing query: {e}")
            return None
    
    def get_all_entities(self):
        """Get all entities in the knowledge graph"""
        query = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT DISTINCT ?entity ?label ?type
        WHERE {
            ?entity a ?type .
            OPTIONAL { ?entity rdfs:label ?label }
        }
        """
        return self.run_query(query)
    
    def get_all_relations(self):
        """Get all relationships in the knowledge graph"""
        query = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?subject ?predicate ?object ?sLabel ?oLabel
        WHERE {
            ?subject ?predicate ?object .
            
            # Filter out RDF, RDFS and OWL properties
            FILTER(!STRSTARTS(STR(?predicate), "http://www.w3.org/1999/02/22-rdf-syntax-ns#"))
            FILTER(!STRSTARTS(STR(?predicate), "http://www.w3.org/2000/01/rdf-schema#"))
            FILTER(!STRSTARTS(STR(?predicate), "http://www.w3.org/2002/07/owl#"))
            
            
        }
        """
        return self.run_query(query)

if __name__ == "__main__":
    store = KnowledgeGraphStore()
    
    # Upload knowledge graph
    store.upload_graph()
    
    # Test query
    results = store.get_all_entities()
    # print(f"Found {len(results['results']['bindings'])} entities")