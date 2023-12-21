from urllib.parse import urlparse
from langchain.docstore.document import Document
from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import ArxivLoader
from langchain.document_loaders import SeleniumURLLoader
from langchain.text_splitter import NLTKTextSplitter
from langchain.document_transformers import Html2TextTransformer


def _load_arxiv(query: str) -> list[Document]:
    loader = ArxivLoader(query=query)
    return loader.load()


def _load_pdf(url: str) -> list[Document]:
    loader = PyPDFLoader(url)
    pages = loader.load_and_split()
    return pages


def _load_html(url: str) -> list[Document]:
    loader = SeleniumURLLoader(urls=[url])
    text = loader.load()

    html2text = Html2TextTransformer()
    docs_transformed = html2text.transform_documents(text)

    text_splitter = NLTKTextSplitter(chunk_size=1000, chunk_overlap=300)
    texts = text_splitter.split_documents(docs_transformed)

    return texts


def get_url_documents(url: str) -> list[Document]:
    parsed_url = urlparse(url)
    extension = parsed_url.path.split(".")[-1]
    texts = None
    if extension == "pdf":
        if parsed_url.netloc == "arxiv.org":
            texts = _load_arxiv(parsed_url.path[1:].strip("pdf")[1:-1])
        else:
            texts = _load_pdf(url)
    else:
        texts = _load_html(url)

    if not texts:
        raise RuntimeError(f"Cannot extract documents from {url}")

    return texts
