import streamlit as st

from utils.custom.chains import follow_up_chain
from utils.custom.knowledge_graph import Neo4JKnowledgeGraph

neo4j = Neo4JKnowledgeGraph(document_name="")
chain = neo4j.get_qa_chain()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

st.markdown("# Knowledge Graph QA")

query = st.chat_input("Enter query")

if query:
    with st.chat_message("user"):
        st.markdown(f":red[Query]: {query}")
        st.session_state.messages.append({"role": "user", "content": query})

    with st.spinner("Getting answer"):
        try:
            query_with_instructions = f"{query}. INSTRUCTIONS: Replace size() with COUNT {{}} in Query. Search terms are present in the id property. Use the most similar Relationship present in the schema. Use variable.property IS NOT NULL instead of exists(variable.property) for checking property existence."
            response = chain(query_with_instructions)

            result = response["result"]
            intermediate_step = response["intermediate_steps"]
            print(response["intermediate_steps"])
            cypher_query, context = (
                intermediate_step[0]["query"],
                intermediate_step[1]["context"],
            )

            with st.chat_message("assistant"):
                st.markdown(f":blue[Answer]: {result}")
                st.session_state.messages.append(
                    {"role": "assistant", "content": result}
                )

            with st.expander(":yellow[View Query]"):
                st.markdown(f"Query:\n```cypher\n{cypher_query}\n```")
                st.markdown(f"Context:")
                st.json(context)

            if result == "I don't know the answer.":
                final_answer = follow_up_chain.invoke(
                    {"query": query, "context": context}
                )
                with st.chat_message("assistant"):
                    st.markdown(f":green[Final Answer]: {final_answer}")
                    st.session_state.messages.append(
                        {"role": "assistant", "content": final_answer}
                    )

        except Exception as e:
            st.markdown(f":red[Error]: Could not fetch results\n{e}")
            st.session_state.messages.append({"role": "assistant", "content": e})
