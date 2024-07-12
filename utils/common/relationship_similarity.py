from langchain_openai import AzureOpenAIEmbeddings
from numpy import dot
from numpy.linalg import norm


def cosine_similarity(a, b):
    score = dot(a, b) / (norm(a) * norm(b))
    normalized_score = round(score * 100, 2)
    return normalized_score


class EmbeddingSimilarity:
    def __init__(self, embeddings: AzureOpenAIEmbeddings) -> None:
        self.emb_cache = {}
        self.similar_entities = {}
        self.embeddings = embeddings

    def get_similar_relationship(self, entity: str):
        entity = entity.title()
        entity_norm = " ".join(entity.split("_"))
        matching_key = next(
            (
                key
                for key, value_list in self.similar_entities.items()
                if entity in value_list
            ),
            None,
        )
        if matching_key:
            return entity

        # if entity in self.emb_cache:
        # return True, entity

        entity_embedding = self.embeddings.embed_query(entity_norm)
        self.emb_cache[entity] = entity_embedding

        for key in self.similar_entities.keys():
            key_embedding = self.emb_cache[key]
            cosine_sim = cosine_similarity(entity_embedding, key_embedding)
            if cosine_sim > 80:
                self.similar_entities[key].append(entity)
                return key

        self.similar_entities[entity] = []
        key_embedding = self.embeddings.embed_query(entity)
        return entity
