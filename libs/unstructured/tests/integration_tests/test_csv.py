import os
from pathlib import Path

from langchain_core.documents.base import Blob
from langchain_unstructured import UnstructuredCSVLoader

EXAMPLE_DIRECTORY = Path(__file__).parent.parent / "examples"


def test_unstructured_csv_loader() -> None:
    """Test unstructured loader."""
    file_path = EXAMPLE_DIRECTORY / "stanley-cups.csv"
    loader = UnstructuredCSVLoader(file_path)
    docs = loader.load()

    assert len(docs) == 1

