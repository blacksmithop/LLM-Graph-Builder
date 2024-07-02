from utils.models import SourceNode
from langchain.docstore.document import Document
from typing import List
from utils.neo4j_handler import Neo4J
from utils.openi_core import embeddings
import logging
from hashlib import sha1


class NodeCreator:

    def __init__(self) -> None:
        self.source_node = SourceNode()
        self.neo4j = Neo4J()
        self.embeddings = embeddings
        self.EMBEDDING_DIM = 1536

    def set_source_node_properties(
        self,
        file_name: str,
        status: str,
        pages: List[Document],
        chunks: List[Document],
        model: str,
    ):
        self.source_node.file_name = file_name
        self.source_node.status = status
        self.source_node.total_chunks = len(chunks)
        self.source_node.total_pages = len(pages)
        self.source_node.model = model

    def process_chunks(self, file_name: str, chunks: List[Document]):
        chunkId_chunkDoc_list = self.create_relation_between_chunks(file_name, chunks)
        self.update_embedding_create_vector_index(chunkId_chunkDoc_list, file_name)
        
    def create_relation_between_chunks(self, file_name, chunks: List[Document]) -> List:
        logging.debug(f"Creating CHUNK relations")

        current_chunk_id = ""
        lst_chunks_including_hash = []
        batch_data = []
        relationships = []
        offset = 0

        for i, chunk in enumerate(chunks):
            page_content_sha1 = sha1(chunk.page_content.encode())
            insightID = chunk.metadata["insightID"]
            previous_chunk_id = current_chunk_id
            current_chunk_id = page_content_sha1.hexdigest()
            position = i + 1
            if i > 0:
                # offset += len(tiktoken.encoding_for_model("gpt2").encode(chunk.page_content))
                offset += len(chunks[i - 1].page_content)
            if i == 0:
                firstChunk = True
            else:
                firstChunk = False
            metadata = {
                "position": position,
                "length": len(chunk.page_content),
                "content_offset": offset,
            }
            chunk_document = Document(
                page_content=chunk.page_content, metadata=metadata
            )

            chunk_data = {
                "insightID": insightID,
                "id": current_chunk_id,
                "pg_content": chunk_document.page_content,
                "position": position,
                "length": chunk_document.metadata["length"],
                "f_name": file_name,
                "previous_id": previous_chunk_id,
                "content_offset": offset,
            }

            if "page_number" in chunk.metadata:
                chunk_data["page_number"] = chunk.metadata["page_number"]

            if "start_time" in chunk.metadata and "end_time" in chunk.metadata:
                chunk_data["start_time"] = chunk.metadata["start_time"]
                chunk_data["end_time"] = chunk.metadata["end_time"]

            batch_data.append(chunk_data)

            lst_chunks_including_hash.append(
                {"chunk_id": current_chunk_id, "chunk_doc": chunk}
            )

            # create relationships between chunks
            if firstChunk:
                relationships.append(
                    {"type": "FIRST_CHUNK", "chunk_id": current_chunk_id}
                )
            else:
                relationships.append(
                    {
                        "type": "NEXT_CHUNK",
                        "previous_chunk_id": previous_chunk_id,  # ID of previous chunk
                        "current_chunk_id": current_chunk_id,
                    }
                )

    def update_embedding_create_vector_index(self, chunkId_chunkDoc_list, file_name):
        # create embedding
        logging.debug("Updating Embeddings and creating Vector Index")
        
        embeddings, dimension = self.embeddings, self.EMBEDDING_DIM
        logging.info(f"embedding model:{embeddings} and dimesion:{dimension}")
        data_for_query = []
        logging.info(f"update embedding and vector index for chunks")
        for row in chunkId_chunkDoc_list:
            # for graph_document in row['graph_doc']:
            embeddings_arr = embeddings.embed_query(row["chunk_doc"].page_content)
            # logging.info(f'Embedding list {embeddings_arr}')

            data_for_query.append(
                {"chunkId": row["chunk_id"], "embeddings": embeddings_arr}
            )

            self.neo4j.graph.query(
                """CREATE VECTOR INDEX `vector` if not exists for (c:Chunk) on (c.embedding)
                            OPTIONS {indexConfig: {
                            `vector.dimensions`: $dimensions,
                            `vector.similarity_function`: 'cosine'
                            }}
                        """,
                {"dimensions": dimension},
            )

        query_to_create_embedding = """
            UNWIND $data AS row
            MATCH (d:Document {fileName: $fileName})
            MERGE (c:Chunk {id: row.chunkId})
            SET c.embedding = row.embeddings
            MERGE (c)-[:PART_OF]->(d)
        """
        self.neo4j.graph.query(
            query_to_create_embedding,
            params={"fileName": file_name, "data": data_for_query},
        )
