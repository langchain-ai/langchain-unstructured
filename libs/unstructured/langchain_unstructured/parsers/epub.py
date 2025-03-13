from typing import Any

from langchain_community.document_loaders.unstructured import (
    validate_unstructured_version,
)
from langchain_core.documents.base import Blob

from langchain_unstructured.parsers.core import \
    _UnstructuredDocumentParseur


class UnstructuredEPubParser(_UnstructuredDocumentParseur):
    """Parse `Markdown` files using `Unstructured`.

    Like other
    Unstructured parsers, UnstructuredMarkdownParser can be used in both
    "single" and "elements" mode.

    Examples
    --------
    from langchain_unstructured.parsers.markdown import UnstructuredMarkdownParser

    blob = Blob.from_path("README.md", mode="elements")

    parser = UnstructuredMarkdwonParser()
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
            from unstructured.partition.epub import partition_epub  # type: ignore
        except ImportError:
            raise ImportError(
                "unstructured package not found, please install it with "
                "`pip install 'langchain_unstructured[epub]'`"
            )

        if blob.data is None and blob.path:
            filename = str(blob.path)
            file = None
        else:
            filename = None
            file = blob.as_bytes_io()
        return partition_epub(
            filename=filename,
            file=file,
            **self.unstructured_kwargs
        )
