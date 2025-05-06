import os
import json
import fitz  # PyMuPDF
import spacy
from collections import defaultdict
import re

class PDFKnowledgeExtractor:
    def __init__(self, models_dir="models"):
        # Load SpaCy model for NER (Named Entity Recognition)
        try:
            self.nlp = spacy.load("en_core_web_lg")
        except:
            # Download if not available
            print("Downloading SpaCy model...")
            os.system("python -m spacy download en_core_web_lg")
            self.nlp = spacy.load("en_core_web_lg")
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF file"""
        text = ""
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()
            print(f"Extracted {len(text)} characters from {pdf_path}")
            return text
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def preprocess_text(self, text):
        """Clean and preprocess extracted text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters
        text = re.sub(r'[^\w\s\.\,\;\:\(\)\[\]\{\}\"\'\-]', '', text)
        return text
    
    def extract_entities_and_relations(self, text):
        """Extract entities and potential relationships from text"""
        # Process with SpaCy
        doc = self.nlp(text)
        
        # Extract entities
        entities = {}
        for ent in doc.ents:
            entity_id = f"{ent.label_}_{ent.text.replace(' ', '_')}"
            entities[entity_id] = {
                "text": ent.text,
                "type": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char
            }
        
        # Extract potential relationships
        relations = []
        sentences = list(doc.sents)
        
        for sent in sentences:
            sent_entities = [ent for ent in doc.ents if ent.start >= sent.start and ent.end <= sent.end]
            
            if len(sent_entities) >= 2:
                for i, entity1 in enumerate(sent_entities[:-1]):
                    for entity2 in sent_entities[i+1:]:
                        # Find verbs or prepositions between entities
                        between_tokens = [token for token in doc if entity1.end <= token.i < entity2.start]
                        verbs = [token.lemma_ for token in between_tokens if token.pos_ == "VERB"]
                        
                        relation_type = "related_to"
                        if verbs:
                            relation_type = "_".join(verbs)
                        
                        entity1_id = f"{entity1.label_}_{entity1.text.replace(' ', '_')}"
                        entity2_id = f"{entity2.label_}_{entity2.text.replace(' ', '_')}"
                        
                        relations.append({
                            "source": entity1_id,
                            "target": entity2_id,
                            "type": relation_type,
                            "sentence": sent.text
                        })
        
        return {
            "entities": entities,
            "relations": relations
        }
    
    def process_pdf(self, pdf_path, output_dir="data/extracted"):
        """Process PDF and extract knowledge"""
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract text from PDF
        text = self.extract_text_from_pdf(pdf_path)
        
        if not text:
            return None
        
        # Preprocess text
        text = self.preprocess_text(text)
        
        # Extract entities and relations
        knowledge = self.extract_entities_and_relations(text)
        
        # Save extracted knowledge
        pdf_name = os.path.basename(pdf_path).replace('.pdf', '')
        output_path = os.path.join(output_dir, f"{pdf_name}_knowledge.json")
        
        with open(output_path, 'w') as f:
            json.dump(knowledge, f, indent=2)
        
        print(f"Extracted {len(knowledge['entities'])} entities and {len(knowledge['relations'])} relations")
        print(f"Saved to {output_path}")
        
        return knowledge
    
    def process_directory(self, pdf_dir=None, output_dir=None):
        
        all_knowledge = {
            "entities": {},
            "relations": []
        }
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  
        # print(base_dir)
        if pdf_dir is None:
            pdf_dir = os.path.join(base_dir, "data/pdfs")
        if output_dir is None:
            output_dir = os.path.join(base_dir, "data/extracted")

        for filename in os.listdir(pdf_dir):
            if filename.lower().endswith('.pdf'):
                pdf_path = os.path.join(pdf_dir, filename)
                knowledge = self.process_pdf(pdf_path, output_dir)
                # print(knowledge)
                if knowledge:
                    # Merge knowledge
                    all_knowledge["entities"].update(knowledge["entities"])
                    all_knowledge["relations"].extend(knowledge["relations"])
        
        # Save combined knowledge
        output_path = os.path.join(output_dir, "combined_knowledge.json")
        with open(output_path, 'w') as f:
            json.dump(all_knowledge, f, indent=2)
        
        print(f"Combined knowledge saved to {output_path}")
        return all_knowledge

if __name__ == "__main__":
    extractor = PDFKnowledgeExtractor()
    
    # Process a single PDF
    # extractor.process_pdf("data/pdfs/example.pdf")
    
    # Process all PDFs in directory
    extractor.process_directory()