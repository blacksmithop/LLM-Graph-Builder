from langchain_community.graphs import Neo4jGraph
from os import getenv


class Neo4J:
    def __init__(self) -> None:
        self.graph = Neo4jGraph(url=getenv("NEO4J_URL"), database=getenv("NEO4J_DATABASE"), username=getenv("NEO4J_USERNAME"), password=getenv("NEO4J_PASSWORD"), refresh_schema=False, sanitize=True)
        
    def execute_query(self, query, param=None):
        return self.graph.query(query, param)
    
    def get_current_status_document_node(self, file_name):
        """
        Get status of Document Node for a given file name
        """
        query = """
                MATCH(d:Document {fileName : $file_name}) RETURN d.status AS Status , d.processingTime AS processingTime, 
                d.nodeCount AS nodeCount, d.model as model, d.relationshipCount as relationshipCount,
                d.total_pages AS total_pages, d.total_chunks AS total_chunks , d.fileSize as fileSize, 
                d.is_cancelled as is_cancelled, d.processed_chunk as processed_chunk, d.fileSource as fileSource
                """
        param = {"file_name" : file_name}
        return self.execute_query(query, param)