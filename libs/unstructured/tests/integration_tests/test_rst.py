import os
from pathlib import Path

from langchain_unstructured import UnstructuredRSTLoader

EXAMPLE_DIRECTORY = Path(__file__).parent.parent / "examples"


def test_unstructured_rst_loader() -> None:
    """Test unstructured loader."""
    file_path = EXAMPLE_DIRECTORY / "README.rst"
    loader = UnstructuredRSTLoader(file_path)
    docs = loader.load()

    assert len(docs) == 1
