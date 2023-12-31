from kor import extract_from_documents, from_pydantic, create_extraction_chain
from langchain.docstore.document import Document
from pydantic import BaseModel, Field, ConfigDict, field_validator
from collections.abc import Iterable

import re

# only relevant while running script for testing purposes
if __name__ == "__main__":
    import os
    import sys

    api_root = os.path.abspath(os.path.join(__file__, "../.."))
    sys.path.append(api_root)

from analyzers import utils


class EntityRelationSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    entity: str = Field(
        repr=True,
        description="The name of the origin of the relationship",
    )

    target: str = Field(
        repr=True,
        description="The name of the target of the relationship",
    )

    relationship: str = Field(
        repr=True,
        description="The description of the relationship",
    )

    @field_validator("entity")
    @classmethod
    def entity_must_be_defined(cls, v: str) -> str:
        assert v
        return v

    @field_validator("target")
    @classmethod
    def target_must_be_defined(cls, v: str) -> str:
        assert v
        return v

    @field_validator("relationship")
    @classmethod
    def relationship_must_be_defined(cls, v: str) -> str:
        assert v
        return v


async def extract_entity_relations(docs: list[Document]) -> list[EntityRelationSchema]:
    llm = utils.chat_llm()
    schema, extraction_validator = from_pydantic(
        EntityRelationSchema,
        description="Extract information about relationships between entities found in documents.",
        examples=[
            (
                "Born in Chicago in 1901, Disney developed an early interest in drawing.",
                {
                    "entity": "Disney",
                    "target": "1901",
                    "relationship": "Born in",
                },
            ),
            (
                "Born in Chicago in 1901, Disney developed an early interest in drawing.",
                {
                    "entity": "Disney",
                    "target": "drawing",
                    "relationship": "interest in",
                },
            ),
            (
                "In 1911, the Disneys moved to Kansas City, Missouri.[14] There, "
                "Disney attended the Benton Grammar School, where he met fellow-student Walter Pfeiffer, "
                "who came from a family of theatre fans and introduced him to the world of vaudeville and motion pictures.",
                {
                    "entity": "Disney",
                    "target": "Kansas City",
                    "relationship": "moved in 1911",
                },
            ),
            (
                "In 1911, the Disneys moved to Kansas City, Missouri.[14] There, "
                "Disney attended the Benton Grammar School, where he met fellow-student Walter Pfeiffer, "
                "who came from a family of theatre fans and introduced him to the world of vaudeville and motion pictures.",
                {
                    "entity": "Disney",
                    "target": "Benton Grammar School",
                    "relationship": "attended in 1911",
                },
            ),
            (
                "In 1911, the Disneys moved to Kansas City, Missouri.[14] There, "
                "Disney attended the Benton Grammar School, where he met fellow-student Walter Pfeiffer, "
                "who came from a family of theatre fans and introduced him to the world of vaudeville and motion pictures.",
                {
                    "entity": "Walter Pfeiffer",
                    "target": "Disney",
                    "relationship": "introduced motion pictures",
                },
            ),
            (
                "During the early to mid-1960s, Disney developed plans for a ski resort "
                "in Mineral King, a glacial valley in California's Sierra Nevada.",
                {
                    "entity": "Disney",
                    "target": "Mineral King",
                    "relationship": "developed plans for a ski resort",
                },
            ),
            (
                "During the early to mid-1960s, Disney developed plans for a ski resort "
                "in Mineral King, a glacial valley in California's Sierra Nevada.",
                {
                    "entity": "Mineral King",
                    "target": "Sierra Nevada",
                    "relationship": "glacial valley in",
                },
            ),
            (
                "During the early to mid-1960s, Disney developed plans for a ski resort "
                "in Mineral King, a glacial valley in California's Sierra Nevada.",
                {
                    "entity": "Sierra Nevada",
                    "target": "California",
                    "relationship": "in",
                },
            ),
        ],
        many=True,
    )

    chain = create_extraction_chain(
        llm,
        schema,
        encoder_or_encoder_class="csv",
        validator=extraction_validator,
        input_formatter="triple_quotes",
    )

    extraction_data = []

    document_extraction_results = await extract_from_documents(
        chain,
        docs,
        max_concurrency=5,
        use_uid=False,
        return_exceptions=True,
    )

    for result in document_extraction_results:
        if isinstance(result, Exception):
            print("Exception: " + str(result))
            continue
        extraction_data.extend(result["validated_data"])

    return list(filter_common_erroneous_relations(extraction_data))


# the same is seen on other properties when this output is generated
_INVALID_ENTITY_REGEX = re.compile(r"[\[\]*]+entity$")


def filter_common_erroneous_relations(
    relations: list[EntityRelationSchema],
) -> Iterable[EntityRelationSchema]:
    for relation in relations:
        if _INVALID_ENTITY_REGEX.match(relation.entity):
            continue
        yield relation


if __name__ == "__main__":
    from langchain.document_loaders import WikipediaLoader
    from langchain.text_splitter import TokenTextSplitter
    import asyncio

    docs = WikipediaLoader(query="Walt_Disney").load()
    text_splitter = TokenTextSplitter(chunk_size=2048, chunk_overlap=24)
    split_docs = text_splitter.split_documents(docs)

    entity_relations = asyncio.run(extract_entity_relations(docs))
    assert len(entity_relations)
    for entity in entity_relations:
        print(entity)
