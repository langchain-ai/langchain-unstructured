"""Loader that uses unstructured to load files."""
from abc import ABC
from pathlib import Path
from typing import Any, Iterator, Optional, Callable, \
    Literal, TYPE_CHECKING, Union, List, IO

from langchain_community.document_loaders.blob_loaders import Blob
from langchain_community.document_loaders.unstructured import (
    validate_unstructured_version,
)
from langchain_core.document_loaders.base import BaseLoader, BaseBlobParser
from langchain_core.documents import Document

from langchain_unstructured.parsers.unstructured import UnstructuredParser

if TYPE_CHECKING:
    from unstructured_client import UnstructuredClient
else:
    UnstructuredClient = Any

class _UnstructuredBaseLoader(BaseLoader, ABC):
    """Base Loader that uses `Unstructured`."""

    def __init__(
            self,
            parser: BaseBlobParser,
            file_path: Union[str, List[str], Path, List[Path]],
            file: Optional[IO[bytes] | list[IO[bytes]]] = None,

    ):
        if file_path is not None and file is not None:
            raise ValueError("file_path and file cannot be defined simultaneously.")
        self.parser = parser
        self.file_path = file_path
        self.file = file

    def lazy_load(self) -> Iterator[Document]:
        if self.file:
            blob = Blob.from_data(self.file.read())
        else:
            blob = Blob.from_path(self.file_path)
        return self._parse_blob(blob)

    def _parse_blob(self, blob: Blob) -> Iterator[Document]:
        yield from self.parser.lazy_parse(blob)


class UnstructuredLoader(_UnstructuredBaseLoader):
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
            file_path: Optional[str | Path | list[str] | list[Path]] = None,
            *,
            file: Optional[IO[bytes] | list[IO[bytes]]] = None,
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
            parser=UnstructuredParser(
                partition_via_api=partition_via_api,
                post_processors=post_processors,
                mode=mode,
                api_key=api_key,
                client=client,
                url=url,
                web_url=web_url,
                **unstructured_kwargs
            ),
            file_path=file_path,
            file=file)

    def _parse_blob(self, blob: Blob) -> Iterator[Document]:
        """
        Lazy load given path as pages.
        Insert image, if possible, between two paragraphs.
        In this way, a paragraph can be continued on the next page.
        """
        yield from self.parser.lazy_parse(blob)
