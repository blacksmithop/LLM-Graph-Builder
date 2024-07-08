from os import getenv
from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from langchain.docstore.document import Document
from typing import List
from utils.common.openi_core import embeddings
import logging
from langchain_experimental.graph_transformers import LLMGraphTransformer
from utils.common.openi_core import gpt3_llm
from langchain_community.graphs.graph_document import Node, Relationship, GraphDocument


class Neo4J:
    def __init__(self, document_name: str) -> None:
        self.document_name = document_name

        self.graph = Neo4jGraph(
            url=getenv("NEO4J_URL"),
            database=getenv("NEO4J_DATABASE"),
            username=getenv("NEO4J_USERNAME"),
            password=getenv("NEO4J_PASSWORD"),
            refresh_schema=False,
            sanitize=True,
        )

    def execute_query(self, query, param=None):
        return self.graph.query(query, param)

           

    def get_insight_count(self):
        response = self.execute_query("MATCH (n:Insight) RETURN COUNT(n) as count")
        count = response[0]["count"]
        return count

    def get_document_node(self):
        document_node = Node(
            id=0, type="Document", properties={"name": self.document_name}
        )

        return document_node

    def get_insight_nodes(self, documents: List[Document]):
        nodes = [
            Node(id=doc.metadata["insightID"], type="Insight", properties={"insightID": doc.metadata["insightID"], "text": doc.page_content})
            for doc in documents
        ]

        logging.info(f"Created {len(nodes)} Insight Nodes (no embeddings)")
        logging.info(nodes[0])

        return nodes

    def update_insight_text_embeddings(self, documents: List[Document]):
        
        data_for_query = [
            {
                "id": doc.metadata["insightID"],
                "text": doc.page_content,
                "embedding": embeddings.embed_query(doc.page_content)
            }
            for doc in documents
        ]
 
        QUERY = """
        UNWIND $data AS row
        MERGE (c:Insight {id: row.id})
        SET c.embedding = row.embedding, c.text = row.text
        """       
        
        self.graph.query(QUERY, params={"data":data_for_query})
        

    def create_insight_index(self):
        response = self.execute_query(
            """
        CREATE VECTOR INDEX `insight_vector` if not exists for (c:Insight) on (c.embedding)
        OPTIONS {indexConfig: {
        `vector.dimensions`: 1536,
        `vector.similarity_function`: 'cosine'}}"""
        )

    def set_node_label(self, new_label: str):
        response = self.execute_query(
        f"""MATCH (n:Chunk)
        SET n:{new_label}
        REMOVE n:Chunk"""
        )

        logging.info(f"Changed label to {new_label}")
        logging.debug(response)

    def create_knowledge_graph(self, documents: List[Document]):
        insight_count = self.get_insight_count()
        
        if insight_count == documents: # TODO: Allow for adding new nodes
            logging.info(f"Insights ({insight_count}) already present in database")
            
            document_node = self.get_document_node()
            document = Document(page_content=self.document_name)
            logging.warning("Loaded Document Node")

            insight_nodes = self.get_insight_nodes(documents=documents)
            logging.warning(f"Loaded {len(insight_nodes)} Insight Nodes")

            node_relationships = [
                Relationship(
                    source=insight_node, target=document_node, type="IS_INSIGHT_FROM"
                )
                for insight_node in insight_nodes
            ]

            logging.warning(f"Defined Insight, Document Relationship")

            graph_document = GraphDocument(
                nodes=[document_node]+insight_nodes, relationships=node_relationships, source=document
            )
            

            self.graph.add_graph_documents([graph_document])
            logging.warning(f"Added Insight, Document Relationship")

            self.update_insight_text_embeddings(documents=documents)
            logging.info(f"Added Embeddings, Text field for {len(documents)} Insights")

            self.create_insight_index()
            logging.info("Created Index for Insights")