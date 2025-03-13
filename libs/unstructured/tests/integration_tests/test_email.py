import os
from pathlib import Path

from langchain_unstructured import UnstructuredEmailLoader

EXAMPLE_DIRECTORY = Path(__file__).parent.parent / "examples"

def test_unstructured_email_loader_with_attachments() -> None:
    """Test unstructured loader."""
    file_path = EXAMPLE_DIRECTORY / "fake-email-attachment.eml"
    loader = UnstructuredEmailLoader(
        file_path,
        mode="elements",
        process_attachments=True
        )
    docs = loader.load()
    assert docs[-1].page_content == "Hey this is a fake attachment!"
    assert docs[-1].metadata["filename"] == "fake-attachment.txt"
    assert docs[-1].metadata["source"].endswith("fake-email-attachment.eml")

def test_unstructured_email_loader_without_attachments() -> None:
    """Test unstructured loader."""
    file_path = EXAMPLE_DIRECTORY / "hello.msg"
    loader = UnstructuredEmailLoader(
        file_path,
        mode="single",
        process_attachments=True
        )
    docs = loader.load()
    assert docs[-1].metadata["sent_from"] == ['Brian Zhou <brizhou@gmail.com>']
    assert docs[-1].metadata["sent_to"] == ['brianzhou@me.com', 'brizhou@gmail.com']
    assert docs[-1].metadata["subject"] == 'Test for TIF files'
