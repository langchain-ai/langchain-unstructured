import os
from pathlib import Path

from langchain_unstructured import UnstructuredPowerPointLoader

EXAMPLE_DIRECTORY = Path(__file__).parent.parent / "examples"


def test_unstructured_powerpoint_loader() -> None:
    """Test unstructured loader."""
    file_path = EXAMPLE_DIRECTORY / "README.pptx"
    loader = UnstructuredPowerPointLoader(file_path)
    docs = loader.load()

    assert len(docs) == 1
