from typing import Dict, List

from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import (ChatPromptTemplate,
                                    HumanMessagePromptTemplate, PromptTemplate)

from utils.common.llm_core import llm
from utils.custom.models import UnstructuredRelation

parser = JsonOutputParser(pydantic_object=UnstructuredRelation)


def get_graph_creation_prompt(
    node_labels: List[str] = [], rel_types: List[str] = [], examples: List[Dict] = []
):

    system_message = SystemMessage(
        content="""
    You are a top-tier algorithm designed for extracting information in
    structured formats to build a knowledge graph. Your task is to identify "
    the entities and relations requested with the user prompt from a given "
    text. You must generate the output in a JSON format containing a list "
    'with JSON objects. Each object should have the keys: "head", '
    '"head_type", "relation", "tail", and "tail_type". The "head" '
    key must contain the text of the extracted entity with one of the types "
    from the provided list in the user prompt.",

    'The "head_type" key must contain the type of the extracted head entity, '
    "which must be one of the types from {node_labels_str}."

    'The "relation" key must contain the type of relation between the "head" '
    'and the "tail", which must be one of the relations from {rel_types_str}.'

    'The "tail" key must represent the text of an extracted entity which is '
    'the tail of the relation, and the "tail_type" key must contain the type '
    "of the tail entity from {node_labels_str}."

    Attempt to extract as many entities and relations as you can. Maintain "
    Entity Consistency: When extracting entities, it's vital to ensure "
            'consistency. If an entity, such as "John Doe", is mentioned multiple '
    times in the text but is referred to by different names or pronouns "
            '(e.g., "Joe", "he"), always use the most complete identifier for '
    that entity. The knowledge graph should be coherent and easily "
    understandable, so maintaining consistency in entity references is "
    crucial.",

    IMPORTANT NOTES:\n- Don't add any explanation and text.",
    """
    )

    human_prompt = PromptTemplate(
        template="""Based on the following example, extract entities and 
    relations from the provided text.
    Use the following entity types, don't use other entity that is not defined below:
    # ENTITY TYPES:
    {node_labels}

    Use the following relation types, don't use other relation that is not defined below:
    # RELATION TYPES:
    {rel_types}

    Below are a number of examples of text and their extracted entities and relationships.
    {examples}

    For the following text, extract entities and relations as in the provided example.
    {format_instructions}
    Text: {input}""",
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


def get_graph_chain(
    node_labels: List[str] = [], rel_types: List[str] = [], examples: List[Dict] = []
):
    prompt = get_graph_creation_prompt(
        node_labels=node_labels, rel_types=rel_types, examples=examples
    )
    chain = prompt | llm | JsonOutputParser()
    return chain


follow_up_prompt = PromptTemplate.from_template(
    """
You are a helpful chatbot. You are tasked with answering questions over a graph database. Following are the queries for which data was fetched but a human could not give an answer. Analyze the query and context to give a suitable answer.
Only give the final answer in a sentence form.

Context:
{context}

Query: {query}
Answer:
"""
)

follow_up_chain = follow_up_prompt | llm | StrOutputParser()
