from SPARQLWrapper import SPARQLWrapper, JSON
import json

class KnowledgeGraphQuerier:
    def __init__(self, endpoint_url="http://localhost:3030/testkg/sparql"):
        self.sparql = SPARQLWrapper(endpoint_url)
        self.sparql.setReturnFormat(JSON)
    
    def run_query(self, query):
        """Run a SPARQL query and return results"""
        self.sparql.setQuery(query)
        results = self.sparql.query().convert()
        return results
    
    def get_all_people(self):
        """Get all people in the knowledge graph"""
        query = """
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX ex: <http://example.org/>
        
        SELECT ?person ?name ?age
        WHERE {
            ?person a foaf:Person .
            OPTIONAL { ?person foaf:name ?name }
            OPTIONAL { ?person foaf:age ?age }
        }
        """
        return self.run_query(query)
    
    def get_relationships(self):
        """Get all relationships between people"""
        query = """
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX ex: <http://example.org/>
        
        SELECT ?person1 ?name1 ?relationship ?person2 ?name2
        WHERE {
            ?person1 a foaf:Person .
            ?person2 a foaf:Person .
            ?person1 ?relationship ?person2 .
            ?person1 foaf:name ?name1 .
            ?person2 foaf:name ?name2 .
            FILTER(?person1 != ?person2)
        }
        """
        return self.run_query(query)
    
    def pretty_print_results(self, results):
        """Print query results in a readable format"""
        vars = results["head"]["vars"]
        
        print("\n=== Query Results ===")
        for result in results["results"]["bindings"]:
            for var in vars:
                if var in result:
                    print(f"{var}: {result[var]['value']}")
            print("---")

if __name__ == "__main__":
    querier = KnowledgeGraphQuerier()
    
    print("\nQuerying all people:")
    results = querier.get_all_people()
    querier.pretty_print_results(results)
    
    print("\nQuerying relationships:")
    results = querier.get_relationships()
    querier.pretty_print_results(results)