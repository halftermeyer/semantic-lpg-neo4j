import os
import logging
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Neo4j connection details
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DB_NAME = os.getenv("NEO4J_DB_NAME", "neo4j")
NEO4J_URI_ONTOLOGY = os.getenv("NEO4J_URI_ONTOLOGY", NEO4J_URI)
NEO4J_USERNAME_ONTOLOGY = os.getenv("NEO4J_USERNAME_ONTOLOGY", NEO4J_USERNAME)
NEO4J_PASSWORD_ONTOLOGY = os.getenv("NEO4J_PASSWORD_ONTOLOGY", NEO4J_PASSWORD)
NEO4J_ONTOLOGY_DB_NAME = os.getenv("NEO4J_ONTOLOGY_DB_NAME", "movie_ontology")

class Neo4jConnection:
    """Manage Neo4j connections."""
    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self.driver.close()

    def session(self, database):
        return self.driver.session(database=database)

class NeoOWLReasoner:
    """Forward-chaining reasoner for NeoOWL."""
    def __init__(self, main_conn, ontology_conn):
        self.main_conn = main_conn
        self.ontology_conn = ontology_conn
        self.rules = self._generate_all_rules()

    def _generate_pattern_defined_label_rules(self):
        records, _, _ = self.ontology_conn.driver.execute_query(
            """MATCH (mdl:PatternDefinedLabel)
            RETURN mdl.name AS name, mdl.pattern AS pattern, mdl.classElementVariable AS classElementVariable""",
            database_=NEO4J_ONTOLOGY_DB_NAME
        )
        return [f"""MATCH {record['pattern']}
                    CALL ({record['classElementVariable']}) {{
                        SET {record['classElementVariable']}:{record['name']}
                    }} IN TRANSACTIONS OF 100 ROWS"""
                for record in records]

    def _generate_pattern_defined_relationship_rules(self):
        records, _, _ = self.ontology_conn.driver.execute_query(
            """MATCH (mdr:PatternDefinedRelationship)
            RETURN mdr.name AS name, mdr.pattern AS pattern, mdr.sourceElementVariable AS sourceElementVariable, mdr.targetElementVariable AS targetElementVariable""",
            database_=NEO4J_ONTOLOGY_DB_NAME
        )
        return [f"""MATCH {record['pattern']}
                    CALL ({record['sourceElementVariable']}, {record['targetElementVariable']}) {{
                        MERGE ({record['sourceElementVariable']})-[:{record['name']}]->({record['targetElementVariable']})
                    }} IN TRANSACTIONS OF 100 ROWS"""
                for record in records]

    def _generate_sco_label_rules(self):
        records, _, _ = self.ontology_conn.driver.execute_query(
            """MATCH (narrower:Label)-[:SCO]->(broader:Label)
            RETURN narrower.name AS narrower, broader.name AS broader""",
            database_=NEO4J_ONTOLOGY_DB_NAME
        )
        return [f"""MATCH (n:{record['narrower']})
                    CALL (n) {{
                        SET n:{record['broader']}
                    }} IN CONCURRENT TRANSACTIONS OF 100 ROWS"""
                for record in records]

    def _generate_implies_relationship_rules(self):
        records, _, _ = self.ontology_conn.driver.execute_query(
            """MATCH (narrower:Relationship)-[:IMPLIES]->(broader:Relationship)
            RETURN narrower.name AS narrower, broader.name AS broader""",
            database_=NEO4J_ONTOLOGY_DB_NAME
        )
        return [f"""MATCH (n)-[:{record['narrower']}]->(m)
                    CALL (n, m) {{
                        MERGE (n)-[:{record['broader']}]->(m)
                    }} IN TRANSACTIONS OF 100 ROWS"""
                for record in records]

    def _generate_equivalent_label_rules(self):
        records, _, _ = self.ontology_conn.driver.execute_query(
            """MATCH (l1:Label)-[:EQUIVALENT]->(l2:Label)
            RETURN l1.name AS l1, l2.name AS l2""",
            database_=NEO4J_ONTOLOGY_DB_NAME
        )
        return [f"""MATCH (n:{record['l1']}|{record['l2']})
                    CALL (n) {{
                        SET n:{record['l1']}:{record['l2']}
                    }} IN CONCURRENT TRANSACTIONS OF 100 ROWS"""
                for record in records]

    def _generate_equivalent_relationship_rules(self):
        records, _, _ = self.ontology_conn.driver.execute_query(
            """MATCH (r1:Relationship)-[:EQUIVALENT]->(r2:Relationship)
            RETURN r1.name AS r1, r2.name AS r2""",
            database_=NEO4J_ONTOLOGY_DB_NAME
        )
        return [f"""MATCH (n)-[:{record['r1']}|{record['r2']}]->(m)
                    CALL (n, m) {{
                        MERGE (n)-[:{record['r1']}]->(m)
                        MERGE (n)-[:{record['r2']}]->(m)
                    }} IN TRANSACTIONS OF 100 ROWS"""
                for record in records]

    def _generate_symmetric_relationship_rules(self):
        records, _, _ = self.ontology_conn.driver.execute_query(
            """MATCH (r:Relationship:Symmetric)
            RETURN r.name AS sim_rel""",
            database_=NEO4J_ONTOLOGY_DB_NAME
        )
        return [f"""MATCH (n)-[:{record['sim_rel']}]->(m)
                    CALL (n, m) {{
                        MERGE (m)-[:{record['sim_rel']}]->(n)
                    }} IN TRANSACTIONS OF 100 ROWS"""
                for record in records]

    def _generate_pattern_defined_property_rules(self):
        records, _, _ = self.ontology_conn.driver.execute_query(
            """MATCH (n:Label)-[:HAS_PROPERTY]->(qdp:PatternDefinedNodeProperty)
            RETURN n.name AS label, qdp.name AS property_name, qdp.pattern AS pattern, qdp.propertyOwnerVariable AS variable, qdp.valueVariable AS val_variable""",
            database_=NEO4J_ONTOLOGY_DB_NAME
        )
        return [f"""MATCH ({record['variable']}:{record['label']})
                    CALL ({record['variable']}) {{
                        MATCH {record['pattern']}
                        WITH {record['variable']}, {record['val_variable']}
                        WHERE {record['variable']}.{record['property_name']} IS NULL OR {record['variable']}.{record['property_name']} <> {record['val_variable']}
                        SET {record['variable']}.{record['property_name']} = {record['val_variable']}
                    }} IN CONCURRENT TRANSACTIONS OF 100 ROWS"""
                for record in records]

    def _generate_all_rules(self):
        """Generate all inference rules."""
        try:
            rule_generators = [
                self._generate_pattern_defined_label_rules,
                self._generate_pattern_defined_relationship_rules,
                self._generate_sco_label_rules,
                self._generate_implies_relationship_rules,
                self._generate_equivalent_label_rules,
                self._generate_equivalent_relationship_rules,
                self._generate_symmetric_relationship_rules,
                self._generate_pattern_defined_property_rules
            ]
            all_rules = []
            for gen in rule_generators:
                all_rules.extend(gen())
            logger.info(f"Generated {len(all_rules)} inference rules")
            return all_rules
        except Exception as e:
            logger.error(f"Failed to generate rules: {e}")
            raise

    def infer_to_convergence(self, params=None):
        """Run inference rules until convergence."""
        params = params or {}
        iteration = 0
        try:
            while True:
                iteration += 1
                any_update = False
                with self.main_conn.session(NEO4J_DB_NAME) as session:
                    for rule in self.rules:
                        result = session.run(rule, params)
                        any_new_update = result.consume().counters.contains_updates
                        any_update = any_update or any_new_update
                logger.info(f"Iteration {iteration}: {'Updates applied' if any_update else 'No updates'}")
                if not any_update:
                    break
            logger.info("Inference converged")
        except Exception as e:
            logger.error(f"Error during inference: {e}")
            raise

def main():
    """Perform inference until convergence."""
    try:
        # Initialize connections
        main_conn = Neo4jConnection(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
        ontology_conn = Neo4jConnection(NEO4J_URI_ONTOLOGY, NEO4J_USERNAME_ONTOLOGY, NEO4J_PASSWORD_ONTOLOGY)
        logger.info("Connected to Neo4j databases")

        # Run inference to convergence
        reasoner = NeoOWLReasoner(main_conn, ontology_conn)
        reasoner.infer_to_convergence()
    except Exception as e:
        logger.error(f"Inference failed: {e}")
    finally:
        main_conn.close()
        ontology_conn.close()
        logger.info("Connections closed")

if __name__ == "__main__":
    main()