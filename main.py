from utils.file_handler import LocalFileHandler
from utils.create_document import get_documents_from_df
from utils.node_creator import NodeCreator
import coloredlogs, logging
from dotenv import load_dotenv

load_dotenv()
coloredlogs.install(level='DEBUG')


file_handler = LocalFileHandler()

FILE_PATH = "./static/XflyAIToolkitInsights.csv"
FILE_NAME = "XflyAIToolkitInsights.csv"

df = file_handler.read_local_file(FILE_PATH)

documents = get_documents_from_df(df=df)

node = NodeCreator()

node.set_node_properties(file_name=FILE_NAME, pages=documents, chunks=documents, model="gpt 3.5", status="Processing")