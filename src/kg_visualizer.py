from pyvis.network import Network
from SPARQLWrapper import SPARQLWrapper, JSON
# import pandas as pd

class PyvisKGVisualizer:
    def __init__(self, sparql_endpoint="http://localhost:3030/testkg/sparql"):
        self.sparql = SPARQLWrapper(sparql_endpoint)
        self.sparql.setReturnFormat(JSON)
    
    def fetch_kg_data(self):
        """Fetch knowledge graph data from SPARQL endpoint"""
        query = """
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX ex: <http://example.org/>
        
        SELECT ?s ?p ?o ?sLabel ?oLabel
        WHERE {
            ?s ?p ?o .
            OPTIONAL { ?s foaf:name ?sLabel }
            OPTIONAL { ?o foaf:name ?oLabel }
            OPTIONAL { 
                FILTER(!BOUND(?sLabel))
                ?s ex:name ?sLabel 
            }
            OPTIONAL { 
                FILTER(!BOUND(?oLabel))
                ?o ex:name ?oLabel 
            }
        }
        """
        
        self.sparql.setQuery(query)
        results = self.sparql.query().convert()
        
        edges = []
        for result in results["results"]["bindings"]:
            s = result["s"]["value"]
            p = result["p"]["value"]
            o = result["o"]["value"]
            
            # Use labels if available, otherwise use URIs
            s_label = result["sLabel"]["value"] if "sLabel" in result else s.split('/')[-1]
            o_label = result["oLabel"]["value"] if "oLabel" in result else o.split('/')[-1]
            p_label = p.split('/')[-1]
            
            edges.append((s, o, p_label, s_label, o_label))
            
        return edges
    
    def visualize(self, filename="kg_visualization.html", height="600px", width="100%"):
        """Create an interactive visualization"""
        # Get graph data
        edges = self.fetch_kg_data()
        
        # Create network
        net = Network(height=height, width=width, directed=True, notebook=False)
        
        # Track nodes to avoid duplicates
        added_nodes = set()
        
        # Add nodes and edges
        for source, target, relation, source_label, target_label in edges:
            # Add source node if not already added
            if source not in added_nodes:
                net.add_node(source, label=source_label, title=source)
                added_nodes.add(source)
            
            # Add target node if not already added
            if target not in added_nodes:
                net.add_node(target, label=target_label, title=target)
                added_nodes.add(target)
            
            # Add edge
            net.add_edge(source, target, label=relation, title=relation)
        
        # Set physics layout
        net.barnes_hut()
        
        # Save visualization
        net.show(filename)
        print(f"Interactive visualization saved as '{filename}'")

if __name__ == "__main__":
    
    visualizer = PyvisKGVisualizer()
    visualizer.visualize()