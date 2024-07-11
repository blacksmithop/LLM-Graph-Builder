from os import getenv

from dotenv import load_dotenv
from langchain.embeddings import CacheBackedEmbeddings
from langchain.storage import LocalFileStore
from langchain_openai import (AzureChatOpenAI, AzureOpenAI,
                              AzureOpenAIEmbeddings)

load_dotenv()

# OpenAI Embeddings
underlying_embeddings = AzureOpenAIEmbeddings(
    azure_deployment=getenv("EMBEDDINGS_NAME"),
)

store = LocalFileStore("./cache/")

embeddings = CacheBackedEmbeddings.from_bytes_store(
    underlying_embeddings,
    store,
    namespace=underlying_embeddings.model,
    query_embedding_cache=True,
)

# OpenAI Completion
llm = AzureOpenAI(deployment_name=getenv("DEPLOYMENT_NAME"), temperature=0)
llm.max_tokens = 2000

llm = AzureChatOpenAI(
    deployment_name=getenv("LLM_DEPLOYMENT_NAME"),
    temperature=0,
    max_tokens=4000,
)

if __name__ == "__main__":
    print(embeddings.embed_query("Hi")[:5])
    print(llm.invoke("Tell me a joke").content)
