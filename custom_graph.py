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
    "httpx"
]

for item in LOG_IGNORELIST:
    logging.getLogger(item).setLevel(logging.WARNING)

neo4j = Neo4J()

file_handler = LocalFileHandler()

FILE_NAME = "Ipsen_Insight_Cluster.xlsx"

FILE_PATH = f"./static/{FILE_NAME}"

df = file_handler.read_local_file(FILE_PATH)

documents = get_documents_from_df(df=df, insight_column="Insight", id_column="InsightID")[:50]

neo4j.insert_documents(documents=documents)
neo4j.insert_graph_documents(documents=documents, allowed_relationships=['Concerns exist regarding the safety, tolerability, and side effect management of Belzutifan.', 'Conferences and scientific meetings discuss the latest advancements in RCC research.', 'Considerations for adjuvant treatment options and their potential benefits.', 'Considerations for sequencing after first-line IO therapy.', 'Desire for education and guidance on engaging with patient groups and advocates in research.', 'Discussions around sequencing and positioning of Cabo+Nivo combination therapy.', 'Discussions around the efficacy and toxicity management of IO-IO and IO-TKI combinations in first-line treatment of RCC.', 'Dose intensity of pembrolizumab in combination therapy.', 'Doubts about the efficacy of triplet therapy in certain patient subgroups.', 'Effective management of patient compliance and adverse events is challenging.', 'Emotional well-being and trust impact treatment adherence and outcomes.', 'Emphasis on managing toxicities associated with IO therapies.'])

neo4j.get_insight_nodes(count=5)

# neo4j.create_insight_index()