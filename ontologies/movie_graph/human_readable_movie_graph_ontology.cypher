// === Class Definitions ===
// Define the base classes (Labels) in the ontology
CREATE (person:Label {name: "Person"})  // Base class for individuals
CREATE (movie:Label {name: "Movie"})    // Base class for films
CREATE (actor:Label {name: "Actor"})    // Subclass of Person who acts
CREATE (director:Label {name: "Director"})  // Subclass of Person who directs
CREATE (anomalous:Label {name: "Anomalous"})  // Special class for outliers

// === Relationships (Properties) ===
// Define relationships between classes
CREATE (actedIn:Relationship {name: "ACTED_IN"})  // Person acts in a Movie
CREATE (directed:Relationship {name: "DIRECTED"})  // Person directs a Movie
CREATE (involvedIn:Relationship {name: "INVOLVED_IN"})  // General involvement in a Movie
CREATE (coactor:Relationship:Symmetric {name: "COACTOR"})  // Symmetric: Person co-acts with another Person
CREATE (collaborator:Relationship:Symmetric {name: "COLLABORATOR"})  // Symmetric: Person collaborates with another Person

// === Subclass Relationships (SCO: subClassOf) ===
// Establish class hierarchies
CREATE (actor)-[:SCO]->(person)  // Actor is a subclass of Person
CREATE (director)-[:SCO]->(person)  // Director is a subclass of Person

// === Property Domain and Range (SOURCE and TARGET) ===
// Define where relationships originate and terminate
CREATE (actedIn)-[:SOURCE]->(person)  // ACTED_IN starts from Person
CREATE (actedIn)-[:TARGET]->(movie)   // ACTED_IN ends at Movie
CREATE (directed)-[:SOURCE]->(person) // DIRECTED starts from Person
CREATE (directed)-[:TARGET]->(movie)  // DIRECTED ends at Movie
CREATE (involvedIn)-[:SOURCE]->(person)  // INVOLVED_IN starts from Person
CREATE (involvedIn)-[:TARGET]->(movie)   // INVOLVED_IN ends at Movie
CREATE (coactor)-[:SOURCE]->(person)     // COACTOR starts from Person
CREATE (coactor)-[:TARGET]->(person)     // COACTOR ends at Person (symmetric)
CREATE (collaborator)-[:SOURCE]->(person)  // COLLABORATOR starts from Person
CREATE (collaborator)-[:TARGET]->(person)  // COLLABORATOR ends at Person (symmetric)

// === Property Implications (IMPLIES) ===
// Define broader relationships implied by specific ones
CREATE (actedIn)-[:IMPLIES]->(involvedIn)  // ACTED_IN implies INVOLVED_IN
CREATE (directed)-[:IMPLIES]->(involvedIn) // DIRECTED implies INVOLVED_IN
CREATE (coactor)-[:IMPLIES]->(collaborator) // COACTOR implies COLLABORATOR

// === Pattern-Defined Labels (Dynamic Classes) ===
// Define classes based on graph patterns
CREATE (personActedInSome:PatternDefinedLabel:Label {
    name: "_PersonActedInSome",
    pattern: "(p:Person) WHERE EXISTS {(p)-[:ACTED_IN]->()}",
    classElementVariable: "p"
})  // Person who has acted in some movie
CREATE (personDirectedSome:PatternDefinedLabel:Label {
    name: "_PersonDirectedSome",
    pattern: "(p:Person) WHERE EXISTS {(p)-[:DIRECTED]->()}",
    classElementVariable: "p"
})  // Person who has directed some movie
CREATE (kevinBacon:PatternDefinedLabel:Label {
    name: "_KevinBacon",
    pattern: "(p:Person {name: 'Kevin Bacon'})",
    classElementVariable: "p"
})  // Specific instance: Kevin Bacon
CREATE (easterEggActor:PatternDefinedLabel:Label {
    name: "_EasterEggActor",
    pattern: "(p:Person {name: 'Emil Eifrem'})",
    classElementVariable: "p"
})  // Specific instance: Emil Eifrem (Neo4j Easter egg)

// === Equivalence Relationships (EQUIVALENT) ===
// Link pattern-defined labels to their equivalent classes
CREATE (personActedInSome)-[:EQUIVALENT]->(actor)  // _PersonActedInSome is equivalent to Actor
CREATE (personDirectedSome)-[:EQUIVALENT]->(director)  // _PersonDirectedSome is equivalent to Director

// === Pattern-Defined Relationships (Dynamic Properties) ===
// Define relationships based on graph patterns
CREATE (coactorPattern:PatternDefinedRelationship:Relationship:Symmetric {
    name: "_COACTOR",
    pattern: "(s:Person)-[:ACTED_IN]->()<-[:ACTED_IN]-(t:Person)",
    sourceElementVariable: "s",
    targetElementVariable: "t"
})  // Persons who acted in the same movie
CREATE (collaboratorPattern:PatternDefinedRelationship:Relationship:Symmetric {
    name: "_COLLABORATOR",
    pattern: "(s:Person)-[:INVOLVED_IN]->()<-[:INVOLVED_IN]-(t:Person)",
    sourceElementVariable: "s",
    targetElementVariable: "t"
})  // Persons involved in the same movie

// Link pattern-defined relationships to their equivalents
CREATE (coactorPattern)-[:EQUIVALENT]->(coactor)  // _COACTOR is equivalent to COACTOR
CREATE (collaboratorPattern)-[:EQUIVALENT]->(collaborator)  // _COLLABORATOR is equivalent to COLLABORATOR

// === Computed Properties ===
// Define the Kevin Bacon number property for Actors
CREATE (kbNumberProperty:Property:PatternDefinedNodeProperty {
    name: "kb_number",
    pattern: "SHORTEST 1 (x)-[ca:COACTOR]-*(y:_KevinBacon) WITH ca LIMIT 1 WITH size(ca) AS kbn",
    propertyOwnerVariable: "x",
    valueVariable: "kbn"
})  // Computes shortest COACTOR path to Kevin Bacon
CREATE (actor)-[:HAS_PROPERTY]->(kbNumberProperty)  // Attach kb_number to Actor class

// === Special Case Hierarchies ===
// Define subclass relationships for specific instances
CREATE (kevinBacon)-[:SCO]->(actor)  // Kevin Bacon is an Actor
CREATE (easterEggActor)-[:SCO]->(actor)  // Emil Eifrem is an Actor
CREATE (easterEggActor)-[:SCO]->(anomalous)  // Emil Eifrem is also Anomalous