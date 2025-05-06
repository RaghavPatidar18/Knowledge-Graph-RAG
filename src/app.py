import os
import argparse
from pdf_extractor import PDFKnowledgeExtractor
from kg_builder import KnowledgeGraphBuilder
from kg_store import KnowledgeGraphStore
from query_engine import QueryEngine

def process_pdfs(pdf_dir, output_dir):
    """Process PDFs and extract knowledge"""
    extractor = PDFKnowledgeExtractor()
    knowledge = extractor.process_directory(pdf_dir, output_dir)
    return knowledge

def build_knowledge_graph(knowledge_data, output_path):
    """Build knowledge graph from extracted data"""
    builder = KnowledgeGraphBuilder()
    builder.build_from_extracted_data(knowledge_data)
    builder.save_graph(output_path)
    return builder.g

def upload_to_fuseki(graph_file):
    """Upload knowledge graph to Fuseki"""
    store = KnowledgeGraphStore()
    success = store.upload_graph(graph_file=graph_file)
    return success

def query_interface():
    """Interactive query interface"""
    engine = QueryEngine()
    
    print("\n" + "=" * 50)
    print("Knowledge Graph Query System")
    print("=" * 50)
    print("Type 'exit' to quit the system")
    print("=" * 50)
    
    while True:
        question = input("\nAsk a question: ")
        
        if question.lower() in ['exit', 'quit', 'q']:
            break
        
        # Process the question
        print("\nProcessing your question...")
        results = engine.process_natural_language_query(question)
        
        # Display explanation
        print(f"\n{results['explanation']}")
        
        # Display formatted results
        if results['results']:
            print("\nResults:")
            for i, item in enumerate(results['results'], 1):
                print(f"\n--- Result {i} ---")
                for key, value in item.items():
                    # Format the display of URIs
                    if isinstance(value, str) and value.startswith('http'):
                        value = value.split('/')[-1]
                    print(f"{key.capitalize()}: {value}")
        else:
            print("\nNo results found. Try rephrasing your question.")
        
        # Optionally show SPARQL query for debugging
        print("\n" + "-" * 50)
        print("Debug info:")
        print(f"SPARQL query used: {results['sparql_query']}")
        print("-" * 50)

def run_full_pipeline(pdf_dir, output_dir, graph_file):
    """Run the full pipeline from PDFs to knowledge graph"""
    print("Step 1: Processing PDFs...")
    knowledge = process_pdfs(pdf_dir, output_dir)
    
    print("\nStep 2: Building knowledge graph...")
    knowledge_file = os.path.join(output_dir, "combined_knowledge.json")
    graph = build_knowledge_graph(knowledge_file, graph_file)
    
    print("\nStep 3: Uploading to Fuseki server...")
    success = upload_to_fuseki(graph_file)
    
    if success:
        print("\nKnowledge graph successfully created and uploaded!")
        return True
    else:
        print("\nError uploading to Fuseki. Please check if the server is running.")
        return False

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='PDF Knowledge Graph System')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Full pipeline command
    pipeline_parser = subparsers.add_parser('pipeline', help='Run the full pipeline')
    pipeline_parser.add_argument('--pdf-dir', default='data/pdfs', help='Directory containing PDF files')
    pipeline_parser.add_argument('--output-dir', default='data/extracted', help='Directory for extracted data')
    pipeline_parser.add_argument('--graph-file', default='data/knowledge_graphs/knowledge_graph.ttl', help='Output path for knowledge graph')
    
    # Process PDFs command
    process_parser = subparsers.add_parser('process', help='Process PDFs only')
    process_parser.add_argument('--pdf-dir', default='data/pdfs', help='Directory containing PDF files')
    process_parser.add_argument('--output-dir', default='data/extracted', help='Directory for extracted data')
    
    # Build KG command
    build_parser = subparsers.add_parser('build', help='Build knowledge graph from extracted data')
    build_parser.add_argument('--input-file', default='data/extracted/combined_knowledge.json', help='Input JSON file with extracted data')
    build_parser.add_argument('--graph-file', default='data/knowledge_graphs/knowledge_graph.ttl', help='Output path for knowledge graph')
    
    # Upload command
    upload_parser = subparsers.add_parser('upload', help='Upload knowledge graph to Fuseki')
    upload_parser.add_argument('--graph-file', default='data/knowledge_graphs/knowledge_graph.ttl', help='Path to knowledge graph file')
    
    # Query command
    subparsers.add_parser('query', help='Start interactive query interface')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute the appropriate command
    if args.command == 'pipeline':
        run_full_pipeline(args.pdf_dir, args.output_dir, args.graph_file)
    
    elif args.command == 'process':
        print("Processing PDFs...")
        process_pdfs(args.pdf_dir, args.output_dir)
        print("Processing complete!")
    
    elif args.command == 'build':
        print("Building knowledge graph...")
        build_knowledge_graph(args.input_file, args.graph_file)
        print(f"Knowledge graph built and saved to {args.graph_file}")
    
    elif args.command == 'upload':
        print("Uploading knowledge graph to Fuseki...")
        success = upload_to_fuseki(args.graph_file)
        if success:
            print("Upload successful!")
        else:
            print("Upload failed. Check if Fuseki server is running.")
    
    elif args.command == 'query':
        query_interface()
    
    else:
        # If no command is specified, show help
        parser.print_help()

if __name__ == "__main__":
    # Make sure directories exist
    os.makedirs("data/pdfs", exist_ok=True)
    os.makedirs("data/extracted", exist_ok=True)
    os.makedirs("data/knowledge_graphs", exist_ok=True)
    
    # Run main function
    main()