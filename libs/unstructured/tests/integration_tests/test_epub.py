import os
from pathlib import Path

from langchain_unstructured import UnstructuredEPubLoader

EXAMPLE_DIRECTORY = file_path = Path(__file__).parent.parent / "examples"


def test_unstructured_epub_loader() -> None:
    """Test unstructured loader."""
    file_path = os.path.join(EXAMPLE_DIRECTORY, "epub30-spec.epub")
    loader = UnstructuredEPubLoader(str(file_path))
    docs = loader.load()

    assert len(docs) == 1

