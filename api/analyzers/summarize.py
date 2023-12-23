from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate

from langchain.docstore.document import Document

from analyzers import utils


async def summarize_document(texts: list[Document]) -> str:
    prompt_template = """Write a concise summary of the following:
    {text}
    CONCISE SUMMARY:"""
    prompt = PromptTemplate.from_template(prompt_template)

    refine_template = (
        "Your job is to produce a final summary with key learnings\n"
        "We have provided an existing summary up to a certain point: {existing_answer}\n"
        "We have the opportunity to refine the existing summary"
        "(only if needed) with detailed context below.\n"
        "------------\n"
        "{text}\n"
        "------------\n"
        "Given the new context, refine the original summary"
        "If the context isn't useful, return the original summary."
    )
    refine_prompt = PromptTemplate.from_template(refine_template)
    refine_chain = load_summarize_chain(
        utils.llm(),
        chain_type="refine",
        question_prompt=prompt,
        refine_prompt=refine_prompt,
        return_intermediate_steps=True,
    )
    refine_outputs = refine_chain({"input_documents": texts})
    return refine_outputs["output_text"]
