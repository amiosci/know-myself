import dataclasses
import json
import os
from langchain.docstore.document import Document
from typing import Any, Callable


def _generate_path_components(hash: str, component_length: int = 12) -> list[str]:
    components = []
    low_i = -2
    high_i = 0
    modifier = 2
    for i in range(max(component_length, 1)):
        low_i += modifier
        high_i += modifier
        components.append(hash[low_i:high_i])
    components.append(hash[high_i:])
    return components


def _save_content(content_file: str, content: str):
    with open(content_file, "w+") as c:
        c.write(content)


def _save_metadata(metadata_file: str, metadata: dict[str, Any]):
    with open(metadata_file, "w+") as c:
        c.write(json.dumps(metadata))


def _load_content(content_file: str) -> str:
    with open(content_file, "r") as c:
        return c.read()


def _load_metadata(metadata_file: str) -> dict[str, Any]:
    with open(metadata_file, "r") as m:
        return json.load(m)


def _files_with_prefix(base_dir: str, prefix: str) -> list[str]:
    if not os.path.exists(base_dir):
        return []
    return [name for name in os.listdir(base_dir) if name.startswith(prefix)]


@dataclasses.dataclass
class DiskStore:
    root_directory: str
    logging_func: Callable[[str], None] = print

    def has_document_content(self, hash: str) -> bool:
        hash_basedir, content_file_name = self._hash_pathspec(hash)
        prefix = f"{content_file_name}."
        content_files = _files_with_prefix(hash_basedir, prefix)
        self.logging_func(f"Document count {len(content_files)} for {hash}")

        return len(content_files) > 0

    def save_document_content(self, hash: str, documents: list[Document]):
        self.logging_func(f"Saving {hash}")
        content_file_directory, content_file_name = self._hash_pathspec(hash)

        os.makedirs(content_file_directory, exist_ok=True)
        for i, doc in enumerate(documents):
            content_part_filename = f"{content_file_name}.{i}"
            content_part_filepath = os.path.join(
                content_file_directory, content_part_filename
            )
            self.logging_func(
                f"Saving document {os.path.abspath(content_part_filepath)}"
            )
            _save_content(
                content_part_filepath,
                doc.page_content,
            )

            if doc.metadata:
                content_part_metadata_filename = f"{content_file_name}.{i}.meta"
                _save_metadata(
                    os.path.join(
                        content_file_directory, content_part_metadata_filename
                    ),
                    doc.metadata,
                )

    def restore_document_content(self, hash: str) -> list[Document]:
        hash_basedir, content_file_name = self._hash_pathspec(hash)
        prefix = f"{content_file_name}."
        content_files = _files_with_prefix(hash_basedir, prefix)
        # ensure documents are ordered correctly for downstream processing
        segments = list({x.split(".")[1] for x in content_files})
        self.logging_func(f"Loading {len(segments)} document segments for {hash}")

        return [self._load_document(hash, int(i)) for i in segments]

    def delete_document_content(self, hash: str):
        hash_basedir, content_file_name = self._hash_pathspec(hash)
        prefix = f"{content_file_name}."
        content_files = _files_with_prefix(hash_basedir, prefix)
        self.logging_func(f"Deleting {len(content_files)} document segments for {hash}")

        for content_file in content_files:
            os.remove(os.path.join(hash_basedir, content_file))

        # clean directory tree until populated parent
        os.removedirs(hash_basedir)

    def _hash_pathspec(self, hash: str) -> tuple[str, str]:
        hash_path_components = _generate_path_components(hash)
        content_filename = hash_path_components.pop(-1)
        return (
            os.path.join(self.root_directory, *hash_path_components),
            content_filename,
        )

    def _load_document(self, hash: str, segment: int) -> Document:
        store_basedir, content_file_name = self._hash_pathspec(hash)

        content_part_filename = f"{content_file_name}.{segment}"
        content_filepath = os.path.join(store_basedir, content_part_filename)
        content = _load_content(content_filepath)

        content_part_metadata_filename = f"{content_file_name}.{segment}.meta"
        metadata_filepath = os.path.join(store_basedir, content_part_metadata_filename)
        if os.path.exists(metadata_filepath):
            metadata = _load_metadata(metadata_filepath)
        else:
            metadata = {}

        return Document(page_content=content, metadata=metadata)


def default_store(**kwargs):
    root = os.environ.get("HOME", ".")
    return DiskStore(
        root_directory=kwargs.pop("root_directory", f"{root}/kms/docs"), **kwargs
    )


if __name__ == "__main__":
    # correct length of initial hash shcema
    hash = "1234567890123456" * 4
    docs = [
        Document(page_content="1234", metadata={}),
        Document(page_content="5678", metadata={"test": "1234"}),
    ]
    store = DiskStore(root_directory="root_path")
    store.save_document_content(
        hash,
        docs,
    )

    try:
        restored_docs = store.restore_document_content(hash)
        for i, doc in enumerate(docs):
            print(doc)
            assert docs[i] == doc
    finally:
        pass
        store.delete_document_content(hash)
