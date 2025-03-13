import os
from pathlib import Path

from langchain_unstructured import UnstructuredEPubLoader

EXAMPLE_DIRECTORY = Path(__file__).parent.parent / "examples"


def test_unstructured_epub_loader() -> None:
    """Test unstructured loader."""
    file_path = EXAMPLE_DIRECTORY / "epub30-spec.epub"
    loader = UnstructuredEPubLoader(file_path)
    docs = loader.load()

    assert len(docs) == 1

