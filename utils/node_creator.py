from utils.models import SourceNode
from langchain.docstore.document import Document
from typing import List
from utils.neo4j_handler import Neo4J
from utils.openi_core import embeddings
import logging
from hashlib import sha1
from datetime import datetime
from pathlib import Path


UPDATE_GRAPH_CHUNKS_PROCESSED = 20


class NodeCreator:

    def __init__(self) -> None:
        self.source_node = SourceNode()
        self.neo4j = Neo4J()
        self.embeddings = embeddings
        self.EMBEDDING_DIM = 1536

    def set_node_properties(
        self,
        file_name: str,
        status: str,
        pages: List[Document],
        chunks: List[Document],
        model: str,
    ):

        start_time = datetime.now()

        self.source_node.file_name = file_name
        self.source_node.status = status
        self.source_node.total_chunks = len(chunks)
        self.source_node.total_pages = len(pages)
        self.source_node.model = model
        self.update_source_node(self.source_node, file_name)

        for i in range(0, len(chunks), UPDATE_GRAPH_CHUNKS_PROCESSED):
            select_chunks_upto = i + UPDATE_GRAPH_CHUNKS_PROCESSED
            logging.info(f"Selected Chunks upto: {select_chunks_upto}")
            if len(chunks) <= select_chunks_upto:
                select_chunks_upto = len(chunks)
            selected_chunks = chunks[i:select_chunks_upto]

            result = self.neo4j.get_current_status_document_node(file_name)
            is_cancelled_status = result[0]["is_cancelled"]
            logging.info(f"Is Cancelled : {result[0]['is_cancelled']}")

            node_count, rel_count = self.process_chunks(file_name, selected_chunks)
            end_time = datetime.now()
            processed_time = end_time - start_time

            obj_source_node = SourceNode()
            obj_source_node.file_name = file_name
            obj_source_node.updated_at = end_time
            obj_source_node.processing_time = processed_time
            obj_source_node.node_count = node_count
            obj_source_node.processed_chunk = select_chunks_upto
            obj_source_node.relationship_count = rel_count
            self.update_source_node(obj_source_node, file_name)

        result = self.neo4j.get_current_status_document_node(file_name)
        is_cancelled_status = result[0]["is_cancelled"]
        if bool(is_cancelled_status) == True:
            logging.info(f"Is_cancelled True at the end extraction")
            job_status = "Cancelled"
        logging.info(f"Job Status at the end : {job_status}")
        end_time = datetime.now()
        processed_time = end_time - start_time
        obj_source_node = SourceNode()
        obj_source_node.file_name = file_name
        obj_source_node.status = job_status
        obj_source_node.processing_time = processed_time

        self.update_source_node(obj_source_node, file_name)
        logging.info("Updated the nodeCount and relCount properties in Docuemnt node")
        logging.info(f"file:{file_name} extraction has been completed")

        # self.delete_uploaded_local_file(merged_file_path, file_name)

        return {
            "fileName": file_name,
            "nodeCount": node_count,
            "relationshipCount": rel_count,
            "processingTime": round(processed_time.total_seconds(), 2),
            "status": job_status,
            "model": model,
            "success_count": 1,
        }

    def delete_uploaded_local_file(merged_file_path, file_name):
        file_path = Path(merged_file_path)
        if file_path.exists():
            file_path.unlink()
            logging.info(f"file {file_name} deleted successfully")

    def process_chunks(self, file_name: str, chunks: List[Document]):
        chunkId_chunkDoc_list = self.create_relation_between_chunks(file_name, chunks)

        logging.error(f"{len(chunkId_chunkDoc_list)=}")
        self.update_embedding_create_vector_index(chunkId_chunkDoc_list, file_name)

        graph_documents = self.neo4j.generate_graph_documents(chunkId_chunkDoc_list)

        self.save_graph_documents(graph_documents)

        chunks_and_graphDocuments_list = self.get_chunk_graph_documents(graph_documents)

        self.neo4j.merge_relationship_between_chunk_and_entites(
            chunks_and_graphDocuments_list
        )

        distinct_nodes = set()
        relations = []
        for graph_document in graph_documents:
            # get distinct nodes
            for node in graph_document.nodes:
                node_id = node.id
                node_type = node.type
                if (node_id, node_type) not in distinct_nodes:
                    distinct_nodes.add((node_id, node_type))
        # get all relations
        for relation in graph_document.relationships:
            relations.append(relation.type)

        node_count = len(distinct_nodes)
        rel_count = len(relations)
        print(f"node count internal func:{node_count}")
        print(f"relation count internal func:{rel_count}")
        return node_count, rel_count

    def create_relation_between_chunks(self, file_name, chunks: List[Document]) -> List:
        logging.debug(f"Creating CHUNK relations | {len(chunks)=}")

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
                
        query_to_create_chunk_and_PART_OF_relation = """
        UNWIND $batch_data AS data
        MERGE (c:Chunk {id: data.id})
        SET c.text = data.pg_content, c.position = data.position, c.length = data.length, c.fileName=data.f_name, c.content_offset=data.content_offset
        WITH data, c
        SET c.page_number = CASE WHEN data.page_number IS NOT NULL THEN data.page_number END,
            c.start_time = CASE WHEN data.start_time IS NOT NULL THEN data.start_time END,
            c.end_time = CASE WHEN data.end_time IS NOT NULL THEN data.end_time END
        WITH data, c
        MATCH (d:Document {fileName: data.f_name})
        MERGE (c)-[:PART_OF]->(d)
        """
        self.neo4j.graph.query(
            query_to_create_chunk_and_PART_OF_relation,
            params={"batch_data": batch_data},
        )

        query_to_create_FIRST_relation = """ 
            UNWIND $relationships AS relationship
            MATCH (d:Document {fileName: $f_name})
            MATCH (c:Chunk {id: relationship.chunk_id})
            FOREACH(r IN CASE WHEN relationship.type = 'FIRST_CHUNK' THEN [1] ELSE [] END |
                    MERGE (d)-[:FIRST_CHUNK]->(c))
            """
        self.neo4j.graph.query(
            query_to_create_FIRST_relation,
            params={"f_name": file_name, "relationships": relationships},
        )

        query_to_create_NEXT_CHUNK_relation = """ 
            UNWIND $relationships AS relationship
            MATCH (c:Chunk {id: relationship.current_chunk_id})
            WITH c, relationship
            MATCH (pc:Chunk {id: relationship.previous_chunk_id})
            FOREACH(r IN CASE WHEN relationship.type = 'NEXT_CHUNK' THEN [1] ELSE [] END |
                    MERGE (c)<-[:NEXT_CHUNK]-(pc))
            """
        self.neo4j.graph.query(
            query_to_create_NEXT_CHUNK_relation, params={"relationships": relationships}
        )

        return lst_chunks_including_hash

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

    def save_graph_documents(self, graph_document_list):
        return self.neo4j.graph.add_graph_documents(graph_document_list)

    def get_chunk_graph_documents(self, graph_document_list):
        logging.info("Creating list of CHUNKS and GRAPH documents")
        lst_chunk_chunkId_document = []
        for graph_document in graph_document_list:
            for chunk_id in graph_document.source.metadata["combined_chunk_ids"]:
                lst_chunk_chunkId_document.append(
                    {"graph_doc": graph_document, "chunk_id": chunk_id}
                )

        return lst_chunk_chunkId_document

    def update_source_node(self, obj_source_node: SourceNode, file_name: str):
        try:
            params = {}
            if (
                obj_source_node.file_name is not None
                and obj_source_node.file_name != ""
            ):
                params["fileName"] = obj_source_node.file_name

            if obj_source_node.status is not None and obj_source_node.status != "":
                params["status"] = obj_source_node.status

            if obj_source_node.created_at is not None:
                params["createdAt"] = obj_source_node.created_at

            if obj_source_node.updated_at is not None:
                params["updatedAt"] = obj_source_node.updated_at

            if (
                obj_source_node.processing_time is not None
                and obj_source_node.processing_time != 0
            ):
                params["processingTime"] = round(
                    obj_source_node.processing_time.total_seconds(), 2
                )

            if (
                obj_source_node.node_count is not None
                and obj_source_node.node_count != 0
            ):
                params["nodeCount"] = obj_source_node.node_count

            if (
                obj_source_node.relationship_count is not None
                and obj_source_node.relationship_count != 0
            ):
                params["relationshipCount"] = obj_source_node.relationship_count

            if obj_source_node.model is not None and obj_source_node.model != "":
                params["model"] = obj_source_node.model

            if (
                obj_source_node.total_pages is not None
                and obj_source_node.total_pages != 0
            ):
                params["total_pages"] = obj_source_node.total_pages

            if (
                obj_source_node.total_chunks is not None
                and obj_source_node.total_chunks != 0
            ):
                params["total_chunks"] = obj_source_node.total_chunks

            if (
                obj_source_node.is_cancelled is not None
                and obj_source_node.is_cancelled != False
            ):
                params["is_cancelled"] = obj_source_node.is_cancelled

            if (
                obj_source_node.processed_chunk is not None
                and obj_source_node.processed_chunk != 0
            ):
                params["processed_chunk"] = obj_source_node.processed_chunk

            param = {"props": params}

            print(f"Base Param value 1 : {param}")
            query = "MERGE(d:Document {fileName :$props.fileName}) SET d += $props"
            logging.info("Update source node properties")
            self.neo4j.graph.query(query, param)
        except Exception as e:
            error_message = str(e)
            self.update_exception_db(file_name, error_message)
            raise Exception(error_message)

    def update_exception_db(self, file_name, exp_msg):
        try:
            job_status = "Failed"
            result = self.neo4j.get_current_status_document_node(file_name)
            is_cancelled_status = result[0]["is_cancelled"]
            if bool(is_cancelled_status) == True:
                job_status = "Cancelled"
            self.neo4j.graph.query(
                """MERGE(d:Document {fileName :$fName}) SET d.status = $status, d.errorMessage = $error_msg""",
                {"fName": file_name, "status": job_status, "error_msg": exp_msg},
            )
        except Exception as e:
            error_message = str(e)
            logging.error(
                f"Error in updating document node status as failed: {error_message}"
            )
            raise Exception(error_message)
