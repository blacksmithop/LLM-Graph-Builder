from langchain.embeddings import CacheBackedEmbeddings
from langchain.storage import LocalFileStore
from langchain_openai import (AzureChatOpenAI, AzureOpenAI,
                              AzureOpenAIEmbeddings)
from os import getenv
from dotenv import load_dotenv


load_dotenv()

# OpenAI Embeddings
underlying_embeddings = AzureOpenAIEmbeddings(
    azure_deployment=getenv("EMBEDDINGS_NAME"),
)

store = LocalFileStore("./cache/")

embeddings = CacheBackedEmbeddings.from_bytes_store(
    underlying_embeddings, store, namespace=underlying_embeddings.model, query_embedding_cache=True
)

# OpenAI Completion
llm = AzureOpenAI(deployment_name=getenv("DEPLOYMENT_NAME"), temperature=0)
llm.max_tokens = 2000

gpt4_llm = AzureChatOpenAI(
    azure_endpoint=getenv("AZURE_OPENAI_GPT4_ENDPOINT"),
    deployment_name=getenv("GPT4_DEPLOYMENT_NAME"),
    api_key=getenv("GPT4_OPENAI_API_KEY"),
    api_version=getenv("OPENAI_API_VERSION"),
    temperature=0, max_tokens=4000
)


gpt3_llm = AzureChatOpenAI(
    azure_endpoint=getenv("AZURE_OPENAI_GPT3_ENDPOINT"),
    deployment_name=getenv("GPT3_DEPLOYMENT_NAME"),
    api_key=getenv("GPT3_OPENAI_API_KEY"),
    api_version=getenv("OPENAI_API_VERSION"),
    temperature=0.4, max_tokens=1000,
)

if __name__ == "__main__":
    print(embeddings.embed_query("Hi")[:5])
    print(gpt3_llm.invoke("Tell me a joke").content)
    print(gpt4_llm.invoke("Tell me a joke").content)

