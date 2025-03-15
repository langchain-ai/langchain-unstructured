import os
from pathlib import Path
from typing import Callable, List

import pytest
from langchain_core.documents import Document

from langchain_unstructured import UnstructuredLoader, UnstructuredPDFLoader

EXAMPLE_DOCS_DIRECTORY = Path(__file__).parent.parent.parent / "example_docs/"
UNSTRUCTURED_API_KEY = os.getenv("UNSTRUCTURED_API_KEY")


def test_unstructured_pdf_loader_elements_mode() -> None:
    """Test unstructured loader with various modes."""
    file_path = EXAMPLE_DOCS_DIRECTORY / "hello.pdf"
    loader = UnstructuredPDFLoader(file_path, mode="elements")
    docs = loader.load()

    assert len(docs) == 2


def test_unstructured_pdf_loader_page_mode() -> None:
    """Test unstructured loader with various modes."""
    file_path = EXAMPLE_DOCS_DIRECTORY / "layout-parser-paper.pdf"
    loader = UnstructuredPDFLoader(file_path, mode="page")
    docs = loader.load()

    assert len(docs) == 16


def test_unstructured_pdf_loader_default_mode() -> None:
    """Test unstructured loader."""
    file_path = EXAMPLE_DOCS_DIRECTORY / "hello.pdf"
    loader = UnstructuredPDFLoader(file_path)
    docs = loader.load()

    assert len(docs) == 1


def _check_docs_content(docs: List[Document]) -> None:
    assert all(
        doc.metadata.get("filename") == "layout-parser-paper.pdf" for doc in docs
    )
    assert (
        sum(doc.metadata.get("category") == "PageBreak" for doc in docs) == 16
    )  # 16 page doc

    expected_metadata_keys = [
        "source",
        "languages",
        "page_number",
        "category",
        "coordinates",
        "element_id",
    ]
    for doc in docs:
        if doc.page_content:
            for key in expected_metadata_keys:
                assert key in doc.metadata
        else:
            assert doc.metadata.get("category") == "PageBreak"

    page_numbers = [
        doc.metadata.get("page_number")
        for doc in docs
        if doc.metadata.get("page_number")
    ]

    assert set(page_numbers) == set(range(1, 17))
    assert len(docs) >= 32  # (16 pages * (>=1 element per page) + 16 page breaks)

    page_1_content = ""
    for doc in docs:
        if doc.metadata.get("page_number") == 1:
            page_1_content += f" {doc.page_content}"
    assert (
        "LayoutParser: A Uniﬁed Toolkit for Deep Learning "
        "Based Document Image Analysis"
    ) in page_1_content

    categories = {doc.metadata.get("category") for doc in docs}
    assert "NarrativeText" in categories
    assert "Title" in categories


# -- Local partition --


@pytest.mark.local
def test_loader_partitions_locally() -> None:
    file_path = EXAMPLE_DOCS_DIRECTORY / "layout-parser-paper.pdf"

    docs = UnstructuredLoader(
        file_path=file_path,
        # Unstructured kwargs
        strategy="fast",
        include_page_breaks=True,
    ).load()

    _check_docs_content(docs)


@pytest.mark.local
async def test_loader_partitions_locally_async_lazy() -> None:
    file_path = EXAMPLE_DOCS_DIRECTORY / "layout-parser-paper.pdf"

    loader = UnstructuredLoader(
        file_path=file_path,
        # Unstructured kwargs
        strategy="fast",
        include_page_breaks=True,
    )
    docs = [doc async for doc in loader.alazy_load()]

    _check_docs_content(docs)


@pytest.mark.local
def test_loader_partition_ignores_invalid_arg() -> None:
    file_path = EXAMPLE_DOCS_DIRECTORY / "layout-parser-paper.pdf"

    docs = UnstructuredLoader(
        file_path=file_path,
        # Unstructured kwargs
        strategy="fast",
        # mode is no longer a valid argument and is ignored when partitioning locally
        mode="single",
    ).load()

    assert len(docs) > 1
    assert all(
        doc.metadata.get("filename") == "layout-parser-paper.pdf" for doc in docs
    )


@pytest.mark.local
def test_loader_partitions_locally_and_applies_post_processors(
    get_post_processor: Callable[[str], str],
) -> None:
    file_path = EXAMPLE_DOCS_DIRECTORY / "layout-parser-paper.pdf"
    loader = UnstructuredLoader(
        file_path=file_path,
        post_processors=[get_post_processor],
        strategy="fast",
    )

    docs = loader.load()

    assert len(docs) > 1
    assert docs[0].page_content.endswith("THE END!")


@pytest.mark.local
def test_url_loader() -> None:
    docs = UnstructuredLoader(web_url="https://www.example.com/").load()

    for doc in docs:
        assert doc.page_content
        assert doc.metadata["filetype"] == "text/html"
        assert doc.metadata["url"] == "https://www.example.com/"
        assert doc.metadata["category"]


# -- API partition --


@pytest.mark.skipif(
    not os.environ.get("UNSTRUCTURED_API_KEY"), reason="Unstructured API key not found"
)
def test_loader_partitions_via_api() -> None:
    file_path = EXAMPLE_DOCS_DIRECTORY / "layout-parser-paper.pdf"
    loader = UnstructuredLoader(
        file_path=file_path,
        partition_via_api=True,
        # Unstructured kwargs
        strategy="fast",
        include_page_breaks=True,
        coordinates=True,
    )

    docs = loader.load()

    _check_docs_content(docs)


@pytest.mark.skipif(
    not os.environ.get("UNSTRUCTURED_API_KEY"), reason="Unstructured API key not found"
)
async def test_loader_partitions_via_api_async_lazy() -> None:
    file_path = EXAMPLE_DOCS_DIRECTORY / "layout-parser-paper.pdf"
    loader = UnstructuredLoader(
        file_path=file_path,
        partition_via_api=True,
        # Unstructured kwargs
        strategy="fast",
        include_page_breaks=True,
        coordinates=True,
    )

    docs = [doc async for doc in loader.alazy_load()]

    _check_docs_content(docs)


@pytest.mark.skipif(
    not os.environ.get("UNSTRUCTURED_API_KEY"), reason="Unstructured API key not found"
)
def test_loader_partitions_multiple_via_api() -> None:
    file_paths = [
        EXAMPLE_DOCS_DIRECTORY / "layout-parser-paper.pdf",
        EXAMPLE_DOCS_DIRECTORY / "fake-email-attachment.eml",
    ]
    loader = UnstructuredLoader(
        file_path=file_paths,
        api_key=UNSTRUCTURED_API_KEY,
        partition_via_api=True,
        # Unstructured kwargs
        strategy="fast",
    )

    docs = loader.load()

    assert len(docs) > 1
    assert docs[0].metadata.get("filename") == "layout-parser-paper.pdf"
    assert docs[-1].metadata.get("filename") == "fake-email-attachment.eml"


@pytest.mark.skipif(
    not os.environ.get("UNSTRUCTURED_API_KEY"), reason="Unstructured API key not found"
)
def test_loader_pdf_partitions_multiple_via_api() -> None:
    file_path = EXAMPLE_DOCS_DIRECTORY / "layout-parser-paper.pdf"
    loader = UnstructuredPDFLoader(
        file_path=file_path,
        api_key=UNSTRUCTURED_API_KEY,
        partition_via_api=True,
        mode="elements",
        # Unstructured kwargs
        strategy="fast",
    )

    docs = loader.load()

    assert len(docs) > 1
    assert docs[0].metadata.get("filename") == "layout-parser-paper.pdf"


@pytest.mark.skipif(
    not os.environ.get("UNSTRUCTURED_API_KEY"), reason="Unstructured API key not found"
)
def test_loader_partitions_via_api_hi_res() -> None:
    file_path = EXAMPLE_DOCS_DIRECTORY / "layout-parser-paper.pdf"
    loader = UnstructuredLoader(
        file_path=file_path,
        partition_via_api=True,
        # Unstructured kwargs
        strategy="hi_res",
    )

    docs = loader.load()

    categories = {doc.metadata.get("category") for doc in docs}
    assert "Table" in categories
    assert "Image" in categories


# -- fixtures ---


@pytest.fixture()
def get_post_processor() -> Callable[[str], str]:
    def append_the_end(text: str) -> str:
        return text + "THE END!"

    return append_the_end
