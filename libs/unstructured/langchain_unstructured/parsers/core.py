"""Unstructured document loader."""

from __future__ import annotations

import json
import logging
import os
from abc import abstractmethod
from copy import deepcopy
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterator,
    Optional,
    Literal, )

from langchain_community.document_loaders.blob_loaders import Blob
from langchain_core.document_loaders.base import BaseBlobParser
from langchain_core.documents import Document
from typing_extensions import TypeAlias
from unstructured_client.models import shared

if TYPE_CHECKING:
    from unstructured_client import UnstructuredClient
    from unstructured_client.models import operations  # type:ignore[attr-defined]

Element: TypeAlias = Any

logger = logging.getLogger(__file__)

_DEFAULT_URL = "https://api.unstructuredapp.io/general/v0/general"


def satisfies_min_unstructured_version(min_version: str) -> bool:
    """Check if the installed `Unstructured` version exceeds the minimum version
    for the feature in question."""
    from unstructured.__version__ import __version__ as __unstructured_version__

    min_version_tuple = tuple([int(x) for x in min_version.split(".")])

    # NOTE(MthwRobinson) - enables the loader to work when you're using pre-release
    # versions of unstructured like 0.4.17-dev1
    _unstructured_version = __unstructured_version__.split("-")[0]
    unstructured_version_tuple = tuple(
        [int(x) for x in _unstructured_version.split(".")]
    )

    return unstructured_version_tuple >= min_version_tuple


def validate_unstructured_version(min_unstructured_version: str) -> None:
    """Raise an error if the `Unstructured` version does not exceed the
    specified minimum."""
    if not satisfies_min_unstructured_version(min_unstructured_version):
        raise ValueError(
            f"unstructured>={min_unstructured_version} is required in this loader."
        )


# _lock # FIXME

class _UnstructuredDocumentParseur(BaseBlobParser):
    """Provides loader functionality for individual document/file objects.

    Encapsulates partitioning individual file objects (file or file_path) either
    locally or via the Unstructured API.
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
        """Initialize parser."""
        _valid_modes = {"single", "elements", "paged"}
        if mode not in _valid_modes:
            raise ValueError(
                f"Got {mode} for `mode`, but should be one of `{_valid_modes}`"
            )

        self._check_if_both_mode_and_chunking_strategy_are_by_page(
            mode, unstructured_kwargs
        )

        self.mode = mode
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

        self.partition_via_api = partition_via_api
        self.post_processors = post_processors
        # SDK parameters
        self.api_key = api_key or os.getenv("UNSTRUCTURED_API_KEY") or ""
        self.url = url or os.getenv("UNSTRUCTURED_URL") or _DEFAULT_URL
        self.unstructured_kwargs = unstructured_kwargs
        if web_url:
            self.unstructured_kwargs["url"] = web_url

        if partition_via_api:
            try:
                from unstructured_client import UnstructuredClient

                self.client = client or UnstructuredClient(
                    api_key_auth=self.api_key, server_url=self.url
                )
            except ImportError:
                raise ImportError(
                    "unstructured package not found, please install it with "
                    "`pip install 'langchain_unstructured[client]'`"
                )

    def _check_if_both_mode_and_chunking_strategy_are_by_page(
        self, mode: str, unstructured_kwargs: dict[str, Any]
    ) -> None:
        if (
            mode == "paged"
            and unstructured_kwargs.get("chunking_strategy") == "by_page"
        ):
            raise ValueError(
                "Only one of `chunking_strategy='by_page'` or `mode='paged'` may be"
                " set. `chunking_strategy` is preferred."
            )

    def lazy_parse(self, blob: Blob) -> Iterator[Document]:
        """Load blob."""
        # if self.file and self.unstructured_kwargs.get("metadata_filename") is None:
        #     raise ValueError(
        #         "If partitioning a fileIO object, metadata_filename must be specified"
        #         " as well.",
        #     )
        elements = (
            self._post_process_elements_json(self._get_elements_json(blob))
            if self.post_processors
            else self._get_elements_json(blob)
        )
        metadata = {**blob.metadata, **{"source": blob.source}}  # FIXME: file
        if self.mode == "elements":
            for element in elements:
                metadata = deepcopy(metadata)
                metadata.update(element.get("metadata"))  # type: ignore
                metadata.update(
                    {"category": element.get("category") or element.get("type")}
                )
                metadata.update({"element_id": element.get("element_id")})
                yield Document(page_content=str(element), metadata=metadata)
        elif self.mode == "paged":
            logger.warning(
                "`mode='paged'` is deprecated in favor of the 'by_page' chunking"
                " strategy. Learn more about chunking here:"
                " https://docs.unstructured.io/open-source/core-functionality/chunking"
            )
            text_dict: dict[int, str] = {}
            meta_dict: dict[int, dict[str, Any]] = {}

            for element in elements:
                metadata = deepcopy(metadata)
                metadata.update(element.get("metadata"))  # type: ignore
                page_number = metadata.get("page_number", 1)

                # Check if this page_number already exists in text_dict
                if page_number not in text_dict:
                    # If not, create new entry with initial text and metadata
                    text_dict[page_number] = str(element) + "\n\n"
                    meta_dict[page_number] = metadata
                else:
                    # If exists, append to text and update the metadata
                    text_dict[page_number] += str(element) + "\n\n"
                    meta_dict[page_number].update(metadata)

            # Convert the dict to a list of Document objects
            for key in text_dict.keys():
                yield Document(page_content=text_dict[key], metadata=meta_dict[key])
        elif self.mode == "single":
            metadata = deepcopy(metadata)
            text = "\n\n".join([str(el) for el in elements])
            yield Document(page_content=text, metadata=metadata)
        else:
            raise ValueError(f"mode of {self.mode} not supported.")

    def _get_elements_json(self, blob: Blob) -> list[dict[str, Any]]:
        """Get elements as a list of dictionaries from local partition or via API."""
        if self.partition_via_api:
            return self._get_elements_via_api(blob)

        return self._convert_elements_to_dicts(self._get_elements_via_local(blob))

    @abstractmethod
    def _get_elements_via_local(self, blob: Blob) -> list[Element]:
        ...
        # try:
        #     from unstructured.partition.auto import partition  # type: ignore
        # except ImportError:
        #     raise ImportError(
        #         "unstructured package not found, please install it with "
        #         "`pip install unstructured`"
        #     )
        #
        # return partition(
        #     file=blob.as_bytes_io(), filename=str(blob.path), **self.unstructured_kwargs
        # )

    def _get_elements(self, blob: Blob) -> list:
        return partition(filename=self.file_path,
                         **self.unstructured_kwargs)  # type: ignore[arg-type]

    def _get_elements_via_api(self, blob: Blob) -> list[dict[str, Any]]:
        """Retrieve a list of element dicts from the API using the SDK client."""
        client = self.client
        req = self._sdk_partition_request(blob)
        response = client.general.partition(request=req)
        if response.status_code == 200:
            return json.loads(response.raw_response.text)
        raise ValueError(
            f"Receive unexpected status code {response.status_code} from the API.",
        )

    def _sdk_partition_request(self, blob: Blob) -> operations.PartitionRequest:
        from unstructured_client.models import operations
        return operations.PartitionRequest(
            partition_parameters=shared.PartitionParameters(
                files=shared.Files(
                    content=blob.as_bytes(),
                    file_name=str(blob.path),
                    content_type=blob.mimetype,
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
        return {"source": self.file_path} if self.file_path else {}

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
