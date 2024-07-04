import logging

import coloredlogs
from dotenv import load_dotenv

from utils.create_document import get_documents_from_df
from utils.file_handler import LocalFileHandler
from utils.node_creator import NodeCreator
from utils.constants import allowed_relations, allowed_nodes

load_dotenv()
coloredlogs.install(level="DEBUG")

LOG_IGNORELIST = [
    "httpcore",
    "openai",
    "neo4j",
]

for item in LOG_IGNORELIST:
    logging.getLogger(item).setLevel(logging.WARNING)


file_handler = LocalFileHandler()

FILE_NAME = "Ipsen_Insight_Cluster.xlsx"

FILE_PATH = f"./static/{FILE_NAME}"

df = file_handler.read_local_file(FILE_PATH)

documents = get_documents_from_df(df=df, insight_column="Insight", id_column="InsightID")[:50]


node = NodeCreator()

node.allowed_nodes = allowed_nodes
node.allowed_relationships = [] #allowed_relations[:10]

logging.info(f"Passing {len(node.allowed_nodes)} nodes and {len(node.allowed_relationships)} relationships as Examples")
logging.debug(f"Relationships: {node.allowed_relationships}")

node.create_neo4j_graph(
    file_name=FILE_NAME,
    pages=documents,
    chunks=documents,
    model="gpt 3.5",
    status="Processing",
)
