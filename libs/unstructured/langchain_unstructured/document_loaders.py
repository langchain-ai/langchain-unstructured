"""Unstructured document loader."""

from __future__ import annotations

import json
import logging
import os
import threading
from bs4 import BeautifulSoup
from langchain_community.document_loaders.blob_loaders import Blob
from langchain_community.document_loaders.parsers.images import (
    BaseImageBlobParser,
    RapidOCRBlobParser,
)
from langchain_community.document_loaders.parsers.pdf import (
    PDFMinerParser, _purge_metadata, _format_inner_image
)
from langchain_community.document_loaders.pdf import BasePDFLoader
from langchain_core.document_loaders.base import BaseLoader, BaseBlobParser
from langchain_core.documents import Document
from pathlib import Path, PurePath
from tempfile import TemporaryDirectory
from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    BinaryIO,
    Callable,
    Iterator,
    Literal,
    Optional,
    Union,
    cast,
)
from typing_extensions import TypeAlias

if TYPE_CHECKING:
    from unstructured_client import UnstructuredClient
    from unstructured_client.models import operations  # type:ignore[attr-defined]

Element: TypeAlias = Any

logger = logging.getLogger(__file__)

_DEFAULT_URL = "https://api.unstructuredapp.io/general/v0/general"


def _transform_cell_content(value: str, conversion_ind: bool = False) -> str:
    if value and conversion_ind is True:
        from markdownify import markdownify as md

        value = md(value)
    chars = {"|": "&#124;", "\n": "<br>"}
    for char, replacement in chars.items():
        value = value.replace(char, replacement)
    return value


def convert_table(
        html: str, content_conversion_ind: bool = False,
        all_cols_alignment: str = "left"
) -> str:
    alignment_options = {"left": " :--- ", "center": " :---: ", "right": " ---: "}
    if all_cols_alignment not in alignment_options.keys():
        raise ValueError(
            "Invalid alignment option for {!r} arg. " "Expected one of: {}".format(
                "all_cols_alignment", list(alignment_options.keys())
            )
        )

    soup = BeautifulSoup(html, "html.parser")

    if not soup.find():
        return html

    table = []
    table_headings = []
    table_body = []
    table_tr = soup.find_all("tr")

    try:
        table_headings = [
            " "
            + _transform_cell_content(
                th.renderContents().decode("utf-8"),
                conversion_ind=content_conversion_ind,
            )
            + " "
            for th in soup.find("tr").find_all("th")
        ]
    except AttributeError:
        raise ValueError("No {!r} tag found".format("tr"))

    if table_headings:
        table.append(table_headings)
        table_tr = table_tr[1:]

    for tr in table_tr:
        td_list = [
            " "
            + _transform_cell_content(
                td.renderContents().decode("utf-8"),
                conversion_ind=content_conversion_ind,
            )
            + " "
            for td in tr.find_all("td")
        ]
        table_body.append(td_list)

    table += table_body
    md_table_header = "|".join(
        [""]
        + ([" "] * len(table[0]) if not table_headings else table_headings)
        + ["\n"]
        + [alignment_options[all_cols_alignment]] * len(table[0])
        + ["\n"]
    )

    md_table = md_table_header + "".join(
        "|".join([""] + row + ["\n"]) for row in table_body
    )
    return md_table


class UnstructuredLoader(BaseLoader):
    """Unstructured document loader interface.

    Setup:
        Install ``langchain-unstructured`` and set environment variable ``UNSTRUCTURED_API_KEY``.

        .. code-block:: bash
            pip install -U langchain-unstructured
            export UNSTRUCTURED_API_KEY="your-api-key"

    Instantiate:
        .. code-block:: python
            from langchain_unstructured import UnstructuredLoader

            loader = UnstructuredLoader(
                file_path = ["example.pdf", "fake.pdf"],
                api_key=UNSTRUCTURED_API_KEY,
                partition_via_api=True,
                chunking_strategy="by_title",
                strategy="fast",
            )

    Lazy load:
        .. code-block:: python

            docs = []
            docs_lazy = loader.lazy_load()

            # async variant:
            # docs_lazy = await loader.alazy_load()

            for doc in docs_lazy:
                docs.append(doc)
            print(docs[0].page_content[:100])
            print(docs[0].metadata)

        .. code-block:: python

            1 2 0 2
            {'source': './example_data/layout-parser-paper.pdf', 'coordinates': {'points': ((16.34, 213.36), (16.34, 253.36), (36.34, 253.36), (36.34, 213.36)), 'system': 'PixelSpace', 'layout_width': 612, 'layout_height': 792}, 'file_directory': './example_data', 'filename': 'layout-parser-paper.pdf', 'languages': ['eng'], 'last_modified': '2024-07-25T21:28:58', 'page_number': 1, 'filetype': 'application/pdf', 'category': 'UncategorizedText', 'element_id': 'd3ce55f220dfb75891b4394a18bcb973'}


    Async load:
        .. code-block:: python

            docs = await loader.aload()
            print(docs[0].page_content[:100])
            print(docs[0].metadata)

        .. code-block:: python

            1 2 0 2
            {'source': './example_data/layout-parser-paper.pdf', 'coordinates': {'points': ((16.34, 213.36), (16.34, 253.36), (36.34, 253.36), (36.34, 213.36)), 'system': 'PixelSpace', 'layout_width': 612, 'layout_height': 792}, 'file_directory': './example_data', 'filename': 'layout-parser-paper.pdf', 'languages': ['eng'], 'last_modified': '2024-07-25T21:28:58', 'page_number': 1, 'filetype': 'application/pdf', 'category': 'UncategorizedText', 'element_id': 'd3ce55f220dfb75891b4394a18bcb973'}


    Load URL:
        .. code-block:: python

            loader = UnstructuredLoader(web_url="https://www.example.com/")
            print(docs[0])

        .. code-block:: none

            page_content='Example Domain' metadata={'category_depth': 0, 'languages': ['eng'], 'filetype': 'text/html', 'url': 'https://www.example.com/', 'category': 'Title', 'element_id': 'fdaa78d856f9d143aeeed85bf23f58f8'}

        .. code-block:: python

            print(docs[1])

        .. code-block:: none

            page_content='This domain is for use in illustrative examples in documents. You may use this domain in literature without prior coordination or asking for permission.' metadata={'languages': ['eng'], 'parent_id': 'fdaa78d856f9d143aeeed85bf23f58f8', 'filetype': 'text/html', 'url': 'https://www.example.com/', 'category': 'NarrativeText', 'element_id': '3652b8458b0688639f973fe36253c992'}


    References
    ----------
    https://docs.unstructured.io/api-reference/api-services/sdk
    https://docs.unstructured.io/api-reference/api-services/overview
    https://docs.unstructured.io/open-source/core-functionality/partitioning
    https://docs.unstructured.io/open-source/core-functionality/chunking
    """  # noqa: E501

    def __init__(
            self,
            file_path: Optional[str | Path | list[str] | list[Path]] = None,
            *,
            file: Optional[IO[bytes] | list[IO[bytes]]] = None,
            partition_via_api: bool = False,
            post_processors: Optional[list[Callable[[str], str]]] = None,
            # SDK parameters
            api_key: Optional[str] = None,
            client: Optional[UnstructuredClient] = None,
            url: Optional[str] = None,
            web_url: Optional[str] = None,
            **kwargs: Any,
    ):
        try:
            import unstructured_client
        except ImportError:
            raise ImportError(
                "unstructured package not found, please install it "
                "with `pip install 'unstructured-client'`"
            )
        if file_path is not None and file is not None:
            raise ValueError("file_path and file cannot be defined simultaneously.")
        if client is not None:
            disallowed_params = [("api_key", api_key), ("url", url)]
            bad_params = [
                param for param, value in disallowed_params if value is not None
            ]

            if bad_params:
                raise ValueError(
                    "if you are passing a custom `client`, you cannot also pass these "
                    f"params: {', '.join(bad_params)}."
                )

        unstructured_api_key = api_key or os.getenv("UNSTRUCTURED_API_KEY") or ""
        unstructured_url = url or os.getenv("UNSTRUCTURED_URL") or _DEFAULT_URL

        self.client = client or unstructured_client.UnstructuredClient(
            api_key_auth=unstructured_api_key, server_url=unstructured_url
        )

        self.file_path = file_path
        self.file = file
        self.partition_via_api = partition_via_api
        self.post_processors = post_processors
        self.unstructured_kwargs = kwargs
        if web_url:
            self.unstructured_kwargs["url"] = web_url

    def lazy_load(self) -> Iterator[Document]:
        """Load file(s) to the _UnstructuredBaseLoader."""

        def load_file(
                f: Optional[IO[bytes]] = None, f_path: Optional[str | Path] = None
        ) -> Iterator[Document]:
            """Load an individual file to the _UnstructuredBaseLoader."""
            return _SingleDocumentLoader(
                file=f,
                file_path=f_path,
                partition_via_api=self.partition_via_api,
                post_processors=self.post_processors,
                # SDK parameters
                client=self.client,
                **self.unstructured_kwargs,
            ).lazy_load()

        if isinstance(self.file, list):
            for f in self.file:
                yield from load_file(f=f)
            return

        if isinstance(self.file_path, list):
            for f_path in self.file_path:
                yield from load_file(f_path=f_path)
            return

        # Call _UnstructuredBaseLoader normally since file and file_path are not lists
        yield from load_file(f=self.file, f_path=self.file_path)


class _SingleDocumentLoader(BaseLoader):
    """Provides loader functionality for individual document/file objects.

    Encapsulates partitioning individual file objects (file or file_path) either
    locally or via the Unstructured API.
    """

    _lock = threading.Lock()

    def __init__(
            self,
            file_path: Optional[str | Path] = None,
            *,
            client: UnstructuredClient,
            file: Optional[IO[bytes]] = None,
            partition_via_api: bool = False,
            post_processors: Optional[list[Callable[[str], str]]] = None,
            password: Optional[str] = None,
            **kwargs: Any,
    ):
        """Initialize loader."""
        self.file_path = str(file_path) if isinstance(file_path, Path) else file_path
        self.file = file
        self.password = password
        self.partition_via_api = partition_via_api
        self.post_processors = post_processors
        # SDK parameters
        self.client = client
        self.unstructured_kwargs = kwargs

    def lazy_load(self) -> Iterator[Document]:
        """Load file."""
        with _SingleDocumentLoader._lock:
            elements_json = (
                self._post_process_elements_json(self._elements_json)
                if self.post_processors
                else self._elements_json
            )
            file_metadata = _purge_metadata(self._get_metadata())
            for element in elements_json:
                metadata = file_metadata.copy()
                element_metadata = element.get("metadata") or {}
                element_metadata.pop("filename", None)
                metadata.update(element_metadata)
                metadata.update(
                    {"category": element.get("category") or element.get("type")}
                )
                metadata.update({"element_id": element.get("element_id")})
                yield Document(
                    page_content=cast(str, element.get("text")), metadata=metadata
                )

    @property
    def _elements_json(self) -> list[dict[str, Any]]:
        """Get elements as a list of dictionaries from local partition or via API."""
        if self.partition_via_api:
            return self._elements_via_api

        return self._convert_elements_to_dicts(self._elements_via_local)

    @property
    def _elements_via_local(self) -> list[Element]:
        try:
            from unstructured.partition.auto import partition
        except ImportError:
            raise ImportError(
                "unstructured package not found, please install it with "
                "`pip install 'unstructured[pdf]'`"
            )

        if self.file and self.unstructured_kwargs.get("metadata_filename") is None:
            raise ValueError(
                "If partitioning a fileIO object, metadata_filename must be specified"
                " as well.",
            )

        return partition(
            file=self.file,
            filename=self.file_path,
            password=self.password,
            **self.unstructured_kwargs,
        )

    @property
    def _elements_via_api(self) -> list[dict[str, Any]]:
        """Retrieve a list of element dicts from the API using the SDK client."""
        client = self.client
        req = self._sdk_partition_request
        response = client.general.partition(request=req)
        if response.status_code == 200:
            return json.loads(response.raw_response.text)
        raise ValueError(
            f"Receive unexpected status code {response.status_code} from the API.",
        )

    @property
    def _file_content(self) -> bytes:
        """Get content from either file or file_path."""
        if self.file is not None:
            return self.file.read()
        elif self.file_path:
            with open(self.file_path, "rb") as f:
                return f.read()
        raise ValueError("file or file_path must be defined.")

    @property
    def _sdk_partition_request(self) -> operations.PartitionRequest:
        from unstructured_client.models import (  # type:ignore[attr-defined]
            operations,
            shared,
        )

        return operations.PartitionRequest(
            partition_parameters=shared.PartitionParameters(
                files=shared.Files(
                    content=self._file_content, file_name=str(self.file_path)
                ),
                **self.unstructured_kwargs,
            ),
        )

    def _convert_elements_to_dicts(
            self, elements: list[Element]
    ) -> list[dict[str, Any]]:
        return [element.to_dict() for element in elements]

    def _get_metadata(self) -> dict[str, Any]:
        """Get file_path metadata if available."""
        metadata = {}
        if self.file_path:
            metadata = {"source": self.file_path, "filename": Path(self.file_path).name}
        if self.file:
            metadata["source"] = self.file.name
            metadata["filename"] = self.file.name
        return metadata

    def _post_process_elements_json(
            self, elements_json: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Apply post processing functions to extracted unstructured elements.

        Post processing functions are str -> str callables passed
        in using the post_processors kwarg when the loader is instantiated.
        """
        if self.post_processors:
            for element in elements_json:
                for post_processor in self.post_processors:
                    element["text"] = post_processor(str(element.get("text")))
        return elements_json


# %% ---------------------- PDF
class _SinglePDFDocumentLoader(_SingleDocumentLoader):
    @property
    def _elements_via_local(self) -> list[Element]:
        try:
            from unstructured.partition.pdf import partition_pdf
        except ImportError:
            raise ImportError(
                "unstructured package not found, please install it with "
                "`pip install 'unstructured[pdf]'`"
            )

        if self.file and self.unstructured_kwargs.get("metadata_filename") is None:
            raise ValueError(
                "If partitioning a fileIO object, metadata_filename must be specified"
                " as well.",
            )

        return partition_pdf(
            file=self.file,
            filename=self.file_path,
            password=self.password,
            **self.unstructured_kwargs,
        )

    def _get_metadata(self) -> dict[str, Any]:
        from pdfminer.pdfpage import PDFDocument, PDFPage, PDFParser

        # Create a PDF parser object associated with the file object.
        if self.unstructured_kwargs.get("url"):
            return {"source": self.unstructured_kwargs.get("url")}
        with self.file or open(str(self.file_path), "rb") as file:
            parser = PDFParser(cast(BinaryIO, file))

            # Create a PDF document object that stores the document structure.
            doc = PDFDocument(parser, password=self.password or "")
            metadata: dict[str, Any] = (
                {"source": self.file_path} if self.file_path else {}
            )
            if self.file and self.file.name:
                metadata["filename"] = Path(self.file.name).name

            for info in doc.info:
                metadata.update(info)
            for k, v in metadata.items():
                try:
                    metadata[k] = PDFMinerParser.resolve_and_decode(v)
                except Exception as e:  # pragma: nocover
                    # This metadata value could not be parsed. Instead of failing
                    # the PDF read, treat it as a warning only if
                    # `strict_metadata=False`.
                    logger.warning(
                        '[WARNING] Metadata key "%s" could not be parsed due to '
                        "exception: %s",
                        k,
                        str(e),
                    )

            # Count number of pages.
            metadata["total_pages"] = len(list(PDFPage.create_pages(doc)))
            return metadata


class UnstructuredPDFParser(BaseBlobParser):
    """Unstructured document loader interface.

    Setup:
        Install ``langchain-unstructured`` and set environment
        variable ``UNSTRUCTURED_API_KEY``.

        .. code-block:: bash
            pip install -U langchain-unstructured
            export UNSTRUCTURED_API_KEY="your-api-key"

    Instantiate:
        .. code-block:: python
            from langchain_unstructured import UnstructuredPDFParser

            loader = UnstructuredPDFParser(
                file_path = "example.pdf",
                api_key=UNSTRUCTURED_API_KEY,
                partition_via_api=True,
                chunking_strategy="by_title",
                strategy="fast",
            )

    Lazy load:
        .. code-block:: python

            docs = []
            docs_lazy = loader.lazy_load()

            # async variant:
            # docs_lazy = await loader.alazy_load()

            for doc in docs_lazy:
                docs.append(doc)
            print(docs[0].page_content[:100])
            print(docs[0].metadata)

        .. code-block:: python

            1 2 0 2
            {'source': './example_data/layout-parser-paper.pdf',
            'coordinates':
            {'points': (
                (16.34, 213.36),
                (16.34, 253.36),
                (36.34, 253.36),
                (36.34, 213.36)),
            'system': 'PixelSpace',
            'layout_width': 612,
            'layout_height': 792},
            'file_directory': './example_data',
            'filename': 'layout-parser-paper.pdf',
            'languages': ['eng'],
            'last_modified': '2024-07-25T21:28:58',
            'page_number': 1,
            'filetype': 'application/pdf',
            'category': 'UncategorizedText',
            'element_id': 'd3ce55f220dfb75891b4394a18bcb973'}


    Async load:
        .. code-block:: python

            docs = await loader.aload()
            print(docs[0].page_content[:100])
            print(docs[0].metadata)

        .. code-block:: python

            1 2 0 2
            {'source': './example_data/layout-parser-paper.pdf',
            'coordinates': {
            'points': (
            (16.34, 213.36),
            (16.34, 253.36),
            (36.34, 253.36),
            (36.34, 213.36)),
            'system': 'PixelSpace',
            'layout_width': 612,
            'layout_height': 792},
            'file_directory': './example_data',
            'filename': 'layout-parser-paper.pdf',
            'languages': ['eng'],
            'last_modified': '2024-07-25T21:28:58',
            'page_number': 1,
            'filetype': 'application/pdf',
            'category': 'UncategorizedText',
            'element_id': 'd3ce55f220dfb75891b4394a18bcb973'}


    Load URL:
        .. code-block:: python

            loader = UnstructuredLoader(web_url="https://www.example.com/")
            print(docs[0])

        .. code-block:: none

            page_content='Example Domain'
                metadata={
                    'category_depth': 0,
                    'languages': ['eng'],
                    'filetype': 'text/html',
                    'url': 'https://www.example.com/',
                    'category': 'Title',
                    'element_id': 'fdaa78d856f9d143aeeed85bf23f58f8'}

        .. code-block:: python

            print(docs[1])

        .. code-block:: none

            page_content='This domain is for use in illustrative examples in documents.
            You may use this domain in literature without prior coordination or asking
            for permission.'
            metadata={
                'languages': ['eng'],
                'parent_id': 'fdaa78d856f9d143aeeed85bf23f58f8',
                'filetype': 'text/html',
                'url': 'https://www.example.com/',
                'category': 'NarrativeText',
                'element_id': '3652b8458b0688639f973fe36253c992'}

    """

    _warn_extract_tables = False

    def __init__(
            self,
            *,
            password: Optional[str] = None,
            mode: Literal["single", "page", "elements"] = "single",
            pages_delimitor: str = "\n\n",
            extract_images: bool = False,
            images_parser: Optional[BaseImageBlobParser] = None,
            images_inner_format: Literal["text", "markdown-img", "html-img"] = "text",
            extract_tables: Optional[Literal["csv", "markdown", "html"]] = None,
            partition_via_api: bool = False,
            post_processors: Optional[list[Callable[[str], str]]] = None,
            # SDK parameters
            api_key: Optional[str] = None,
            client: Optional[UnstructuredClient] = None,
            url: Optional[str] = None,
            web_url: Optional[str] = None,
            **unstructured_kwargs: Any,
    ) -> None:
        """Initialize the parser.

        Args:
        """
        try:
            import unstructured_client
        except ImportError:
            raise ImportError(
                "unstructured package not found, please install it "
                "with `pip install 'unstructured[pdf]'`"
            )
        if unstructured_kwargs.get("strategy") == "ocr_only" and extract_images:
            logger.warning("extract_images is not supported with strategy='ocr_only")
            extract_images = False
        if unstructured_kwargs.get("strategy") != "hi_res" and extract_tables:
            if not UnstructuredPDFParser._warn_extract_tables:
                UnstructuredPDFParser._warn_extract_tables = True
                logger.warning(
                    "extract_tables is not supported with strategy!='hi_res'"
                )
            extract_tables = None
        super().__init__()

        if client is not None:
            disallowed_params = [("api_key", api_key), ("url", url)]
            bad_params = [
                param for param, value in disallowed_params if value is not None
            ]

            if bad_params:
                raise ValueError(
                    "if you are passing a custom `client`, you cannot also pass these "
                    f"params: {', '.join(bad_params)}."
                )

        unstructured_api_key = api_key or os.getenv("UNSTRUCTURED_API_KEY") or ""
        unstructured_url = url or os.getenv("UNSTRUCTURED_URL") or _DEFAULT_URL
        self.client = client or unstructured_client.UnstructuredClient(
            api_key_auth=unstructured_api_key, server_url=unstructured_url
        )

        self.password = password
        _valid_modes = {"single", "elements", "paged", "page"}
        if mode not in _valid_modes:
            raise ValueError(
                f"Got {mode} for `mode`, but should be one of `{_valid_modes}`"
            )
        if mode == "paged":
            logger.warning("`paged` mode is depreceted. Use `page` mode")
            mode = "page"
        self.mode = mode
        self.pages_delimitor = pages_delimitor
        if extract_images and not images_parser:
            images_parser = RapidOCRBlobParser()
        if extract_images and unstructured_kwargs.get("strategy") == "fast":
            logger.warning("Change strategy to 'auto' to extract images")
            unstructured_kwargs["strategy"] = "auto"
        self.images_parser = images_parser
        self.images_inner_format = images_inner_format
        self.tmp_dir = None
        if extract_images:
            if partition_via_api:
                logger.warning("extract_images is not supported with partition_via_api")
            else:
                unstructured_kwargs["extract_images_in_pdf"] = True
                self.tmp_dir = TemporaryDirectory(ignore_cleanup_errors=True)
                if "extract_image_block_output_dir" not in unstructured_kwargs:
                    unstructured_kwargs["extract_image_block_output_dir"] = (
                        self.tmp_dir.name
                    )
        self.extract_tables = extract_tables
        self.partition_via_api = partition_via_api
        self.post_processors = post_processors
        self.unstructured_kwargs = unstructured_kwargs

        if web_url:
            self.unstructured_kwargs["url"] = web_url

    def lazy_parse(self, blob: Blob) -> Iterator[Document]:  # type: ignore[valid-type]
        """Lazily parse the blob."""
        unstructured_kwargs = self.unstructured_kwargs.copy()
        if not self.partition_via_api:
            unstructured_kwargs["metadata_filename"] = blob.path or blob.metadata.get(
                "source"
            )
        if self.extract_tables:
            unstructured_kwargs["infer_table_structure"] = True
        if self.mode != "elements":
            unstructured_kwargs["include_page_breaks"] = True
        page_number = 0
        path = Path(str(blob.source or blob.path))
        with blob.as_bytes_io() as pdf_file_obj:
            _single_doc_loader = _SinglePDFDocumentLoader(
                file=pdf_file_obj,
                password=self.password,
                partition_via_api=self.partition_via_api,
                post_processors=self.post_processors,
                # SDK parameters
                client=self.client,
                **unstructured_kwargs,
            )
            doc_metadata = _purge_metadata(
                _single_doc_loader._get_metadata()
                | {
                    "source": blob.source,
                    "file_directory": str(path.parent),
                    "filename": path.name,
                    "filetype": blob.mimetype,
                }
            )
        with blob.as_bytes_io() as pdf_file_obj:
            _single_doc_loader = _SinglePDFDocumentLoader(
                file=pdf_file_obj,
                password=self.password,
                partition_via_api=self.partition_via_api,
                post_processors=self.post_processors,
                # SDK parameters
                client=self.client,
                **unstructured_kwargs,
            )
            if self.mode == "elements":
                yield from _single_doc_loader.lazy_load()
            elif self.mode in ("page", "single"):
                page_content = []
                page_break = False
                for doc in _single_doc_loader.lazy_load():
                    if page_break:
                        page_content.append(self.pages_delimitor)
                        page_break = False

                    if doc.metadata.get("category") == "Image":
                        if "image_path" in doc.metadata:
                            blob = Blob.from_path(doc.metadata["image_path"])
                            image_text = next(
                                self.images_parser.lazy_parse(blob)  # type: ignore
                            ).page_content
                            if image_text:
                                page_content.append(
                                    _format_inner_image(blob, image_text,
                                                        self.images_inner_format)
                                )

                    elif doc.metadata.get("category") == "Table":
                        page_content.append(
                            self._convert_table(
                                doc.metadata.get("text_as_html"),
                            ),
                        )
                    elif doc.metadata.get("category") == "Title":
                        page_content.append("# " + doc.page_content)
                    elif doc.metadata.get("category") == "Header":
                        pass
                    elif doc.metadata.get("category") == "Footer":
                        pass
                    elif doc.metadata.get("category") == "PageBreak":
                        if self.mode in ("page", "paged"):
                            yield Document(
                                page_content="\n".join(page_content),
                                metadata=(doc_metadata | {"page": page_number}),
                            )
                            page_content.clear()
                            page_number += 1
                        else:
                            page_break = True
                    else:
                        # NarrativeText, UncategorizedText, Formula, FigureCaption,
                        # ListItem, Address, EmailAddress
                        if doc.metadata.get("category") not in [
                            "NarrativeText",
                            "UncategorizedText",
                            "Formula",
                            "FigureCaption",
                            "ListItem",
                            "Address",
                            "EmailAddress",
                        ]:
                            logger.warning(
                                "Unknown category %s", doc.metadata.get("category")
                            )
                        page_content.append(doc.page_content)
                if self.mode == "single":
                    yield Document(
                        page_content="\n".join(page_content),
                        metadata=doc_metadata,
                    )
                else:
                    if page_content:
                        yield Document(
                            page_content="\n".join(page_content),
                            metadata=doc_metadata | {"page": page_number},
                        )

    def _convert_table(self, html_table: Optional[str]) -> str:
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas package not found, please install it with `pip install pandas`"
            )
        if not self.extract_tables:
            return ""
        if not html_table:
            return ""
        if self.extract_tables == "html":
            return html_table
        elif self.extract_tables == "markdown":
            try:
                from markdownify import markdownify as md

                return md(html_table)
            except ImportError:
                raise ImportError(
                    "markdownify package not found, please install it with "
                    "`pip install markdownify`"
                )
        elif self.extract_tables == "csv":
            return pd.read_html(html_table)[0].to_csv()
        else:
            raise ValueError("extract_tables must be csv, markdown or html")


class UnstructuredPDFLoader(BasePDFLoader):
    def __init__(
            self,
            file_path: Union[str, PurePath],
            *,
            headers: Optional[dict] = None,
            mode: Literal["single", "page", "elements"] = "single",
            pages_delimitor: str = "\n\n",
            extract_images: bool = False,
            images_parser: Optional[BaseImageBlobParser] = None,
            images_inner_format: Literal["text", "markdown-img", "html-img"] = "text",
            partition_via_api: bool = False,
            post_processors: Optional[list[Callable[[str], str]]] = None,
            # SDK parameters
            api_key: Optional[str] = None,
            client: Optional[UnstructuredClient] = None,
            password: Optional[str] = None,
            **unstructured_kwargs: Any,
    ) -> None:
        super().__init__(file_path, headers=headers)

        self.parser = UnstructuredPDFParser(
            mode=mode,  # typing: ignore
            pages_delimitor=pages_delimitor,
            extract_images=extract_images,
            images_parser=images_parser,
            images_inner_format=images_inner_format,
            client=client,
            partition_via_api=partition_via_api,
            post_processors=post_processors,
            password=password,
            api_key=api_key,
            **unstructured_kwargs,
        )

    def lazy_load(
            self,
    ) -> Iterator[Document]:
        """Lazy load given path as pages."""
        if self.web_path:
            blob = Blob.from_data(open(self.file_path, "rb").read(),
                                  path=self.web_path)  # type: ignore[attr-defined]
        else:
            blob = Blob.from_path(self.file_path)  # type: ignore[attr-defined]
        yield from self.parser.lazy_parse(blob)
