from os import getenv
from langchain_community.graphs import Neo4jGraph
from langchain.docstore.document import Document
from typing import List
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
    
    def insert_nodes(self, documents: List[Document]):
        pass


 