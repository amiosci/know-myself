from langchain.chains import create_extraction_chain
from langchain_experimental.llms.ollama_functions import OllamaFunctions
from pydantic import BaseModel, Field


def _llm(**kwargs):
    return OllamaFunctions(
        base_url=kwargs.pop("base_url", "http://localhost:11434"),
        model=kwargs.pop("model", "llama2"),
        verbose=kwargs.pop("verbose", True),
        temperature=kwargs.pop("temperature", 0.0),
        **kwargs
    )


def EntityRelationSchema(BaseModel):
    pass


if __name__ == '__main__':
    inp = """Alex is 5 feet tall. Claudia is 1 feet taller Alex and jumps higher than him. Claudia is a brunette and Alex is blonde."""
    schema = {
        "properties": {
            "name": {"type": "string"},
            "height": {"type": "integer"},
            "hair_color": {"type": "string"},
        },
        "required": ["name", "height"],
    }

    llm = _llm()
    chain = create_extraction_chain(schema, llm)
    result = chain.run(inp)
    print(result)

    from langchain.document_loaders import WikipediaLoader
    from langchain.text_splitter import TokenTextSplitter

    # Read the wikipedia article
    raw_documents = WikipediaLoader(query="Walt Disney").load()
    # Define chunking strategy
    text_splitter = TokenTextSplitter(chunk_size=2048, chunk_overlap=24)

    # Only take the first the raw_documents
    documents = text_splitter.split_documents(raw_documents[:3])
    for d in documents:
        print(d)
        # extract_and_store_graph(d)