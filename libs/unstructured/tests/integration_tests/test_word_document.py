import os
from pathlib import Path

from langchain_unstructured.word_document import UnstructuredWordDocumentLoader

EXAMPLE_DIRECTORY = Path(__file__).parent.parent / "examples"


def test_unstructured_word_loader() -> None:
    """Test unstructured loader."""
    file_path = EXAMPLE_DIRECTORY / "README.docx"
    loader = UnstructuredWordDocumentLoader(file_path)
    docs = loader.load()

    assert len(docs) == 1

    file_path = EXAMPLE_DIRECTORY / "README.doc"
    loader = UnstructuredWordDocumentLoader(file_path)
    docs = loader.load()

    assert len(docs) == 1
