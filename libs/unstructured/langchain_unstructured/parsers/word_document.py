from typing import Any

from langchain_community.document_loaders.unstructured import (
    validate_unstructured_version,
)
from langchain_core.documents.base import Blob

from langchain_unstructured.parsers.core import \
    _UnstructuredDocumentParseur

# FIXME
from typing import Iterator

from langchain_core.documents import Document

from langchain_community.document_loaders.base import BaseBlobParser
from langchain_community.document_loaders.blob_loaders import Blob


class MsWordParser(BaseBlobParser):
    """Parse the Microsoft Word documents from a blob."""

    def lazy_parse(self, blob: Blob) -> Iterator[Document]:  # type: ignore[valid-type]
        """Parse a Microsoft Word document into the Document iterator.

        Args:
            blob: The blob to parse.

        Returns: An iterator of Documents.

        """
        try:
            from unstructured.partition.doc import partition_doc
            from unstructured.partition.docx import partition_docx
            from unstructured.file_utils.filetype import FileType, detect_filetype
        except ImportError as e:
            raise ImportError(
                "Could not import unstructured, please install with `pip install "
                "unstructured`."
            ) from e

        if blob.mimetype not in (
                "application/msword",
                "application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document"
        ):
            raise ValueError("This blob type is not supported for this parser.")
        with blob.as_bytes_io() as word_document:  # type: ignore[attr-defined]
            elements = mime_type_parser[blob.mimetype](file=word_document)  # type: ignore[attr-defined]  # type: ignore[operator]  # type: ignore[operator]  # type: ignore[operator]  # type: ignore[operator]  # type: ignore[operator]  # type: ignore[operator]
            text = "\n\n".join([str(el) for el in elements])
            metadata = {"source": blob.source}  # type: ignore[attr-defined]
            yield Document(page_content=text, metadata=metadata)

class UnstructuredWordDocumentParser(_UnstructuredDocumentParseur):
    """Parse `Excel` files using `Unstructured`.

    Like other
    Unstructured parsers, UnstructuredExcelParser can be used in both
    "single" and "elements" mode. If you use the loader in "elements"
    mode, the CSV file will be a single Unstructured Table element.
    If you use the loader in "elements" mode, an HTML representation
    of the table will be available in the "text_as_html" key in the
    document metadata.

    Examples
    --------
    from langchain_unstructured.parsers.excel import UnstructuredExcelParser

    blob = Blob.from_path("stanley-cups.xlsx", mode="elements")

    parser = UnstructuredExcelParser()
    docs = list(parser.lazy_parse(blob))
    """

    def __init__(
        self, **unstructured_kwargs: Any
    ):
        """

        Args:
            **unstructured_kwargs: Keyword arguments to pass to unstructured.
        """
        validate_unstructured_version(min_unstructured_version="0.6.8")
        super().__init__(**unstructured_kwargs)

    def _get_elements_via_local(self, blob:Blob) -> list:
        try:
            from unstructured.partition.docx import partition_docx  # type: ignore
            from unstructured.partition.doc import partition_doc  # type: ignore
        except ImportError:
            raise ImportError(
                "unstructured package not found, please install it with "
                "`pip install 'langchain_unstructured[docx]'`"
            )

        mime_type_parser = {
            "application/msword": partition_doc,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (
                partition_docx
            ),
        }
        if blob.data is None and blob.path:
            filename = str(blob.path)
            file = None
        else:
            filename = None
            file = blob.as_bytes_io()
        return mime_type_parser[blob.mimetype](
            filename=filename,
            file=file,
            **self.unstructured_kwargs
        )
