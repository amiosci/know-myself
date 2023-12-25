import abc
import tempfile

from urllib.parse import urlparse, ParseResult
from langchain.docstore.document import Document
from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import ArxivLoader
from langchain.document_loaders import SeleniumURLLoader
from langchain.text_splitter import NLTKTextSplitter
from langchain.document_transformers import Html2TextTransformer
from langchain.document_loaders.blob_loaders.youtube_audio import YoutubeAudioLoader
from langchain.document_loaders.generic import GenericLoader
from langchain.document_loaders.parsers.audio import OpenAIWhisperParserLocal


def _get_url_extension(url: ParseResult) -> str:
    return url.path.split(".")[-1]


class DocumentLoader(abc.ABC):
    url: ParseResult

    def __init__(self, url: ParseResult):
        self.url = url

    @staticmethod
    @abc.abstractmethod
    def can_load(url: ParseResult) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def load(self) -> list[Document]:
        raise NotImplementedError()

    @property
    def target_url(self) -> str:
        return self.url.geturl()


class DefaultDocumentLoader(DocumentLoader):
    @staticmethod
    def can_load(url: ParseResult) -> bool:
        return True

    def load(self) -> list[Document]:
        return []


class ArxivDocumentLoader(DocumentLoader):
    @staticmethod
    def can_load(url: ParseResult) -> bool:
        valid_site = url.netloc == "arxiv.org"
        valid_path_prefixes = ["/pdf/", "/abs/"]
        has_valid_path_prefix = any(url.path.startswith(x) for x in valid_path_prefixes)

        return valid_site and has_valid_path_prefix

    def load(self) -> list[Document]:
        query = self._load_query()
        if not query:
            raise ValueError("Invalid Arxiv URL requested")

        loader = ArxivLoader(query=query)
        return loader.load()

    def _load_query(self) -> str:
        if self.url.path.startswith("/pdf/"):
            # https://arxiv.org/pdf/2305.05003.pdf
            return self.url.path[1:].strip("pdf")[1:-1]

        # https://arxiv.org/abs/2305.05003
        return self.url.path.split("/")[-1]


class PDFDocumentLoader(DocumentLoader):
    @staticmethod
    def can_load(url: ParseResult) -> bool:
        extension = _get_url_extension(url)
        return extension.lower() in ["pdf"]

    def load(self) -> list[Document]:
        loader = PyPDFLoader(self.target_url)
        pages = loader.load_and_split()
        return pages


class WebPageDocumentLoader(DocumentLoader):
    @staticmethod
    def can_load(url: ParseResult) -> bool:
        valid_schemes = ["http", "https"]
        return url.scheme in valid_schemes

    def load(self) -> list[Document]:
        loader = SeleniumURLLoader(urls=[self.target_url])
        text = loader.load()

        html2text = Html2TextTransformer()
        docs_transformed = html2text.transform_documents(text)

        text_splitter = NLTKTextSplitter(chunk_size=1000, chunk_overlap=300)
        texts = text_splitter.split_documents(docs_transformed)

        return texts


class YouTubeVideoDocumentLoader(DocumentLoader):
    @staticmethod
    def can_load(url: ParseResult) -> bool:
        is_youtube = url.netloc in ["www.youtube.com", "youtube.com"]
        valid_schemes = ["http", "https"]
        return (url.scheme in valid_schemes) and is_youtube

    def load(self) -> list[Document]:
        with tempfile.TemporaryDirectory() as d:
            loader = GenericLoader(
                YoutubeAudioLoader([self.target_url], d), OpenAIWhisperParserLocal()
            )
            return loader.load()


# TODO: Define by namespace lookup
_LOADERS = [
    ArxivDocumentLoader,
    PDFDocumentLoader,
    YouTubeVideoDocumentLoader,
]

_FALLBACK_LOADERS = [
    WebPageDocumentLoader,
    DefaultDocumentLoader,
]


def locate(url: str) -> DocumentLoader | None:
    parsed_url = urlparse(url)
    loaders = [x for x in (_LOADERS + _FALLBACK_LOADERS) if x.can_load(parsed_url)]
    for loader in loaders:
        print(f"testing {loader.__name__}")
        if loader.can_load(parsed_url):
            return loader(parsed_url)

    return None


if __name__ == "__main__":

    def confirm_loader_functionality(url: str, loader_type: type):
        loader = locate(url)

        assert loader is not None
        assert isinstance(loader, loader_type)

        docs = loader.load()
        assert len(docs) > 0

    webpage_url = "https://docs.python.org/3/library/urllib.parse.html"
    confirm_loader_functionality(webpage_url, WebPageDocumentLoader)

    arxiv_urls = [
        "https://arxiv.org/pdf/2305.05003.pdf",
        "https://arxiv.org/abs/2305.05003",
    ]
    for arxiv_url in arxiv_urls:
        confirm_loader_functionality(arxiv_url, ArxivDocumentLoader)

    youtube_urls = [
        "https://youtube.com/shorts/IicbiwTAslE?si=H1qA7---M4ZiuHTc",
        # Too large for GPU under standard usage
        # Evaluate PowerInfer, and the like
        # "https://www.youtube.com/watch?v=edyqWHRgSX8",
    ]

    for youtube_url in youtube_urls:
        confirm_loader_functionality(youtube_url, YouTubeVideoDocumentLoader)
