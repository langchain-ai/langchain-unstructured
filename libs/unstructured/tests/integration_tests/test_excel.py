import os
from pathlib import Path

from langchain_unstructured import UnstructuredExcelLoader

EXAMPLE_DIRECTORY = file_path = Path(__file__).parent.parent / "examples"


def test_unstructured_excel_loader() -> None:
    """Test unstructured loader."""
    file_path = EXAMPLE_DIRECTORY / "stanley-cups.xlsx"
    loader = UnstructuredExcelLoader(file_path)
    docs = loader.load()

    assert len(docs) == 1
