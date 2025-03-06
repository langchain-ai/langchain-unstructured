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
    from langchain_unstructured.document_loaders.chm import (
        UnstructuredCHMLoader,
    )
    from langchain_unstructured.document_loaders.csv_loader import (
        UnstructuredCSVLoader,
    )

    from langchain_unstructured.document_loaders.epub import (
        UnstructuredEPubLoader,
    )
    from langchain_unstructured.document_loaders.excel import (
        UnstructuredExcelLoader,
    )
    from langchain_unstructured.document_loaders.main import (
        UnstructuredLoader,
    )
    from langchain_unstructured.document_loaders.markdown import (
        UnstructuredMarkdownLoader,
    )
    from langchain_unstructured.document_loaders.odt import (
        UnstructuredODTLoader,
    )
    from langchain_unstructured.document_loaders.org_mode import (
        UnstructuredOrgModeLoader,
    )
    from langchain_unstructured.document_loaders.powerpoint import (
        UnstructuredPowerPointLoader,
    )
    from langchain_unstructured.document_loaders.rst import (
        UnstructuredRSTLoader,
    )
    from langchain_unstructured.document_loaders.rtf import (
        UnstructuredRTFLoader,
    )
    from langchain_unstructured.document_loaders.tsv import (
        UnstructuredTSVLoader,
    )
    from langchain_unstructured.document_loaders.unstructured import (
        UnstructuredAPIFileIOLoader,
        UnstructuredAPIFileLoader,
        UnstructuredFileIOLoader,
        UnstructuredFileLoader,
    )
    from langchain_unstructured.document_loaders.url import (
        UnstructuredURLLoader,
    )
    from langchain_unstructured.document_loaders.word_document import (
        UnstructuredWordDocumentLoader,
    )
    from langchain_unstructured.document_loaders.xml import (
        UnstructuredXMLLoader,
    )

_module_lookup = {
    "UnstructuredAPIFileIOLoader": "langchain_unstructured.document_loaders.unstructured",
    "UnstructuredAPIFileLoader": "langchain_unstructured.document_loaders.unstructured",
    "UnstructuredCHMLoader": "langchain_unstructured.document_loaders.chm",
    "UnstructuredCSVLoader": "langchain_unstructured.document_loaders.csv_loader",
    "UnstructuredEPubLoader": "langchain_unstructured.document_loaders.epub",
    "UnstructuredEmailLoader": "langchain_unstructured.document_loaders.email",
    "UnstructuredExcelLoader": "langchain_unstructured.document_loaders.excel",
    "UnstructuredFileIOLoader": "langchain_unstructured.document_loaders.unstructured",
    "UnstructuredFileLoader": "langchain_unstructured.document_loaders.unstructured",
    "UnstructuredHTMLLoader": "langchain_unstructured.document_loaders.html",
    "UnstructuredImageLoader": "langchain_unstructured.document_loaders.image",
    "UnstructuredLoader": "langchain_unstructured.document_loaders.main",
    "UnstructuredMarkdownLoader": "langchain_unstructured.document_loaders.markdown",
    "UnstructuredODTLoader": "langchain_unstructured.document_loaders.odt",
    "UnstructuredOrgModeLoader": "langchain_unstructured.document_loaders.org_mode",
    "UnstructuredPDFLoader": "langchain_unstructured.document_loaders.pdf",
    "UnstructuredPowerPointLoader": "langchain_unstructured.document_loaders.powerpoint",
    "UnstructuredRSTLoader": "langchain_unstructured.document_loaders.rst",
    "UnstructuredRTFLoader": "langchain_unstructured.document_loaders.rtf",
    "UnstructuredTSVLoader": "langchain_unstructured.document_loaders.tsv",
    "UnstructuredURLLoader": "langchain_unstructured.document_loaders.url",
    "UnstructuredWordDocumentLoader": "langchain_unstructured.document_loaders.word_document",  # noqa: E501
    "UnstructuredXMLLoader": "langchain_unstructured.document_loaders.xml",
}


def __getattr__(name: str) -> Any:
    if name in _module_lookup:
        module = importlib.import_module(_module_lookup[name])
        return getattr(module, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = [
    "UnstructuredAPIFileIOLoader",
    "UnstructuredAPIFileLoader",
    "UnstructuredCHMLoader",
    "UnstructuredCSVLoader",
    "UnstructuredEPubLoader",
    "UnstructuredEmailLoader",
    "UnstructuredExcelLoader",
    "UnstructuredFileIOLoader",
    "UnstructuredFileLoader",
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
