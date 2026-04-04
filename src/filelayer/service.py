from __future__ import annotations

from .config import StorageSettings
from .factory import create_file_provider
from .providers.base import FileProvider


class StorageService:
    def __init__(self, provider: FileProvider) -> None:
        self.provider = provider

    @classmethod
    def from_settings(cls, settings: StorageSettings | None = None) -> "StorageService":
        provider = create_file_provider(settings=settings)
        return cls(provider)

    def read_file(self, filepath: str) -> str:
        return self.provider.read_file(filepath)

    def write_file(self, filepath: str, file_content: str) -> None:
        self.provider.write_file(filepath, file_content)

    def read_file_bytes(self, filepath: str) -> bytes:
        return self.provider.read_file_bytes(filepath)

    def write_file_bytes(self, filepath: str, file_bytes: bytes) -> None:
        self.provider.write_file_bytes(filepath, file_bytes)

    def exists(self, filepath: str) -> bool:
        return self.provider.exists(filepath)
