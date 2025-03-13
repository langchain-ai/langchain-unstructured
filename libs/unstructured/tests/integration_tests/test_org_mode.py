import os
from pathlib import Path

from langchain_unstructured import UnstructuredOrgModeLoader

EXAMPLE_DIRECTORY = Path(__file__).parent.parent / "examples"


def test_unstructured_org_mode_loader() -> None:
    """Test unstructured loader."""
    file_path = EXAMPLE_DIRECTORY / "README.org"
    loader = UnstructuredOrgModeLoader(file_path)
    docs = loader.load()

    assert len(docs) == 1
