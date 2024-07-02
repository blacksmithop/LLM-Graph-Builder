from langchain_community.graphs import Neo4jGraph
from os import getenv


class Neo4J:
    def __init__(self) -> None:
        self.graph = Neo4jGraph(url=getenv("NEO4J_URL"), database=getenv("NEO4J_DATABASE"), username=getenv("NEO4J_USERNAME"), password=getenv("NEO4J_PASSWORD"), refresh_schema=False, sanitize=True)
        
        