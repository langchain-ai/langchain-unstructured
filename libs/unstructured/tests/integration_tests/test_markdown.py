import os
from pathlib import Path

from langchain_unstructured import UnstructuredMarkdownLoader

EXAMPLE_DIRECTORY = Path(__file__).parent.parent / "examples"


def test_unstructured_markdown_loader() -> None:
    """Test unstructured loader."""
    file_path = EXAMPLE_DIRECTORY / "README.md"
    loader = UnstructuredMarkdownLoader(file_path)
    docs = loader.load()

    assert len(docs) == 1
