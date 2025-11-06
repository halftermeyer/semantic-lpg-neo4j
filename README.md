# Semantic LPG Reasoning

![Movie Graph](media/arrows_app_movie_graph_ontology.png)

**NeoOWL** brings OWL-inspired semantics and reasoning to Neo4j’s LPG, extending some of Jesus Barrasa’s “Going Meta” [work](https://github.com/jbarrasa/goingmeta/tree/main/session04).

## Disclaimer

- This is a prototype
- The code is untested and very far from production-grade
- It's not supported by Neo4j
- It's not supported by anyone

## Why NeoOWL?

Overcomes RDF/OWL limits (inflexibility, expertise scarcity, slow iteration, transactional gaps) with Neo4j’s flexibility, accessibility, and CDC integration.

## Ontology Meta-Model: Parallel with OWL

The meta-model encodes OWL-like semantics in LPG:
- **Classes**: `Label` nodes (e.g., `Actor`), with `SCO` for `rdfs:subClassOf`.
- **Dynamic Classes**: `PatternDefinedLabel` (e.g., `_PersonActedInSome`).
- **Properties**: `Relationship` nodes (e.g., `ACTED_IN`), with `IMPLIES` for `rdfs:subPropertyOf`.
- **Computed Values**: `PatternDefinedNodeProperty` (e.g., `kb_number`).

## Comparing RDF/OWL to LPG approach

| RDF/OWL Construct                | LPG Equivalent                       | Example Cypher                          |
|----------------------------------|-----------------------------------------|-----------------------------------------|
| `rdfs:subClassOf`                | `SCO` relationship                      | `CREATE (:Label {name: "Actor"})-[:SCO]->(:Label {name: "Person"})` |
| `rdf:domain` / `rdf:range`       | `SOURCE` / `TARGET` relationships       | `CREATE (person)<-[:SOURCE]-(:Relationship {name: "ACTED_IN"})-[:TARGET]->(movie)` |
| `rdfs:subPropertyOf`             | `IMPLIES` relationship                  | `CREATE (:Relationship {name: "ACTED_IN"})-[:IMPLIES]->(:Relationship {name: "INVOLVED_IN"})` |
| `owl:SymmetricProperty`          | `:Symmetric` label                      | `CREATE (:Relationship:Symmetric {name: "COACTOR"})` |
| `owl:someValuesFrom`             | `PatternDefinedLabel`                   | `CREATE (:PatternDefinedLabel:Label {name: "_PersonActedInSome", pattern: "(p:Person) WHERE EXISTS {(p)-[:ACTED_IN]->()}"})` |
| `owl:DatatypeProperty` (computed)| `PatternDefinedNodeProperty`            | `CREATE (:Label {name: "Actor"})-[:HAS_PROPERTY]->(:Property:PatternDefinedNodeProperty {name: "kb_number", pattern: "SHORTEST 1 (x)-[ca:COACTOR]-*(y:_KevinBacon) WITH ca LIMIT 1 WITH size(ca) AS kbn"})` |


## Installation

### Prerequisites
- Neo4j AuraDB (Business Critical+ with CDC ON)
- Python 3.8+ (`pip install neo4j`)

### Steps
1. Clone: `git clone https://github.com/yourusername/neoowl.git`
2. Configure: Copy `.env.example` to `.env`, set Neo4j credentials.
3. Ingest movie graph data and ontology: `python scripts/ingest_databases.py`
4. Run inference script until convergence: `python scripts/infer_to_convergence.py`
5. Launch **Neoowl** inference server: `python scripts/neoowl_server.py`

## Usage

1. Run query to create a new node:
```cypher
MATCH (m:Movie {title: "Top Gun"})
CREATE (p:Person {name: "Jesus Barrasa"})
MERGE (p)-[:ACTED_IN]->(m)
```
2. Inspect the new node:
```cypher
MATCH (p:Person {name: "Jesus Barrasa"})
RETURN p
```

### Demo (video)

[![Ontology inference engine demo](https://img.youtube.com/vi/wnMCs-knI0Y/0.jpg)](https://www.youtube.com/watch?v=wnMCs-knI0Y)

## Acknowledgments

- Jesus Barrasa
- Neo4j Community

---
*Last Updated: February 20, 2025*
