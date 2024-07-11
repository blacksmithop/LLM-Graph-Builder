from typing import Dict, List

from langchain.prompts import PromptTemplate
from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import JsonOutputParser

from utils.common.openi_core import gpt3_llm
from utils.custom.models import UnstructuredRelationNodes
from utils.custom.prompts import (BASE_PROMPT, EXAMPLE_PROMPT,
                                  HEAD_TAIL_PROMPT, INSTRUCTION_PROMPT,
                                  NODE_RELATION_EXAMPLE_PROMPT, SCHEMA_PROMPT)

parser = JsonOutputParser(pydantic_object=UnstructuredRelationNodes)

# constants
from utils.common.constants import allowed_nodes, allowed_relations, examples

gpt3_llm.max_tokens = 1000
gpt3_llm.temperature = 0.4


def get_graph_chain_v2(
    node_labels: List[str] = allowed_nodes,
    rel_types: List[str] = allowed_relations[30:60],
    examples: List[Dict] = examples,
):
    system_message = SystemMessage(
        content=f"{BASE_PROMPT}\n{HEAD_TAIL_PROMPT}\n{INSTRUCTION_PROMPT}"
    )
    human_prompt = PromptTemplate(
        template=f"{NODE_RELATION_EXAMPLE_PROMPT}\n{EXAMPLE_PROMPT}\n{SCHEMA_PROMPT}",
        input_variables=["input"],
        partial_variables={
            "schema": parser.get_format_instructions(),
            "node_labels": node_labels,
            "rel_types": rel_types,
            "examples": examples,
        },
    )
    generate_graph_chain = (
        human_prompt
        | gpt3_llm
        | JsonOutputParser(pydantic_object=UnstructuredRelationNodes)
    )

    return generate_graph_chain