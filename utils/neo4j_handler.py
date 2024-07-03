from langchain_community.graphs import Neo4jGraph
from typing import List
from os import getenv
import logging
from concurrent.futures import ThreadPoolExecutor
from utils.openi_core import gpt3_llm
from utils.llm_graph_creator import LLMGraphTransformerWithLogging
from concurrent.futures import as_completed
from langchain.docstore.document import Document
import logging


CHUNKS_TO_COMBINE = 1 # TODO: Refactor to support 0 / remove argument


class Neo4J:
    def __init__(self) -> None:
        logging.error(getenv("NEO4J_URL"))
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
        param = {"file_name": file_name}
        return self.execute_query(query, param)

    def generate_graph_documents(
        self, chunkId_chunkDoc_list: List, allowed_nodes=None, allowed_relationship=None
    ):
        logging.info("Creating GRAPH documents")

        if allowed_nodes is None or allowed_nodes == "":
            allowed_nodes = []
        else:
            allowed_nodes = allowed_nodes.split(",")
        if allowed_relationship is None or allowed_relationship == "":
            allowed_relationship = []
        else:
            allowed_relationship = allowed_relationship.split(",")

        logging.debug(
            f"Allowed Nodes: {allowed_nodes}, Allowed Relationship: {allowed_relationship}"
        )

        graph_documents = self.get_graph_from_openai(
            chunkId_chunkDoc_list, allowed_nodes, allowed_relationship
        )

        logging.info(f"graph_documents = {len(graph_documents)}")
        return graph_documents

    def get_graph_from_openai(
        self, chunkId_chunkDoc_list, allowed_nodes, allowed_relationship
    ):
        futures = []
        graph_document_list = []

        combined_chunk_document_list = self.get_combined_chunks(chunkId_chunkDoc_list)

        llm_transformer = LLMGraphTransformerWithLogging(
            llm=gpt3_llm,
            node_properties=["description"],
            allowed_nodes=allowed_nodes,
            allowed_relationships=allowed_relationship,
        )

        with ThreadPoolExecutor(max_workers=10) as executor:
            for chunk in combined_chunk_document_list:
                futures.append(
                    executor.submit(llm_transformer.convert_to_graph_documents, [chunk])
                )

            for __file__, future in enumerate(as_completed(futures)):
                graph_document = future.result()
                graph_document_list.append(graph_document[0])
        return graph_document_list

    def get_combined_chunks(self, chunkId_chunkDoc_list):
        logging.info(
            "Getting Page Content"
        )
        combined_chunk_document_list = []
        
        logging.error(chunkId_chunkDoc_list[0]["chunk_doc"].metadata.keys())
        
        # combined_chunks_page_content = [
        #     "".join(
        #         document["chunk_doc"].page_content
        #         for document in chunkId_chunkDoc_list[i : i + CHUNKS_TO_COMBINE]
        #     )
        #     for i in range(0, len(chunkId_chunkDoc_list), CHUNKS_TO_COMBINE)
        # ]
        

        for document in chunkId_chunkDoc_list:
            combined_chunk_document_list.append(
                Document(
                    page_content=document["chunk_doc"].page_content,
                    metadata={"combined_chunk_ids": document["chunk_id"]},
                )
            )
        return combined_chunk_document_list

    def merge_relationship_between_chunk_and_entites(self, graph_documents_chunk_chunk_Id: List):
        batch_data = []
        logging.info("Create HAS_ENTITY relationship between chunks and entities")
        chunk_node_id_set = 'id:"{}"'
        
        for graph_doc_chunk_id in graph_documents_chunk_chunk_Id:
            for node in graph_doc_chunk_id['graph_doc'].nodes:
                query_data={
                    'chunk_id': graph_doc_chunk_id['chunk_id'],
                    'node_type': node.type,
                    'node_id': node.id
                }
                batch_data.append(query_data)
            
        if batch_data:
            unwind_query = """
                        UNWIND $batch_data AS data
                        MATCH (c:Chunk {id: data.chunk_id})
                        CALL apoc.merge.node([data.node_type], {id: data.node_id}) YIELD node AS n
                        MERGE (c)-[:HAS_ENTITY]->(n)
                    """
            self.graph.query(unwind_query, params={"batch_data": batch_data})
