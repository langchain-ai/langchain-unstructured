from typing import Any, List, Dict, Union

from langchain_community.document_loaders.unstructured import (
    validate_unstructured_version,
)
from langchain_core.documents.base import Blob

from langchain_unstructured.parsers.core import \
    _UnstructuredDocumentParseur


class CHMParser(object):  # FIXME
    """Microsoft Compiled HTML Help (CHM) Parser."""

    path: str
    file: "chm.CHMFile"

    def __init__(self, path: str):
        from chm import chm

        self.path = path
        self.file = chm.CHMFile()
        self.file.LoadCHM(path)

    def __enter__(self):  # type: ignore[no-untyped-def]
        return self

    def __exit__(self, exc_type, exc_value, traceback):  # type: ignore[no-untyped-def]
        if self.file:
            self.file.CloseCHM()

    @property
    def encoding(self) -> str:
        return self.file.GetEncoding().decode("utf-8")

    def index(self) -> List[Dict[str, str]]:
        from urllib.parse import urlparse

        from bs4 import BeautifulSoup

        res = []
        index = self.file.GetTopicsTree().decode(self.encoding)
        soup = BeautifulSoup(index)
        # <OBJECT ..>
        for obj in soup.find_all("object"):
            # <param name="Name" value="<...>">
            # <param name="Local" value="<...>">
            name = ""
            local = ""
            for param in obj.find_all("param"):
                if param["name"] == "Name":
                    name = param["value"]
                if param["name"] == "Local":
                    local = param["value"]
            if not name or not local:
                continue

            local = urlparse(local).path
            if not local.startswith("/"):
                local = "/" + local
            res.append({"name": name, "local": local})

        return res

    def load(self, path: Union[str, bytes]) -> str:
        if isinstance(path, str):
            path = path.encode("utf-8")
        obj = self.file.ResolveObject(path)[1]
        return self.file.RetrieveObject(obj)[1].decode(self.encoding)

    def load_all(self) -> List[Dict[str, str]]:  # FIXME: c'est sur fichiers
        res = []
        index = self.index()
        for item in index:
            content = self.load(item["local"])
            res.append(
                {
                    "name": item["name"],
                    "local": item["local"],
                    "content": content,
                }
            )
        return res

class UnstructuredCHMParser(_UnstructuredDocumentParseur):
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
                "`pip install 'langchain_unstructured[html]'`"
            )

        with CHMParser(self.file_path) as f:  # type: ignore[arg-type]

            return [
                partition_html(text=item["content"], **self.unstructured_kwargs)
                for item in f.load_all()
            ]
            # return partition_html(
            #     file=blob.as_bytes_io(), filename=str(blob.path), **self.unstructured_kwargs
            # )
