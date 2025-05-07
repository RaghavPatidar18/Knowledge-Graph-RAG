# from SPARQLWrapper import SPARQLWrapper, JSON
from nl_query_processor import NLQueryProcessor
from kg_store import KnowledgeGraphStore

class QueryEngine:
    def __init__(self, fuseki_url="http://localhost:3030", dataset="kg"):
        self.kg_store = KnowledgeGraphStore(fuseki_url, dataset)
        self.nl_processor = NLQueryProcessor()
    
    def process_natural_language_query(self, question):
        """Process a natural language query and return results"""
        # Convert natural language to SPARQL
        query_type, target = self.nl_processor.extract_question_type(question)
        sparql_query = self.nl_processor.nl_to_sparql(question)
        explanation = self.nl_processor.query_explanation(query_type, target)
        print("Query : " , sparql_query)
        # Execute SPARQL query
        results = self.kg_store.run_query(sparql_query)
        
        # print("result:: ",results)
        # Format results
        formatted_results = self.format_results(results, query_type)
        
        return {
            "question": question,
            "query_type": query_type,
            "target": target,
            "sparql_query": sparql_query,
            "explanation": explanation,
            "results": formatted_results,
            "raw_results": results
        }
    
    def format_results(self, results, query_type):
        """Format SPARQL query results for user-friendly display"""
        if not results or "results" not in results or "bindings" not in results["results"]:
            return []
        
        bindings = results["results"]["bindings"]
        formatted = []
        
        if query_type == "relation":
            for item in bindings:
                formatted.append({
                    "source": item.get("sLabel", {}).get("value", item.get("subject", {}).get("value", "")),
                    "relation": item.get("predicate", {}).get("value", "").split("/")[-1],
                    "target": item.get("oLabel", {}).get("value", item.get("object", {}).get("value", ""))
                })
        
        elif query_type == "attribute":
            for item in bindings:
                predicate = item.get("predicate", {}).get("value", "").split("/")[-1]
                object_value = item.get("objLabel", {}).get("value", item.get("object", {}).get("value", ""))
                
                formatted.append({
                    "attribute": predicate,
                    "value": object_value
                })
        
        else:
            # General format for other query types
            for item in bindings:
                entry = {}
                for key, value in item.items():
                    if key.endswith("Label"):
                        # Use labels for display
                        base_key = key.replace("Label", "")
                        entry[base_key] = value.get("value", "")
                    elif not any(k.startswith(key) and k.endswith("Label") for k in item.keys()):
                        # Only include if there's no corresponding label
                        entry[key] = value.get("value", "")
                formatted.append(entry)
        
        # Update entity cache with any new entities
        if results and "results" in results and "bindings" in results["results"]:
            entities = []
            for binding in results["results"]["bindings"]:
                if "entity" in binding and "label" in binding:
                    entities.append(binding)
            self.nl_processor.update_entity_cache(entities)
        
        return formatted

if __name__ == "__main__":
    engine = QueryEngine()
    
    # Test with some example questions
    test_questions = [
        "What are the various adventure activities ?"
    ]
    
    for question in test_questions:
        results = engine.process_natural_language_query(question)
        
        print(f"Question: {results['question']}")
        print(f"Explanation: {results['explanation']}")
        print("Results:")
        for item in results['results']:
            print(f"  {item}")
        print("-" * 50)