import logging
from typing import Any, Dict, List, Optional, cast, Sequence

from langchain_community.graphs.graph_document import (GraphDocument, Node,
                                                       Relationship)
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import (ChatPromptTemplate,
                                    HumanMessagePromptTemplate, PromptTemplate)
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_experimental.graph_transformers.llm import (
    UnstructuredRelation, _convert_to_graph_document, examples)
from langfuse.callback import CallbackHandler
from time import sleep
import logging


langfuse_handler = CallbackHandler(
    secret_key="sk-lf-12ab7f6d-c911-4f9c-9475-e7d9e140ffd9",
    public_key="pk-lf-78c3dfa2-3a70-4e9a-9421-8a9e29b3973f",
    host="http://localhost:3000",
)

SLEEP_TIME = 30

class LLMGraphTransformerWithLogging(LLMGraphTransformer):


    def convert_to_graph_documents(
        self, documents: Sequence[Document]
    ) -> List[GraphDocument]:
        """Convert a sequence of documents into graph documents.

        Args:
            documents (Sequence[Document]): The original documents.
            **kwargs: Additional keyword arguments.

        Returns:
            Sequence[GraphDocument]: The transformed documents as graphs.
        """
        results = []
        
        for index, document in enumerate(documents, start=1):
            response = self.process_response(document)
            results.append(response)
            logging.info(f"[Process_{index}] Sleeping for {SLEEP_TIME} seconds 💤💤")
            sleep(SLEEP_TIME)
            
        return results
    
    def process_response(self, document: Document) -> GraphDocument:
        """
        Processes a single document, transforming it into a graph document using
        an LLM based on the model's schema and constraints.
        """

        
        text = document.page_content
        raw_schema = self.chain.invoke(
            {"input": text}, config={"callbacks": [langfuse_handler]}
        )
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

    def create_unstructured_prompt(
        self,
        node_labels: Optional[List[str]] = None,
        rel_types: Optional[List[str]] = None,
    ) -> ChatPromptTemplate:
        logging.warning("Using custom prompt")

        node_labels_str = str(node_labels) if node_labels else ""
        rel_types_str = str(rel_types) if rel_types else ""
        base_string_parts = [
            "You are a top-tier algorithm designed for extracting information in "
            "structured formats to build a knowledge graph. Your task is to identify "
            "the entities and relations requested with the user prompt from a given "
            "text. You must generate the output in a JSON format containing a list "
            'with JSON objects. Each object should have the keys: "head", '
            '"head_type", "relation", "tail", and "tail_type". The "head" '
            "key must contain the text of the extracted entity with one of the types "
            "from the provided list in the user prompt.",
            (
                f'The "head_type" key must contain the type of the extracted head entity, '
                f"which can be one of the types from {node_labels_str}. Use the following as reference"
                if node_labels
                else ""
            ),
            (
                f'The "relation" key must contain the type of relation between the "head" '
                f'and the "tail", which can be one of the relations from {rel_types_str}. Use the following as reference'
                if rel_types
                else ""
            ),
            (
                f'The "tail" key must represent the text of an extracted entity which is '
                f'the tail of the relation, and the "tail_type" key can contain the type '
                f"of the tail entity from {node_labels_str}."
                if node_labels
                else ""
            ),
            "Attempt to extract as many entities and relations as you can. Maintain "
            "Entity Consistency: When extracting entities, it's vital to ensure "
            'consistency. If an entity, such as "John Doe", is mentioned multiple '
            "times in the text but is referred to by different names or pronouns "
            '(e.g., "Joe", "he"), always use the most complete identifier for '
            "that entity. The knowledge graph should be coherent and easily "
            "understandable, so maintaining consistency in entity references is "
            "crucial.",
            "IMPORTANT NOTES:\n- Don't add any explanation and text.",
        ]
        system_prompt = "\n".join(filter(None, base_string_parts))

        system_message = SystemMessage(content=system_prompt)
        parser = JsonOutputParser(pydantic_object=UnstructuredRelation)

        human_prompt = PromptTemplate(
            template="""Based on the following example, extract entities and 
    relations from the provided text.\n\n
    Use the following entity types, don't use other entity that is not defined below:
    # ENTITY TYPES:
    {node_labels}

    Use the following relation types, don't use other relation that is not defined below:
    # RELATION TYPES:
    {rel_types}

    Below are a number of examples of text and their extracted entities and relationships.
    {examples}

    For the following text, extract entities and relations as in the provided example.
    {format_instructions}\nText: {input}""",
            input_variables=["input"],
            partial_variables={
                "format_instructions": parser.get_format_instructions(),
                "node_labels": node_labels,
                "rel_types": rel_types,
                "examples": examples,
            },
        )

        human_message_prompt = HumanMessagePromptTemplate(prompt=human_prompt)

        chat_prompt = ChatPromptTemplate.from_messages(
            [system_message, human_message_prompt]
        )
        return chat_prompt
