# Knowledge Graph Builder

![Python](https://skillicons.dev/icons?i=python,docker)

## Graph Creation
```mermaid
flowchart TD
    A[File Upload] --> B[Identify File Type]
    B --> C[Create Documents]
    C --> D[Extract Entity from Document]
    D --> E[Get Entity Relationships]
    E --> F[Create Vector Index]
```

### Installation


First, install the dependenices
```bash
pip install -r requirements.txt
```

### Configure Neo4J (Dozerdb)

Next, install Neo4j. I recommend doing this [Dozerb](https://dozerdb.org/) as it offers enterprise features in the community edition. You can use this [script](./install_dozerdb.sh) to get a docker container running.

### Configure LLM, Embeddings

You can use Azure OpenAI, Ollama or your custom provider. You just need to define your LLM and Embeddings model in [llm_core.py](./utils/common/llm_core.py)

### Usage

Once complete you can set your `FILE_PATH` in [knowledge_graph_creator.py](./knowledge_graph_creator.py) and run the python script. It should you populate you Neo4J database.


The Builder supports different modes of operation when creating the nodes. This can be toggled by changing `prompt_version` in [Neo4JKnowledgeGraph](/utils/custom/knowledge_graph.py#L40). Defaults to `2`.



## Question Answering

```mermaid
graph TD
  A[Query] --> B[Construct Cypher from Schema]
  B --> C[Retrieve related Nodes]
  C --> D{Can Answer Question}
  D -->|Yes| E[Response]
  D -->|No| F[Process result]
  F --> E
```

You can perform QA on your knowledge graph using the streamlit application at [graph_qa_chatbot.py](./graph_qa_chatbot.py)

```bash
streamlit run graph_qa_chatbot.py
```

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=blacksmithop/LLM-Graph-Builder&type=Date)](https://star-history.com/#blacksmithop/LLM-Graph-Builder&Date)
