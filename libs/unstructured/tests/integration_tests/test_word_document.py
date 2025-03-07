import os
from pathlib import Path

from langchain_unstructured.word_document import UnstructuredWordDocumentLoader

EXAMPLE_DIRECTORY = file_path = Path(__file__).parent.parent / "examples"


def test_unstructured_word_loader() -> None:
    """Test unstructured loader."""
    file_path = os.path.join(EXAMPLE_DIRECTORY, "README.docx")
    loader = UnstructuredWordDocumentLoader(str(file_path))
    docs = loader.load()

    assert len(docs) == 1
