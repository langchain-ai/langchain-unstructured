import os
from pathlib import Path

import pytest

from langchain_unstructured.parsers import UnstructuredWordDocumentParser

from langchain_core.documents.base import Blob

EXAMPLE_DIRECTORY = file_path = Path(__file__).parent.parent.parent / "examples"


def test_unstructured_word_parser() -> None:
    """Test unstructured loader."""
    file_path = os.path.join(EXAMPLE_DIRECTORY, "README.docx")
    blob = Blob.from_path(file_path)

    parser = UnstructuredWordDocumentParser()
    docs = list(parser.lazy_parse(blob))

    assert len(docs) == 1

@pytest.mark.skipif(
    not os.environ.get("UNSTRUCTURED_API_KEY"), reason="Unstructured API key not found"
)
def test_unstructured_excel_parser_via_api() -> None:
    """Test unstructured loader."""
    file_path = os.path.join(EXAMPLE_DIRECTORY, "README.docx")
    blob = Blob.from_path(file_path)

    parser = UnstructuredWordDocumentParser(
        partition_via_api=True
    )
    docs = list(parser.lazy_parse(blob))

    assert len(docs) == 1