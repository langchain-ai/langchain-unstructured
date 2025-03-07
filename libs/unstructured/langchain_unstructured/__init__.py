"""**Document Loaders**  are classes to load Documents.

**Document Loaders** are usually used to load a lot of Documents in a single run.

**Class hierarchy:**

.. code-block::

    BaseLoader --> <name>Loader  # Examples: TextLoader, UnstructuredFileLoader

**Main helpers:**

.. code-block::

    Document, <name>TextSplitter
"""

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .chm import UnstructuredCHMLoader
    from .csv import UnstructuredCSVLoader

    from .epub import UnstructuredEPubLoader
    from .email import UnstructuredEmailLoader
    from .excel import UnstructuredExcelLoader
    from .html import UnstructuredHTMLLoader
    from .image import UnstructuredImageLoader
    from .markdown import UnstructuredMarkdownLoader
    from .odt import UnstructuredODTLoader
    from .org_mode import UnstructuredOrgModeLoader
    from .pdf import UnstructuredPDFLoader
    from .powerpoint import UnstructuredPowerPointLoader
    from .rst import UnstructuredRSTLoader
    from .rtf import UnstructuredRTFLoader
    from .tsv import UnstructuredTSVLoader
    from .url import UnstructuredURLLoader
    from .word_document import UnstructuredWordDocumentLoader
    # from .unstructured import (  # FIXME
    #     UnstructuredAPIFileIOLoader,
    #     UnstructuredAPIFileLoader,
    #     UnstructuredFileIOLoader,
    #     UnstructuredFileLoader,
    # )
    from .xml import UnstructuredXMLLoader

_module_lookup = {
    "UnstructuredCHMLoader": "langchain_unstructured.chm",
    "UnstructuredCSVLoader": "langchain_unstructured.csv",
    "UnstructuredEPubLoader": "langchain_unstructured.epub",
    "UnstructuredEmailLoader": "langchain_unstructured.email",
    "UnstructuredExcelLoader": "langchain_unstructured.excel",
    "UnstructuredFileIOLoader": "langchain_unstructured.unstructured",
    "UnstructuredFileLoader": "langchain_unstructured.unstructured",
    "UnstructuredHTMLLoader": "langchain_unstructured.html",
    "UnstructuredImageLoader": "langchain_unstructured.image",
    "UnstructuredLoader": "langchain_unstructured.main",
    "UnstructuredMarkdownLoader": "langchain_unstructured.markdown",
    "UnstructuredODTLoader": "langchain_unstructured.odt",
    "UnstructuredOrgModeLoader": "langchain_unstructured.org_mode",
    "UnstructuredPDFLoader": "langchain_unstructured.pdf",
    "UnstructuredPowerPointLoader": "langchain_unstructured.powerpoint",
    "UnstructuredRSTLoader": "langchain_unstructured.rst",
    "UnstructuredRTFLoader": "langchain_unstructured.rtf",
    "UnstructuredTSVLoader": "langchain_unstructured.tsv",
    "UnstructuredURLLoader": "langchain_unstructured.url",
    "UnstructuredWordDocumentLoader": "langchain_unstructured.word_document",
    "UnstructuredXMLLoader": "langchain_unstructured.xml",
}


def __getattr__(name: str) -> Any:
    if name in _module_lookup:
        module = importlib.import_module(_module_lookup[name])
        return getattr(module, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = [
    "UnstructuredCHMLoader",
    "UnstructuredCSVLoader",
    "UnstructuredEPubLoader",
    "UnstructuredEmailLoader",
    "UnstructuredExcelLoader",
    "UnstructuredHTMLLoader",
    "UnstructuredImageLoader",
    "UnstructuredMarkdownLoader",
    "UnstructuredODTLoader",
    "UnstructuredOrgModeLoader",
    "UnstructuredPDFLoader",
    "UnstructuredPowerPointLoader",
    "UnstructuredRSTLoader",
    "UnstructuredRTFLoader",
    "UnstructuredTSVLoader",
    "UnstructuredURLLoader",
    "UnstructuredWordDocumentLoader",
    "UnstructuredXMLLoader",
]
