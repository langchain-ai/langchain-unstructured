import os
from pathlib import Path

from langchain_unstructured import UnstructuredRTFLoader

EXAMPLE_DIRECTORY = Path(__file__).parent.parent / "examples"


def test_unstructured_rtf_loader() -> None:
    """Test unstructured loader."""
    file_path = EXAMPLE_DIRECTORY / "fake.rtf"
    loader = UnstructuredRTFLoader(file_path)
    docs = loader.load()

    assert len(docs) == 1
