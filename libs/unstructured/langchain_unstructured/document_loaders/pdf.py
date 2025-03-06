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
