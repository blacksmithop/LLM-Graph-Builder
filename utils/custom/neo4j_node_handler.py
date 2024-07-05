from os import getenv
from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from langchain.docstore.document import Document
from typing import List
from utils.common.openi_core import embeddings
from utils.custom.models import InsightNode
import logging


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
    
    def insert_documents(self, documents: List[Document]):
        is_exist = self.check_if_nodes_exist()
        logging.info(f"Documents already uploaded: {is_exist}")
        
        if not is_exist:
            logging.info(f"Inserting documents...")
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
            return logging.info(f"Finished inserting embedding data for {len(documents)} Nodes")
    
    def check_if_nodes_exist(self):
        response = self.execute_query("MATCH (n:Chunk) RETURN COUNT(n) as count")
        count = response[0]["count"]
        return count > 0

    def get_insight_nodes(self, count: int = 10):
        response = self.execute_query(f"MATCH (n:Chunk) RETURN n.text as Insight, n.insightID as InsightID LIMIT {count}")
        
        nodes = [
            InsightNode(text=item["Insight"], insightID=item["InsightID"]) for item in response
        ]
        
        logging.info(f"Fetched {len(nodes)} Insight Nodes")
        logging.info(nodes[0])

 