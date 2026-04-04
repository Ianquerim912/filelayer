from __future__ import annotations

from abc import ABC, abstractmethod


class FileProvider(ABC):
    @abstractmethod
    def read_file(self, filepath: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def write_file(self, filepath: str, file_content: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def read_file_bytes(self, filepath: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def write_file_bytes(self, filepath: str, file_bytes: bytes) -> None:
        raise NotImplementedError

    @abstractmethod
    def exists(self, filepath: str) -> bool:
        raise NotImplementedError
