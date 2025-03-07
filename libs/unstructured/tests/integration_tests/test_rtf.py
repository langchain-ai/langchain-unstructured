import os
from pathlib import Path

from langchain_unstructured import UnstructuredRTFLoader

EXAMPLE_DIRECTORY = file_path = Path(__file__).parent.parent / "examples"


def test_unstructured_rtf_loader() -> None:
    """Test unstructured loader."""
    file_path = os.path.join(EXAMPLE_DIRECTORY, "fake.rtf")
    loader = UnstructuredRTFLoader(str(file_path))
    docs = loader.load()

    assert len(docs) == 1
