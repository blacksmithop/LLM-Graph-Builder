import logging

import coloredlogs
from dotenv import load_dotenv

from utils.common.constants import allowed_nodes, allowed_relations, examples, examples_v3
from utils.common.create_document import get_documents_from_df
from utils.common.file_handler import LocalFileHandler
from utils.custom.knowledge_graph import Neo4JKnowledgeGraph

load_dotenv()
coloredlogs.install(level="DEBUG")

LOG_IGNORELIST = ["httpcore", "openai", "neo4j", "httpx", "urllib3"]

for item in LOG_IGNORELIST:
    logging.getLogger(item).setLevel(logging.WARNING)


file_handler = LocalFileHandler()

FILE_NAME = "dataset.xlsx"

FILE_PATH = f"./static/{FILE_NAME}"

df = file_handler.read_local_file(FILE_PATH)

documents = get_documents_from_df(
    df=df, insight_column="Insight", id_column="InsightID"
)[:50]

neo4j = Neo4JKnowledgeGraph(
    document_name=FILE_NAME, rel_types=allowed_relations[:30], node_labels=allowed_nodes, examples=examples_v3, prompt_version=3
)

neo4j.create_knowledge_graph(documents=documents)


entity_relationship = neo4j.get_insight_entity_relationships(
    insight=documents[0].page_content
)
logging.info(entity_relationship)
