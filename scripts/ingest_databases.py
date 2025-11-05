import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Main database connection details
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DB_NAME = os.getenv("NEO4J_DB_NAME", "neo4j")  # Default to "neo4j" if not set

# Ontology database connection details
NEO4J_URI_ONTOLOGY = os.getenv("NEO4J_URI_ONTOLOGY", NEO4J_URI)  # Fallback to main URI
NEO4J_USERNAME_ONTOLOGY = os.getenv("NEO4J_USERNAME_ONTOLOGY", NEO4J_USERNAME)
NEO4J_PASSWORD_ONTOLOGY = os.getenv("NEO4J_PASSWORD_ONTOLOGY", NEO4J_PASSWORD)
NEO4J_ONTOLOGY_DB_NAME = os.getenv("NEO4J_ONTOLOGY_DB_NAME", "movie_ontology")

# Cypher file paths
DATA_CYPHER_FILE = "../data/movie_graph.cypher"
ONTOLOGY_CYPHER_FILE = "../ontologies/movie_graph/human_readable_movie_graph_ontology.cypher"

def delete_all(driver, database):
    """Delete all nodes and relationships in the specified database."""
    try:
        with driver.session(database=database) as session:
            session.run("MATCH (n) DETACH DELETE n")
        print(f"Cleared all data from database: {database}")
    except Exception as e:
        print(f"Error clearing database {database}: {e}")
        raise

def ingest_cypher_file(driver, database, cypher_file):
    """Read and execute Cypher commands from a file in the specified database."""
    try:
        with open(cypher_file, "r") as file:
            cypher_content = file.read()
            # Split into individual statements (assuming semicolon-separated)
            statements = [stmt.strip() for stmt in cypher_content.split(";") if stmt.strip()]
        
        with driver.session(database=database) as session:
            for statement in statements:
                session.run(statement)
        print(f"Successfully ingested {cypher_file} into database: {database}")
    except FileNotFoundError:
        print(f"Error: File {cypher_file} not found")
        raise
    except Exception as e:
        print(f"Error ingesting {cypher_file} into {database}: {e}")
        raise

def main():
    # Initialize drivers for both databases
    try:
        driver_main = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
        #driver_ontology = GraphDatabase.driver(
        #    NEO4J_URI_ONTOLOGY,
        #    auth=(NEO4J_USERNAME_ONTOLOGY, NEO4J_PASSWORD_ONTOLOGY)
        #)
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
        return

    # Delete all data from both databases
    try:
        delete_all(driver_main, NEO4J_DB_NAME)
        #delete_all(driver_ontology, NEO4J_ONTOLOGY_DB_NAME)
    except Exception as e:
        print("Failed to clear databases. Exiting.")
        driver_main.close()
        #driver_ontology.close()
        return

    # Ingest data into respective databases
    try:
        ingest_cypher_file(driver_main, NEO4J_DB_NAME, DATA_CYPHER_FILE)
        #ingest_cypher_file(driver_ontology, NEO4J_ONTOLOGY_DB_NAME, ONTOLOGY_CYPHER_FILE)
    except Exception as e:
        print("Failed to ingest data. Exiting.")
    finally:
        # Close connections
        driver_main.close()
        #driver_ontology.close()

if __name__ == "__main__":
    main()