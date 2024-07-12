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

# For creating chained Entity Nodes
CORRELATION_EXAMPLE_PROMPT = """
Below are a number of examples of text and their extracted entities and relationships.
Eg: 
Docetaxel alone is the approved therapy in second line stage IV NSCLC. but often HCPs use other drugs ( with the exception of patients with tumors harboring targeted alterations). In his center: Paclitaxel (80 to 90mg/m2 in a weekly schedule) plus bevacizumab (7.5 to 15mg/kg every 21 days) is a standard regimen as second line or third line treatment in stage IV NSCLC. The toxicity profile is acceptable. The results of the IFCT 1103 ULTIMATE study place weekly paclitaxel plus bevacizumab as a valid option in this population. However, docétaxel is used for clinical trial as second line comparator arm
{{
"nodes": 
{{
        [
        {{
                "head": "HCP",
                "head_type": "Person",
                "relation": "APPROVED_THERAPY",
                "tail": "Docetaxel",
                "tail_type": "Drug",
        }},
        {{
                "head": "HCP",
                "head_type": "Person",
                "relation": "IS_STANDARD_REGIMEN",
                "tail": "Paclitaxel and Bevacizumab",
                "tail_type": "Drug",
        }},
        {{
                "head": "Paclitaxel and Bevacizumab",
                "head_type": "Drug",
                "relation": "SECOND_OR_THIRD_LINE_TREATMENT",
                "tail": "stage IV NSCLC",
                "tail_type": "Disease",
        }},
        {{
                "head": "Paclitaxel and Bevacizumab",
                "head_type": "Drug",
                "relation": "VALID_OPTION_IN_POPULATION",
                "tail": "IFCT 1103 ULTIMATE study",
                "tail_type": "Clinical Trial",
        }},
        {{
                "head": "IFCT 1103 ULTIMATE study",
                "head_type": "Clinical Trial",
                "relation": "SECOND_LINE_COMPARATOR",
                "tail": "Docetaxel",
                "tail_type": "Drug",
        }}
        ]
}}
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
