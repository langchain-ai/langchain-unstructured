import os
from pathlib import Path

from langchain_unstructured import UnstructuredMarkdownLoader

EXAMPLE_DIRECTORY = file_path = Path(__file__).parent.parent / "examples"


def test_unstructured_markdown_loader() -> None:
    """Test unstructured loader."""
    file_path = os.path.join(EXAMPLE_DIRECTORY, "README.md")
    loader = UnstructuredMarkdownLoader(str(file_path))
    docs = loader.load()

    assert len(docs) == 1
