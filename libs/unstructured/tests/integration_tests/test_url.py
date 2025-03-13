import pytest

from langchain_unstructured import UnstructuredURLLoader


def test_unstructured_url_loader() -> None:
    """Test unstructured loader."""
    loader = UnstructuredURLLoader(
        urls=[
            "https://docs.unstructured.io/",
            "http://www.google.com/",
        ],
    )
    docs = loader.load()
    assert len(docs) == 2


def test_continue_on_failure_true() -> None:
    """Test exception is not raised when continue_on_failure=True."""
    loader = UnstructuredURLLoader(["badurl.foobar"])
    docs = loader.load()
    assert len(docs) == 0


def test_continue_on_failure_false() -> None:
    """Test exception is raised when continue_on_failure=False."""
    loader = UnstructuredURLLoader(["badurl.foobar"], continue_on_failure=False)
    with pytest.raises(Exception):
        loader.load()
