import logging

import coloredlogs
from dotenv import load_dotenv

from utils.common.create_document import get_documents_from_df
from utils.common.file_handler import LocalFileHandler
from utils.common.constants import allowed_relations, allowed_nodes
from utils.custom.neo4j_node_handler import Neo4J


load_dotenv()
coloredlogs.install(level="DEBUG")

LOG_IGNORELIST = [
    "httpcore",
    "openai",
    "neo4j",
]

for item in LOG_IGNORELIST:
    logging.getLogger(item).setLevel(logging.WARNING)

neo4j = Neo4J()

# file_handler = LocalFileHandler()

# FILE_NAME = "Ipsen_Insight_Cluster.xlsx"

# FILE_PATH = f"./static/{FILE_NAME}"

# df = file_handler.read_local_file(FILE_PATH)

# documents = get_documents_from_df(df=df, insight_column="Insight", id_column="InsightID")

# neo4j.insert_documents(documents=documents)

neo4j.get_insight_nodes()

