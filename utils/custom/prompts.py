BASE_PROMPT = """
You are a top-tier algorithm designed for extracting information in
structured formats to build a knowledge graph. Your task is to identify "
the entities and relations requested with the user prompt from a given "
text. You must generate the output in a JSON format containing a list "
'with JSON objects. Each object should have the keys: "head", '
'"head_type", "relation", "tail", and "tail_type". The "head" '
key must contain the text of the extracted entity with one of the types "
from the provided list in the user prompt.",
"""

HEAD_TAIL_PROMPT = """
'The "head_type" key must contain the type of the extracted head entity, '
"which must be one of the types from {node_labels}."

'The "relation" key must contain the type of relation between the "head" '
'and the "tail", which must be one of the relations from {rel_types}.'

'The "tail" key must represent the text of an extracted entity which is '
'the tail of the relation, and the "tail_type" key must contain the type '
"of the tail entity from {node_labels}."
"""

INSTRUCTION_PROMPT = """
Attempt to extract as many entities and relations as you can. Maintain "
Entity Consistency: When extracting entities, it's vital to ensure "
        'consistency. If an entity, such as "John Doe", is mentioned multiple '
times in the text but is referred to by different names or pronouns "
        '(e.g., "Joe", "he"), always use the most complete identifier for '
that entity. The knowledge graph should be coherent and easily "
understandable, so maintaining consistency in entity references is "
crucial.",

IMPORTANT NOTES:\n- Don't add any explanation and text.
"""

NODE_RELATION_EXAMPLE_PROMPT = """
Based on the following example, extract entities and 
relations from the provided text.
Use the following entity types, don't use other entity that is not defined below:
# ENTITY TYPES:
{node_labels}

Use the following relation types, don't use other relation that is not defined below:
# RELATION TYPES:
{rel_types}
"""

EXAMPLE_PROMPT = """
Below are a number of examples of text and their extracted entities and relationships.
{examples}
"""

SCHEMA_PROMPT = """
For the following text, extract entities and relations as in the provided example.
{schema}

Text: {input}
"""
