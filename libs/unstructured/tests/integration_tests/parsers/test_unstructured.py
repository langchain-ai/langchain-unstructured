import os
from pathlib import Path

import pytest

from langchain_unstructured.parsers import UnstructuredParser

from langchain_core.documents.base import Blob

EXAMPLE_DIRECTORY = Path(__file__).parent.parent.parent / "examples"


# TODO: lecture depuis file et non file_path
def test_unstructured_parser() -> None:
    """Test unstructured loader."""
    file_path = os.path.join(EXAMPLE_DIRECTORY, "image.png")
    blob = Blob.from_path(file_path)

    parser = UnstructuredParser()
    docs = list(parser.lazy_parse(blob))

    assert len(docs) == 1  # FIXME: texte pas bon

    # TODO: test avec blob sans fichier (partout)

@pytest.mark.skipif(
    not os.environ.get("UNSTRUCTURED_API_KEY"), reason="Unstructured API key not found"
)
def test_unstructured_parser_via_api() -> None:
    """Test unstructured loader."""
    file_path = os.path.join(EXAMPLE_DIRECTORY, "image.png")
    blob = Blob.from_path(file_path)

    parser = UnstructuredParser(
        partition_via_api=True
    )
    docs = list(parser.lazy_parse(blob))

    assert len(docs) == 1