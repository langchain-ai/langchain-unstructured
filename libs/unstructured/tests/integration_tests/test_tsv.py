import os
from pathlib import Path

from langchain_unstructured import UnstructuredTSVLoader

EXAMPLE_DIRECTORY = Path(__file__).parent.parent / "examples"


def test_unstructured_tsv_loader() -> None:
    """Test unstructured loader."""
    file_path = EXAMPLE_DIRECTORY / "stanley-cups.tsv"
    loader = UnstructuredTSVLoader(file_path)
    docs = loader.load()

    assert len(docs) == 1
