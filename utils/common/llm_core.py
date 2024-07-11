from os import getenv

from dotenv import load_dotenv
from langchain.embeddings import CacheBackedEmbeddings
from langchain.storage import LocalFileStore

load_dotenv()

store = LocalFileStore("./cache/")

llm_provider = getenv("LLM_PROVIDER")
llm_name = getenv("LLM_NAME")
embeddings_name = getenv("EMBEDDINGS_NAME")

if llm_provider == "openai":
    from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

    # OpenAI Completion
    llm = AzureChatOpenAI(
        deployment_name=llm_name,
        temperature=0,
        max_tokens=2000,
    )

    # OpenAI Chat
    underlying_embeddings = AzureOpenAIEmbeddings(
        azure_deployment=embeddings_name,
    )

elif llm_provider == "ollama":
    from langchain_community.embeddings import OllamaEmbeddings
    from langchain_community.llms.ollama import Ollama

    base_url = getenv("OLLAMA_URL") or "http://localhost:11434"
    llm = Ollama(base_url=base_url, model=llm_name)

    underlying_embeddings = OllamaEmbeddings(base_url=base_url, model=embeddings_name)

embeddings = CacheBackedEmbeddings.from_bytes_store(
    underlying_embeddings,
    store,
    namespace=underlying_embeddings.model,
    query_embedding_cache=True,
)

if __name__ == "__main__":
    print(embeddings.embed_query("Hi")[:5])
    print(llm.invoke("Tell me a joke"))
