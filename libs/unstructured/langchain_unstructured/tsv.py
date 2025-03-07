"""Loads rich text files."""
from langchain_unstructured.parsers.tsv import UnstructuredTSVParser

"""Loads RST files."""

"""Loads Microsoft Excel files."""

from typing import Any, Iterator, Optional, Callable, \
    Literal, TYPE_CHECKING

from langchain_community.document_loaders.blob_loaders import Blob
from langchain_community.document_loaders.unstructured import (
    validate_unstructured_version,
)
from langchain_core.documents import Document

from langchain_unstructured.unstructured import _UnstructuredBaseLoader

if TYPE_CHECKING:
    from unstructured_client import UnstructuredClient
else:
    UnstructuredClient = Any


class UnstructuredTSVLoader(_UnstructuredBaseLoader):
    """Load `TSV` files using `Unstructured`.

    Like other
    Unstructured loaders, UnstructuredTSVLoader can be used in both
    "single" and "elements" mode. If you use the loader in "elements"
    mode, the TSV file will be a single Unstructured Table element.
    If you use the loader in "elements" mode, an HTML representation
    of the table will be available in the "text_as_html" key in the
    document metadata.

    Examples
    --------
    from langchain_community.document_loaders.tsv import UnstructuredTSVLoader

    loader = UnstructuredTSVLoader("stanley-cups.tsv", mode="elements")
    docs = loader.load()
    """

    def __init__(
            self,
            file_path: str,
            *,
            partition_via_api: bool = False,
            post_processors: Optional[list[Callable[[str], str]]] = None,
            mode: Literal["elements", "single", "paged"] = "single",
            # SDK parameters
            api_key: Optional[str] = None,
            client: Optional[UnstructuredClient] = None,
            url: Optional[str] = None,
            web_url: Optional[str] = None,
            **unstructured_kwargs: Any,
    ):
        """

        Args:
            file_path: The path to the CSV file.
            mode: The mode to use when loading the CSV file.
              Optional. Defaults to "single".
            **unstructured_kwargs: Keyword arguments to pass to unstructured.
        """
        validate_unstructured_version(min_unstructured_version="0.6.8")
        super().__init__(
            parser=UnstructuredTSVParser(
                partition_via_api=partition_via_api,
                post_processors=post_processors,
                mode=mode,
                api_key=api_key,
                client=client,
                url=url,
                web_url=web_url,
                **unstructured_kwargs
            ),
            file_path=file_path)

    def lazy_load(
            self,
    ) -> Iterator[Document]:
        """
        Lazy load given path as pages.
        Insert image, if possible, between two paragraphs.
        In this way, a paragraph can be continued on the next page.
        """
        blob = Blob.from_path(self.file_path)  # type: ignore[attr-defined]
        yield from self.parser.lazy_parse(blob)
