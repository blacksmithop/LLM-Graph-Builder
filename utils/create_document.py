from langchain.docstore.document import Document
from pandas import DataFrame


def get_documents_from_df(df: DataFrame, insight_column: str = "insight", id_column: str = "insightID"):
    
    if len({insight_column, id_column} - set(df.columns)):
            raise ValueError(f"Check if both {insight_column} and {id_column} are present as Columns")
        
    documents = [
        Document(
            page_content=insight, metadata={
                "insightID": insightID
            }) for insight, insightID in zip(df[insight_column], df[id_column])
        ]
    return documents