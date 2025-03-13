from typing import Literal, Optional, Callable, Any, TYPE_CHECKING

from .core import _UnstructuredDocumentParseur
from langchain_core.documents.base import Blob

if TYPE_CHECKING:
    from unstructured_client import UnstructuredClient
    from unstructured_client.models import operations  # type:ignore[attr-defined]
else:
    UnstructuredClient=Any



class UnstructuredParser(_UnstructuredDocumentParseur):
    """Parse files using `Unstructured`.

    The parser uses the unstructured partition function and will automatically
    detect the format. You can run the parser in different modes: "single",
    "elements", and "paged". The default "single" mode will return a single langchain
    Document object. If you use "elements" mode, the unstructured library will split
    the document into elements such as Title and NarrativeText and return those as
    individual langchain Document objects. In addition to these post-processing modes
    (which are specific to the LangChain Loaders), Unstructured has its own "chunking"
    parameters for post-processing elements into more useful chunks for uses cases such
    as Retrieval Augmented Generation (RAG). You can pass in additional unstructured
    kwargs to configure different unstructured settings.

    Examples
    --------
    from langchain_community.document_loaders import UnstructuredFileLoader

    loader = UnstructuredFileLoader(
        "example.pdf", mode="elements", strategy="fast",
    )
    docs = loader.load()

    References
    ----------
    https://docs.unstructured.io/open-source/core-functionality/partitioning
    https://docs.unstructured.io/open-source/core-functionality/chunking
    """

    def __init__(
            self,
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
        super().__init__( partition_via_api=partition_via_api,
               post_processors=post_processors,
               mode=mode,
               api_key=api_key,
               client=client,
               url=url,
               web_url=web_url,
               **unstructured_kwargs)

    def _get_elements_via_local(self, blob:Blob) -> list:
        try:
            from unstructured.partition.auto import partition  # type: ignore
        except ImportError:
            raise ImportError(
                "unstructured package not found, please install it with "
                "`pip install 'langchain_unstructured[all_docs]' or some file formats`"
            )

        if blob.data is None and blob.path:
            filename = str(blob.path)
            file = None
        else:
            filename = None
            file = blob.as_bytes_io()
        return partition(
            filename=filename,
            file=file,
            **self.unstructured_kwargs
        )
