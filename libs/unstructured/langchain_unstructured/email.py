from pathlib import PurePath
from typing import Any, Iterator, Optional, Callable, \
    Literal, TYPE_CHECKING, Union

from langchain_community.document_loaders.blob_loaders import Blob
from langchain_community.document_loaders.unstructured import (
    validate_unstructured_version,
)
from langchain_core.documents import Document

from langchain_unstructured.parsers.email import UnstructuredEmailParser
from langchain_unstructured.unstructured import _UnstructuredBaseLoader

if TYPE_CHECKING:
    from unstructured_client import UnstructuredClient
else:
    UnstructuredClient = Any


class UnstructuredEmailLoader(_UnstructuredBaseLoader):
    """Load email files using `Unstructured`.

    Works with both
    .eml and .msg files. You can process attachments in addition to the
    e-mail message itself by passing process_attachments=True into the
    constructor for the loader. By default, attachments will be processed
    with the unstructured partition function. If you already know the document
    types of the attachments, you can specify another partitioning function
    with the attachment partitioner kwarg.

    Example
    -------
    from langchain_community.document_loaders import UnstructuredEmailLoader

    loader = UnstructuredEmailLoader("example_data/fake-email.eml", mode="elements")
    loader.load()

    Example
    -------
    from langchain_community.document_loaders import UnstructuredEmailLoader

    loader = UnstructuredEmailLoader(
        "example_data/fake-email-attachment.eml",
        mode="elements",
        process_attachments=True,
    )
    loader.load()
    """

    def __init__(
            self,
            file_path: Union[str, PurePath],
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
            parser=UnstructuredEmailParser(
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
        if not blob.mimetype:
            from unstructured.file_utils.filetype import detect_filetype
            blob = Blob(
                id=blob.id,
                metadata=blob.metadata,
                data=blob.data,
                encoding=blob.encoding,
                mimetype=detect_filetype(file_path=self.file_path).mime_type,
                path=blob.path,

            )
        yield from self.parser.lazy_parse(blob)
