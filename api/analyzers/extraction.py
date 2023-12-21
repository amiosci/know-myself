import dataclasses


@dataclasses.dataclass
class EntityRelation:
    origin_node: str
    destination_node: str
    relation: str
    weight: float = 1.0


from langchain.graphs.graph_document import (
    Node as BaseNode,
    Relationship as BaseRelationship,
)
from langchain.pydantic_v1 import Field, BaseModel
from langchain.prompts import ChatPromptTemplate


class Property(BaseModel):
    """A single property consisting of key and value"""

    key: str = Field(..., description="key")
    value: str = Field(..., description="value")


class Node(BaseNode):
    properties: list[Property] | None = Field(
        None, description="List of node properties"
    )


class Relationship(BaseRelationship):
    properties: list[Property] | None = Field(
        None, description="List of relationship properties"
    )


class KnowledgeGraph(BaseModel):
    """Generate a knowledge graph with entities and relationships."""

    nodes: list[Node] = Field(..., description="List of nodes in the knowledge graph")
    rels: list[Relationship] = Field(
        ..., description="List of relationships in the knowledge graph"
    )


from langchain.chat_models import ChatOllama
from langchain.chains.openai_functions import (
    create_openai_fn_chain,
    create_openai_fn_runnable,
    create_structured_output_chain,
    create_structured_output_runnable,
)


def _default_chat_llm(**kwargs):
    return ChatOllama(
        base_url=kwargs.pop("base_url", "http://localhost:11434"),
        model=kwargs.pop("model", "llama2"),
        verbose=kwargs.pop("verbose", False),
        temperature=kwargs.pop("temperature", 0.0),
        **kwargs,
    )


def get_extraction_chain(
    allowed_nodes: list[str] | None = None, allowed_rels: list[str] | None = None
):
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""# Knowledge Graph Instructions for GPT-4
## 1. Overview
You are a top-tier algorithm designed for extracting information in structured formats to build a knowledge graph.
- **Nodes** represent entities and concepts. They're akin to Wikipedia nodes.
- The aim is to achieve simplicity and clarity in the knowledge graph, making it accessible for a vast audience.
## 2. Labeling Nodes
- **Consistency**: Ensure you use basic or elementary types for node labels.
  - For example, when you identify an entity representing a person, always label it as **"person"**. Avoid using more specific terms like "mathematician" or "scientist".
- **Node IDs**: Never utilize integers as node IDs. Node IDs should be names or human-readable identifiers found in the text.
{'- **Allowed Node Labels:**' + ", ".join(allowed_nodes) if allowed_nodes else ""}
{'- **Allowed Relationship Types**:' + ", ".join(allowed_rels) if allowed_rels else ""}
## 3. Handling Numerical Data and Dates
- Numerical data, like age or other related information, should be incorporated as attributes or properties of the respective nodes.
- **No Separate Nodes for Dates/Numbers**: Do not create separate nodes for dates or numerical values. Always attach them as attributes or properties of nodes.
- **Property Format**: Properties must be in a key-value format.
- **Quotation Marks**: Never use escaped single or double quotes within property values.
- **Naming Convention**: Use camelCase for property keys, e.g., `birthDate`.
## 4. Coreference Resolution
- **Maintain Entity Consistency**: When extracting entities, it's vital to ensure consistency.
If an entity, such as "John Doe", is mentioned multiple times in the text but is referred to by different names or pronouns (e.g., "Joe", "he"), 
always use the most complete identifier for that entity throughout the knowledge graph. In this example, use "John Doe" as the entity ID.  
Remember, the knowledge graph should be coherent and easily understandable, so maintaining consistency in entity references is crucial. 
## 5. Strict Compliance
Adhere to the rules strictly. Non-compliance will result in termination.""",
            ),
            (
                "human",
                "Use the given format to extract information from the following input: {input}",
            ),
            ("human", "Tip: Make sure to answer in the correct format"),
        ]
    )
    return create_structured_output_chain(
        KnowledgeGraph, _default_chat_llm(), prompt, verbose=False
    )


from langchain.schema import Document


def extract_and_store_graph(
    document: Document, nodes: list[str] | None = None, rels: list[str] | None = None
) -> None:
    # Extract graph data using OpenAI functions
    extract_chain = get_extraction_chain(nodes, rels)
    data = extract_chain.run(document.page_content)
    print(data)

    # persist!

    # # Construct a graph document
    # graph_document = GraphDocument(
    #     nodes=[map_to_base_node(node) for node in data.nodes],
    #     relationships=[map_to_base_relationship(rel) for rel in data.rels],
    #     source=document,
    # )
    # # Store information into a graph
    # graph.add_graph_documents([graph_document])


if __name__ == '__main__':
    from langchain.document_loaders import WikipediaLoader
    from langchain.text_splitter import TokenTextSplitter

    # Read the wikipedia article
    raw_documents = WikipediaLoader(query="Walt Disney").load()
    # Define chunking strategy
    text_splitter = TokenTextSplitter(chunk_size=2048, chunk_overlap=24)

    # Only take the first the raw_documents
    documents = text_splitter.split_documents(raw_documents[:3])
    for d in documents:
        extract_and_store_graph(d)

# def search_knowledgebase(search_query):

#     vector = Vector(value=generate_embeddings(search_query), k=3, fields="embedding")
#     print("search query: ", search_query)
#     # print("products: ", products.split(","))
#     # product_filter = " or ".join([f"product eq '{product}'" for product in products.split(",")])
#     results = azcs_search_client.search(
#         search_text=search_query,
#         vectors= [vector],
#         # filter= product_filter,
#         query_type="semantic", query_language="en-us", semantic_configuration_name='default', query_caption="extractive", query_answer="extractive",
#         select=["sourcepage","content"],
#         top=3
#     )
#     text_content =""
#     for result in results:
#         text_content += f"{result['sourcepage']}\n{result['content']}\n"
#     # print("text_content", text_content)
#     return text_content
