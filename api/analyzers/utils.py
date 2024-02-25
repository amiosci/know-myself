import os
from langchain.llms import Ollama
from langchain.chat_models import ChatOllama
from langchain_experimental.llms.ollama_functions import OllamaFunctions


_DEFAULT_OLLAMA_MODEL = "gemma:7b"


def functions_llm(verbose: bool = False, **kwargs):
    return OllamaFunctions(
        tool_system_prompt_template="",
        verbose=verbose,
        llm=chat_llm(
            **dict(
                kwargs,
                **{
                    "verbose": verbose,
                    "format": "json",
                    "model": _DEFAULT_OLLAMA_MODEL,
                },
            )
        ),
    )


def chat_llm(**kwargs):
    return ChatOllama(
        base_url=kwargs.pop("base_url", "http://localhost:11434"),
        model=kwargs.pop(
            "model", os.environ.get("KMS_OLLAMA_MODEL", _DEFAULT_OLLAMA_MODEL)
        ),
        verbose=kwargs.pop("verbose", False),
        temperature=kwargs.pop("temperature", 0.0),
        **kwargs,
    )


def llm(**kwargs):
    return Ollama(
        base_url=kwargs.pop("base_url", "http://localhost:11434"),
        model=kwargs.pop(
            "model", os.environ.get("KMS_OLLAMA_MODEL", _DEFAULT_OLLAMA_MODEL)
        ),
        verbose=kwargs.pop("verbose", False),
        temperature=kwargs.pop("temperature", 0.0),
        **kwargs,
    )
