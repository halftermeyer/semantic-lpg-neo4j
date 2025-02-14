CREATE (:MatchDefinedLabel:Label {name: "_PersonActedInSome", pattern: "(p:Person) WHERE EXISTS {(p)-[:ACTED_IN]->()}", classElementVariable: "p"})<-[:EQUIVALENT]-(:Label {name: "Actor"})-[:SCO]->(n1:Label {name: "Person"})<-[:SOURCE]-(n2:Relationship {name: "ACTED_IN"})-[:IMPLIES]->(n10:Relationship {name: "INVOLVED_IN"})-[:TARGET]->(n3:Label {name: "Movie"})<-[:TARGET]-(n13:Relationship {name: "DIRECTED"}),
(n2)-[:TARGET]->(n3),
(n12:Relationship:Symmetric {name: "COLLABORATOR"})<-[:SCO]-(n7:Relationship:Symmetric {name: "COACTOR"})-[:TARGET]->(n1)<-[:SOURCE]-(n7)-[:EQUIVALENT]->(:MatchDefinedRelationship:Relationship:Symmetric {name: "_COACTOR", pattern: "(s:Person)-[:ACTED_IN]->()<-[:ACTED_IN]-(t:Person)", sourceElementVariable: "s", targetElementVariable: "t"}),
(n10)-[:SOURCE]->(n1)<-[:SCO]-(:Label {name: "Director"})-[:EQUIVALENT]->(:MatchDefinedLabel:Label {name: "_PersonDirectedSome", pattern: "(p:Person) WHERE EXISTS {(p)-[:DIRECTED]->()}", classElementVariable: "p"}),
(n12)-[:SOURCE]->(n1)<-[:TARGET]-(n12)-[:EQUIVALENT]->(:MatchDefinedRelationship:Relationship:Symmetric {name: "_COLLABORATOR", pattern: "(s:Person)-[:INVOLVED_IN]->()<-[:INVOLVED_IN]-(t:Person)", sourceElementVariable: "s", targetElementVariable: "t"}),
(n13)-[:SOURCE]->(n1)