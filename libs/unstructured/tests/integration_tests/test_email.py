from pathlib import Path

from langchain_community.document_loaders import (
    UnstructuredEmailLoader,
)


def test_unstructured_email_loader_with_attachments() -> None:
    file_path = Path(__file__).parent.parent / "examples/fake-email-attachment.eml"
    loader = UnstructuredEmailLoader(
        str(file_path), mode="elements", process_attachments=True
    )
    docs = loader.load()

    assert docs[-1].page_content == "Hey this is a fake attachment!"
    assert docs[-1].metadata["filename"] == "fake-attachment.txt"
    assert docs[-1].metadata["source"].endswith("fake-email-attachment.eml")
