from typing import Any

from langchain_community.document_loaders.unstructured import (
    validate_unstructured_version,
)
from langchain_core.documents.base import Blob

from langchain_unstructured.parsers.core import \
    _UnstructuredDocumentParseur


class UnstructuredHTMLParser(_UnstructuredDocumentParseur):
    """Parse `CSV` files using `Unstructured`.

    Like other
    Unstructured parsers, UnstructuredCSVParser can be used in both
    "single" and "elements" mode. If you use the loader in "elements"
    mode, the CSV file will be a single Unstructured Table element.
    If you use the loader in "elements" mode, an HTML representation
    of the table will be available in the "text_as_html" key in the
    document metadata.

    Examples
    --------
    from langchain_unstructured.parsers.csv import UnstructuredCSVParser

    blob = Blob.from_path("stanley-cups.csv", mode="elements")

    parser = UnstructuredCSVParser()
    docs = list(parser.lazy_parse(blob))
    """

    def __init__(
        self, **unstructured_kwargs: Any
    ):
        """

        Args:
            file_path: The path to the CSV file.
            mode: The mode to use when loading the CSV file.
              Optional. Defaults to "single".
            **unstructured_kwargs: Keyword arguments to pass to unstructured.
        """
        validate_unstructured_version(min_unstructured_version="0.6.8")
        super().__init__(**unstructured_kwargs)

    def _get_elements_via_local(self, blob:Blob) -> list:
        try:
            from unstructured.partition.html import partition_html  # type: ignore
        except ImportError:
            raise ImportError(
                "unstructured package not found, please install it with "
                "`pip install 'langchain_unstructured[csv]'`"
            )

        if blob.data is None and blob.path:
            return partition_html(
                filename=blob.path,
                **self.unstructured_kwargs
            )
        else:
            return partition_html(
                file=blob.as_bytes_io(),
                **self.unstructured_kwargs
            )
