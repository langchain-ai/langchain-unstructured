"""Unstructured document loader."""

from __future__ import annotations

import logging
import os
from pathlib import Path, PurePath
from tempfile import TemporaryDirectory
from typing import (
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
from langchain_core.document_loaders.base import BaseBlobParser
from langchain_core.documents import Document
from typing_extensions import TypeAlias

from .main import _SingleDocumentLoader

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


