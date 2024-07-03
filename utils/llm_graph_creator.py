from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_experimental.graph_transformers.llm import _convert_to_graph_document
from langchain_core.documents import Document
from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship
from typing import Any, Dict, cast
from langfuse.callback import CallbackHandler


langfuse_handler = CallbackHandler(
    secret_key="sk-lf-12ab7f6d-c911-4f9c-9475-e7d9e140ffd9",
    public_key="pk-lf-78c3dfa2-3a70-4e9a-9421-8a9e29b3973f",
    host="http://localhost:3000"
)

class LLMGraphTransformerWithLogging(LLMGraphTransformer):
    
    def process_response(self, document: Document) -> GraphDocument:
        """
        Processes a single document, transforming it into a graph document using
        an LLM based on the model's schema and constraints.
        """
        text = document.page_content
        raw_schema = self.chain.invoke({"input": text}, config={"callbacks": [langfuse_handler]})
        if self._function_call:
            raw_schema = cast(Dict[Any, Any], raw_schema)
            nodes, relationships = _convert_to_graph_document(raw_schema)
        else:
            nodes_set = set()
            relationships = []
            if not isinstance(raw_schema, str):
                raw_schema = raw_schema.content
            parsed_json = self.json_repair.loads(raw_schema)
            for rel in parsed_json:
                # Nodes need to be deduplicated using a set
                nodes_set.add((rel["head"], rel["head_type"]))
                nodes_set.add((rel["tail"], rel["tail_type"]))

                source_node = Node(id=rel["head"], type=rel["head_type"])
                target_node = Node(id=rel["tail"], type=rel["tail_type"])
                relationships.append(
                    Relationship(
                        source=source_node, target=target_node, type=rel["relation"]
                    )
                )
            # Create nodes list
            nodes = [Node(id=el[0], type=el[1]) for el in list(nodes_set)]

        # Strict mode filtering
        if self.strict_mode and (self.allowed_nodes or self.allowed_relationships):
            if self.allowed_nodes:
                lower_allowed_nodes = [el.lower() for el in self.allowed_nodes]
                nodes = [
                    node for node in nodes if node.type.lower() in lower_allowed_nodes
                ]
                relationships = [
                    rel
                    for rel in relationships
                    if rel.source.type.lower() in lower_allowed_nodes
                    and rel.target.type.lower() in lower_allowed_nodes
                ]
            if self.allowed_relationships:
                relationships = [
                    rel
                    for rel in relationships
                    if rel.type.lower()
                    in [el.lower() for el in self.allowed_relationships]
                ]

        return GraphDocument(nodes=nodes, relationships=relationships, source=document)