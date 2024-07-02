from utils.file_handler import LocalFileHandler
from utils.create_document import get_documents_from_df
import coloredlogs, logging
from dotenv import load_dotenv

load_dotenv()
coloredlogs.install(level='DEBUG')


file_handler = LocalFileHandler()

df = file_handler.read_local_file("./static/XflyAIToolkitInsights.csv")

documents = get_documents_from_df(df=df)

# logging.debug(documents[0])