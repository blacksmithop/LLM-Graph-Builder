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
    def __init__(self) -> None:
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
    
    def insert_node(self, document: Document):
        raise NotImplementedError
    
    def insert_graph_documents(self, documents: List[Document], allowed_nodes: List[str] = [], allowed_relationships: List[str] = []):
        is_exist = self.check_if_nodes_exist()
        logging.debug(f"Insights already uploaded: {is_exist}")
        
        if not is_exist:
        # Insert Insight Documents
            self.insert_documents(documents=documents)
            logging.info("Finished Inserting Insight Documents")
            
            llm_transformer_filtered = LLMGraphTransformer(
                llm=gpt3_llm,
                allowed_nodes=allowed_nodes,
                allowed_relationships=allowed_relationships,
                strict_mode=False
            )
            graph_documents = llm_transformer_filtered.convert_to_graph_documents(documents)
            self.graph.add_graph_documents(graph_documents)
            logging.info("Finished Inserting Graph Documents")

    def get_document_node(self, document_name: str):
        document_node = Node(id=0, type="Document", properties={
            "name": document_name
        })
        return document_node
    

    
    def insert_documents(self, documents: List[Document]):
        is_exist = self.check_if_nodes_exist()
        logging.error(f"Insights already uploaded: {is_exist}")
        
        if not is_exist:
            logging.warning(f"Inserting documents...")
            Neo4jVector.create_new_index
            Neo4jVector.from_documents(
                documents,
                embeddings,
                url=getenv("NEO4J_URL"),
                username=getenv("NEO4J_USERNAME"),
                password=getenv("NEO4J_PASSWORD"),
                search_type="hybrid",
                node_label="Insight",
                database=getenv("NEO4J_DATABASE")
            )
            
            self.set_node_label(new_label="Insight")
            self.create_insight_index()
            return logging.info(f"Finished inserting embedding data for {len(documents)} Nodes")
    
    def check_if_nodes_exist(self):
        response = self.execute_query("MATCH (n:Chunk) RETURN COUNT(n) as count")
        count = response[0]["count"]
        return count > 0

    def get_insight_nodes(self, count: int = None):
        if count:
            response = self.execute_query(f"MATCH (n:Insight) RETURN ID(n) as nodeID, n.text as Insight, n.insightID as InsightID LIMIT {count}")
        else:
            response = self.execute_query("MATCH (n:Insight) RETURN ID(n) as nodeID, n.text as Insight, n.insightID as InsightID")
        nodes = [
            Node(id=int(item["nodeID"]), type="Insight",
                 properties={
                     "insightID": item["InsightID"],
                     "text": item["Insight"]
                 } 
                 ) for item in response
        ]
        
        logging.info(f"Fetched {len(nodes)} Insight Nodes")
        logging.info(nodes[0])

    def create_insight_index(self):
        response = self.execute_query("""
        CREATE VECTOR INDEX `insight_vector` if not exists for (c:Insight) on (c.embedding)
        OPTIONS {indexConfig: {
        `vector.dimensions`: 1536,
        `vector.similarity_function`: 'cosine'}}""")
        
        logging.info("Created Index for Insights")
        logging.debug(response)
        
    def set_node_label(self, new_label: str):
        response = self.execute_query(f"""MATCH (n:Chunk)
        SET n:{new_label}
        REMOVE n:Chunk""")
        
        logging.info(f"Changed label to {new_label}")
        logging.debug(response)