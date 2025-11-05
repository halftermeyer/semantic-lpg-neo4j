import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
import rdflib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Neo4j connection details
NEO4J_URI = os.getenv('NEO4J_URI_ONTOLOGY')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME_ONTOLOGY')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD_ONTOLOGY')
NEO4J_DB_NAME = os.getenv('NEO4J_RDF_ONTOLOGY_NAME', 'neo4j')

# TTL file path
TTL_FILE = '../ontologies/movie_graph/movie_graph.ttl'

class Neo4jConnection:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def session(self, database):
        return self.driver.session(database=database)

def delete_all(driver, database):
    """Delete all nodes and relationships in the specified database."""
    try:
        with driver.session(database=database) as session:
            session.run("MATCH (n) DETACH DELETE n")
        print(f"Cleared all data from database: {database}")
    except Exception as e:
        print(f"Error clearing database {database}: {e}")
        raise

def ingest_ttl_to_neo4j(ttl_file, conn, database):
    """Parse TTL and ingest as (:Triple)-[:SUBJECT|PREDICATE|OBJECT]->(:Resource)"""
    g = rdflib.Graph()
    try:
        g.parse(ttl_file, format='turtle')
        logger.info(f"Parsed {len(g)} triples from {ttl_file}")
    except Exception as e:
        logger.error(f"Failed to parse TTL: {e}")
        return

    triples = []
    for s, p, o in g:
        triples.append((str(s), str(p), str(o) if isinstance(o, rdflib.URIRef) else o.value))

    # Batch size for UNWIND
    batch_size = 1000
    for i in range(0, len(triples), batch_size):
        batch = triples[i:i + batch_size]
        cypher = """
        UNWIND $triples AS triple
        MERGE (subj:Resource {uri: triple[0]}) # should be uri or litteral
        MERGE (pred:Resource {uri: triple[1]})
        MERGE (obj:Resource {uri: triple[2]})
        CREATE (t:Triple)
        CREATE (t)-[:SUBJECT]->(subj)
        CREATE (t)-[:PREDICATE]->(pred)
        CREATE (t)-[:OBJECT]->(obj)
        """
        with conn.session(database) as session:
            session.run(cypher, triples=batch)
        logger.info(f"Ingested batch {i//batch_size + 1} of {len(triples)//batch_size + 1}")

def main():
    conn = Neo4jConnection(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)

    try:
        delete_all(conn, NEO4J_DB_NAME)
    except Exception as e:
        print("Failed to clear databases. Exiting.")
        return


    try:
        ingest_ttl_to_neo4j(TTL_FILE, conn, NEO4J_DB_NAME)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()