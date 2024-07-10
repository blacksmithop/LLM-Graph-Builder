# Knowledge Graph Builder

## Graph Creation
```mermaid
flowchart TD
    A[File Upload] --> B{Identify File Type}
    B --> C[Create Documents]
    C --> D[Extract Entity from Document]
    D --> E[Get Entity Relationships]
    E --> F[Create Vector Index]
```

The Builder supports two modes of operation when creating the nodes. This can be toggled by setting `use_v2_chain` in [Neo4JKnowledgeGraph](/utils/custom/knowledge_graph.py#L40). When set to `False` less number of nodes will be created. It defaults to `True`. This might be useful in some cases. 


## Question Answering
```mermaid
graph TD
  A[Query] --> B{Construct Cypher from Schema}
  B --> C[Retrieve related Nodes]
  C --> D{Can Answer Question}
  D -->|Yes| E[Response]
  D -->|No| F[Process result]
  F --> E
```