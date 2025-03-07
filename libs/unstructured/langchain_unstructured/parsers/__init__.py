"""**Document Parsers**  are classes to load Documents.

**Document Parsers** are usually used to load a lot of Documents in a single run.

**Class hierarchy:**

.. code-block::

    BaseParser --> <name>Parser  # Examples: TextParser, UnstructuredFileParser

**Main helpers:**

.. code-block::

    Document, <name>TextSplitter
"""

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .chm import (
        UnstructuredCHMParser,
    )
    from .csv import (
        UnstructuredCSVParser,
    )

    from .epub import (
        UnstructuredEPubParser,
    )
    from .email import (
        UnstructuredEmailParser,
    )
    from .excel import (
        UnstructuredExcelParser,
    )
    from .html import (
        UnstructuredHTMLParser,
    )
    from .image import (
        UnstructuredImageParser,
    )
    from .markdown import (
        UnstructuredMarkdownParser,
    )
    from .odt import (
        UnstructuredODTParser,
    )
    from .org_mode import (
        UnstructuredOrgModeParser,
    )
    from .pdf import (
        UnstructuredPDFParser,
    )
    from .powerpoint import (
        UnstructuredPowerPointParser,
    )
    from .rst import (
        UnstructuredRSTParser,
    )
    from .rtf import (
        UnstructuredRTFParser,
    )
    from .tsv import (
        UnstructuredTSVParser,
    )
    from .url import (
        UnstructuredURLParser,
    )
    from .word_document import (
        UnstructuredWordDocumentParser,
        UnstructuredWordParser,
    )
    from .xml import (
        UnstructuredXMLParser,
    )

_module_lookup = {
    "UnstructuredCHMParser": "langchain_unstructured.parsers.chm",
    "UnstructuredCSVParser": "langchain_unstructured.parsers.csv",
    "UnstructuredEPubParser": "langchain_unstructured.parsers.epub",
    "UnstructuredEmailParser": "langchain_unstructured.parsers.email",
    "UnstructuredExcelParser": "langchain_unstructured.parsers.excel",
    "UnstructuredFileIOParser": "langchain_unstructured.parsers.unstructured",
    "UnstructuredFileParser": "langchain_unstructured.parsers.unstructured",
    "UnstructuredHTMLParser": "langchain_unstructured.parsers.html",
    "UnstructuredImageParser": "langchain_unstructured.parsers.image",
    "UnstructuredParser": "langchain_unstructured.parsers.unstructured",
    "UnstructuredMarkdownParser": "langchain_unstructured.parsers.markdown",
    "UnstructuredODTParser": "langchain_unstructured.parsers.odt",
    "UnstructuredOrgModeParser": "langchain_unstructured.parsers.org_mode",
    "UnstructuredPDFParser": "langchain_unstructured.parsers.pdf",
    "UnstructuredPowerPointParser": "langchain_unstructured.parsers.powerpoint",
    "UnstructuredRSTParser": "langchain_unstructured.parsers.rst",
    "UnstructuredRTFParser": "langchain_unstructured.parsers.rtf",
    "UnstructuredTSVParser": "langchain_unstructured.parsers.tsv",
    "UnstructuredURLParser": "langchain_unstructured.parsers.url",
    "UnstructuredWordDocumentParser": "langchain_unstructured.parsers.word_document",
    "UnstructuredXMLParser": "langchain_unstructured.parsers.xml",
}


def __getattr__(name: str) -> Any:
    if name in _module_lookup:
        module = importlib.import_module(_module_lookup[name])
        return getattr(module, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = [
    "UnstructuredCHMParser",
    "UnstructuredCSVParser",
    "UnstructuredEPubParser",
    "UnstructuredEmailParser",
    "UnstructuredExcelParser",
    "UnstructuredHTMLParser",
    "UnstructuredImageParser",
    "UnstructuredMarkdownParser",
    "UnstructuredODTParser",
    "UnstructuredOrgModeParser",
    "UnstructuredPDFParser",
    "UnstructuredPowerPointParser",
    "UnstructuredRSTParser",
    "UnstructuredRTFParser",
    "UnstructuredTSVParser",
    "UnstructuredURLParser",
    "UnstructuredWordDocumentParser",
    "UnstructuredXMLParser",
]
