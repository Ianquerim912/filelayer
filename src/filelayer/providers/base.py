from __future__ import annotations

from abc import ABC, abstractmethod


class FileProvider(ABC):
    """Abstract base class for storage providers.

    Subclasses must implement all five file operations: read/write for text
    and bytes, plus an existence check.
    """

    @abstractmethod
    def read_file(self, filepath: str) -> str:
        """Read a file and return its content as a string."""
        raise NotImplementedError

    @abstractmethod
    def write_file(self, filepath: str, file_content: str) -> None:
        """Write a string to a file."""
        raise NotImplementedError

    @abstractmethod
    def read_file_bytes(self, filepath: str) -> bytes:
        """Read a file and return its content as raw bytes."""
        raise NotImplementedError

    @abstractmethod
    def write_file_bytes(self, filepath: str, file_bytes: bytes) -> None:
        """Write raw bytes to a file."""
        raise NotImplementedError

    @abstractmethod
    def exists(self, filepath: str) -> bool:
        """Return True if the file exists."""
        raise NotImplementedError
