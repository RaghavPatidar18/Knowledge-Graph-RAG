import os
import re
import json
import spacy
# from sentence_transformers import SentenceTransformer
# import numpy as np
# from collections import defaultdict

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class NLQueryProcessor:
    def __init__(self, entity_cache_file=None):

        if entity_cache_file is None:
            entity_cache_file = os.path.join(base_dir, "data/entity_cache.json")

        # Load language models
        self.nlp = spacy.load("en_core_web_lg")
        
        # Load sentence transformer model for semantic similarity
        # try:
        #     self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        # except:
        #     # If error, download the model
        #     print("Downloading sentence-transformers model...")
        #     os.system("pip install sentence-transformers")
        #     self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Template SPARQL queries
        self.query_templates = {
            "find_entity": """
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                SELECT ?entity ?label ?type WHERE {{
                    ?entity rdfs:label ?label .
                    ?entity a ?type .
                    FILTER(REGEX(?label, "{}", "i"))
                }}
            """,
            "find_relation_between": """
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                SELECT ?subject ?predicate ?object ?sLabel ?oLabel WHERE {{
                    ?subject ?predicate ?object .
                    ?subject rdfs:label ?sLabel .
                    ?object rdfs:label ?oLabel .
                    FILTER(REGEX(?sLabel, "{}", "i"))
                    FILTER(REGEX(?oLabel, "{}", "i"))
                }}
            """,
            "entity_attributes": """
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                SELECT ?predicate ?object ?objLabel WHERE {{
                    ?entity rdfs:label ?label .
                    FILTER(REGEX(?label, "{}", "i"))
                    ?entity ?predicate ?object .
                    OPTIONAL {{ ?object rdfs:label ?objLabel }}
                }}
            """,
            "entity_related": """
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                SELECT ?relation ?entity ?label WHERE {{
                    {{
                        ?subject rdfs:label ?sLabel .
                        ?subject ?relation ?entity .
                        ?entity rdfs:label ?label .
                        FILTER(REGEX(?sLabel, "{}", "i"))
                    }} UNION {{
                        ?entity ?relation ?object .
                        ?entity rdfs:label ?label .
                        ?object rdfs:label ?oLabel .
                        FILTER(REGEX(?oLabel, "{}", "i"))
                    }}
                }}
            """
        }
        
        # Load entity cache
        self.entity_cache = {}
        if os.path.exists(entity_cache_file):
            with open(entity_cache_file, 'r') as f:
                self.entity_cache = json.load(f)
    
    def update_entity_cache(self, entities, cache_file=None):
        """Update the entity cache with new entities"""

        if cache_file is None:
            cache_file = os.path.join(base_dir, "data/entity_cache.json")

        for entity in entities:
            label = entity.get("label", {}).get("value", "")
            uri = entity.get("entity", {}).get("value", "")
            entity_type = entity.get("type", {}).get("value", "")
            
            if label and uri:
                self.entity_cache[label.lower()] = {
                    "uri": uri,
                    "type": entity_type
                }
        
        # Save cache
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(self.entity_cache, f, indent=2)
    
    def extract_question_type(self, question):
        """Determine the type of question being asked"""
        question_lower = question.lower()
        
        # Check for relationship questions
        relation_patterns = [
            r"(relation|relationship) between (.*) and (.*)",
            r"how (?:is|are) (.*) (?:related|connected) to (.*)",
            r"what (?:connects|links) (.*) (?:and|to|with) (.*)"
        ]
        
        for pattern in relation_patterns:
            match = re.search(pattern, question_lower)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    return "relation", (groups[-2], groups[-1])
        
        # Check for attribute questions
        attribute_patterns = [
            r"what (?:is|are) (.*)",
            r"tell me about (.*)",
            r"who (?:is|was) (.*)",
            r"describe (.*)"
        ]
        
        for pattern in attribute_patterns:
            match = re.search(pattern, question_lower)
            if match:
                entity = match.group(1)
                return "attribute", entity
        
        # Extract entities from question for general query
        doc = self.nlp(question)
        entities = [ent.text for ent in doc.ents]
        
        if entities:
            return "entity_related", entities[0]
        
        return "general", None
    
    def nl_to_sparql(self, question):
        """Convert natural language question to SPARQL query"""
        # Process the question
        doc = self.nlp(question)
        
        # Extract question type and target
        q_type, target = self.extract_question_type(question)
        
        # Generate SPARQL query based on question type
        if q_type == "relation" and isinstance(target, tuple) and len(target) == 2:
            entity1, entity2 = target
            return self.query_templates["find_relation_between"].format(entity1, entity2)
        
        elif q_type == "attribute" and target:
            return self.query_templates["entity_attributes"].format(target)
        
        elif q_type == "entity_related" and target:
            return self.query_templates["entity_related"].format(target, target)
        
        else:
            # Extract all named entities from question
            entities = [ent.text for ent in doc.ents]
            
            if entities:
                return self.query_templates["find_entity"].format(entities[0])
            else:
                # Extract key noun phrases if no named entities
                noun_chunks = [chunk.text for chunk in doc.noun_chunks]
                if noun_chunks:
                    return self.query_templates["find_entity"].format(noun_chunks[0])
        
        # Default fallback query
        return self.query_templates["find_entity"].format(question.replace("?", "").strip())
    
    def query_explanation(self, query_type, target):
        """Generate human-readable explanation of the SPARQL query"""
        if query_type == "relation" and isinstance(target, tuple) and len(target) == 2:
            return f"Searching for relationships between '{target[0]}' and '{target[1]}'."
            
        elif query_type == "attribute" and target:
            return f"Looking for attributes and information about '{target}'."
            
        elif query_type == "entity_related" and target:
            return f"Finding entities related to '{target}'."
            
        else:
            return "Performing a general search based on keywords in your question."

if __name__ == "__main__":
    processor = NLQueryProcessor()
    
    # Test with some example questions
    test_questions = [
        "What is the relationship between Apple and Microsoft?",
        "Who is Tim Cook?",
        "What companies are in the technology sector?",
        "How is Amazon related to e-commerce?"
    ]
    
    for question in test_questions:
        query_type, target = processor.extract_question_type(question)
        sparql = processor.nl_to_sparql(question)
        
        print(f"Question: {question}")
        print(f"Type: {query_type}, Target: {target}")
        print(f"SPARQL: {sparql}")
        print(f"Explanation: {processor.query_explanation(query_type, target)}")
        print("-" * 50)