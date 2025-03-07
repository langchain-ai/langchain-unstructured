import os
from pathlib import Path

from langchain_unstructured.image import UnstructuredImageLoader

EXAMPLE_DIRECTORY = file_path = Path(__file__).parent.parent / "examples"


def test_unstructured_image_loader() -> None:
    """Test unstructured loader."""
    file_path = os.path.join(EXAMPLE_DIRECTORY, "image.png")
    loader = UnstructuredImageLoader(str(file_path))
    docs = loader.load()

    assert len(docs) == 1
