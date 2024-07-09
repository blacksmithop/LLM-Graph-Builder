import logging
from os import getenv
from time import sleep
from typing import List

from langchain.chains.graph_qa.cypher import GraphCypherQAChain
from langchain.docstore.document import Document
from langchain_community.graphs import Neo4jGraph
from langchain_community.graphs.graph_document import (GraphDocument, Node,
                                                       Relationship)
from utils.common.relationship_similarity import EmbeddingSimilarity

from tqdm import tqdm

from utils.common.openi_core import embeddings, gpt3_llm, gpt4_llm
from utils.custom.chains import get_graph_chain



class Neo4J:
    def __init__(
        self,
        document_name: str = "",
        node_labels: List[str] = [],
        rel_types: List[str] = [],
    ) -> None:
        self.document_name = document_name

        self.graph = Neo4jGraph(
            url=getenv("NEO4J_URL"),
            database=getenv("NEO4J_DATABASE"),
            username=getenv("NEO4J_USERNAME"),
            password=getenv("NEO4J_PASSWORD"),
            refresh_schema=False,
            sanitize=True,
        )
        self.chain = get_graph_chain(node_labels=node_labels, rel_types=rel_types)
        self.embeddings = embeddings
        self.similarity = EmbeddingSimilarity(embeddings=self.embeddings)
        

    def get_qa_chain(self):
        return GraphCypherQAChain.from_llm(
            gpt4_llm, graph=self.graph, verbose=True, return_intermediate_steps=True
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

    def get_insight_nodes(self, documents: List[Document]) -> List[Node]:
        nodes = []

        for doc in tqdm(documents):
            node = Node(
                id=doc.metadata["insightID"],
                type="Insight",
                properties={
                    "text": doc.page_content,
                    "embedding": self.embeddings.embed_query(doc.page_content),
                },
            )
            nodes.append(node)

        logging.info(f"Created {len(nodes)} Insight Nodes")

        return nodes

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
        logging.info(f"Insights - {insight_count} Documents")

        if insight_count + 1 < len(documents):  # TODO: Allow for adding new nodes
            document_node = self.get_document_node()
            source_document = Document(page_content=self.document_name)

            logging.debug("Generating Nodes with Embeddings")
            insight_nodes: List[Node] = self.get_insight_nodes(documents=documents)
            logging.warning(f"Completed for {len(insight_nodes)} Nodes")

            insight_node_relationships = [
                Relationship(
                    source=insight_node, target=document_node, type="IS_INSIGHT_FROM"
                )
                for insight_node in insight_nodes
            ]

            graph_document = GraphDocument(
                nodes=[document_node] + insight_nodes,
                relationships=insight_node_relationships,
                source=source_document,
            )
            self.graph.add_graph_documents([graph_document])
            logging.warning(f"Finished inserting Insight Nodes into database")

            logging.debug("Generating Entity, Relationships from Insight")

            BATCH_SIZE = 10
            COUNT = 0

            for insight_node in tqdm(insight_nodes):
                if COUNT == BATCH_SIZE:
                    COUNT = 0
                    logging.info("[SLEEPING FOR 20s 💤]")
                    sleep(20)

                insight = insight_node.properties["text"]
                insight_entity_relationship = self.get_insight_entity_relationships(
                    insight=insight
                )
                BATCH_SIZE += 1

                for item in insight_entity_relationship:
                    try:
                        head, head_type, tail, tail_type, relation = (
                            item["head"],
                            item["head_type"],
                            item["tail"],
                            item["tail_type"],
                            item["relation"],
                        )

                        head_type = self.similarity.get_similar_relationship(entity=head_type)                        
                        
                        head_node = Node(
                            id=head,
                            type=head_type,
                        )
                        
                        tail_type = self.similarity.get_similar_relationship(entity=tail_type)
                        
                        tail_node = Node(
                            id=tail,
                            type=tail_type,
                        )

                        # HEAD - RELATION -> TAIL
                        head_tail_relationship = Relationship(
                            source=head_node, target=tail_node, type=relation
                        )

                        # INSIGHT - CONTAINS -> HEAD
                        insight_head_relationship = Relationship(
                            source=insight_node,
                            target=head_node,
                            type="CONTAINS_ENTITY",
                        )

                        graph_document = GraphDocument(
                            nodes=[insight_node, head_node, tail_node],
                            relationships=[
                                head_tail_relationship,
                                insight_head_relationship,
                            ],
                            source=source_document,
                        )

                        self.graph.add_graph_documents([graph_document])
                    except KeyError:
                        pass

            logging.warning(f"Added Insight, Entity Relationship to database")

            self.create_insight_index()
            logging.info("Created Index (cosine) for Insights")
        else:
            logging.error("Insights already present in database")

    def get_insight_entity_relationships(self, insight: str):

        entity_relationship = self.chain.invoke({"input": insight})

        return entity_relationship
