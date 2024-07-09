import streamlit as st
from utils.custom.neo4j_node_handler import Neo4J

neo4j = Neo4J(document_name="")
chain = neo4j.get_qa_chain()

st.markdown("# Knowledge Graph QA")

query = st.chat_input("Enter query")

if query:
    st.markdown(f"#### :red[Query]: {query}")
    
    with st.spinner("Getting answer"):
        try:
            response = chain(query)
        except ValueError:
            fixed_query = f"{query} replace size() with COUNT {{}} in Query"
            response = chain(fixed_query)
            
        result = response["result"]
        intermediate_step = response["intermediate_steps"]
        print(response["intermediate_steps"])
        cypher_query, context = intermediate_step[0]["query"], intermediate_step[1]["context"]
        
        st.markdown(f"#### :blue[Answer]: {result}")
        
        with st.expander(":yellow[View Query]"):
            st.markdown(f"#### Query:\n```cypher\n{cypher_query}\n```")
            st.markdown(f"#### Context:")
            st.json(context)