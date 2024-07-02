from utils.models import SourceNode
from langchain.docstore.document import Document
from typing import List
from utils.neo4j_handler import graph


class NodeCreator:
    
    def __init__(self) -> None:
        self.source_node = SourceNode()
        
    def set_source_node_properties(self, file_name: str, status: str, pages: List[Document], chunks: List[Document], model: str):
        self.source_node.file_name = file_name
        self.source_node.status = status
        self.source_node.total_chunks = len(chunks)
        self.source_node.total_pages = len(pages)
        self.source_node.model = model