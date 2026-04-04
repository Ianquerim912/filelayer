from __future__ import annotations

from .config import StorageSettings
from .factory import create_file_provider
from .providers.base import FileProvider


class StorageService:
    """High-level storage service that delegates to a configured file provider.

    Use ``from_settings()`` to create an instance from environment variables,
    or pass a ``FileProvider`` directly to the constructor.
    """

    def __init__(self, provider: FileProvider) -> None:
        self.provider = provider

    @classmethod
    def from_settings(cls, settings: StorageSettings | None = None) -> StorageService:
        """Create a StorageService from settings (loaded from environment by default)."""
        provider = create_file_provider(settings=settings)
        return cls(provider)

    def read_file(self, filepath: str) -> str:
        """Read a file and return its content as a string."""
        return self.provider.read_file(filepath)

    def write_file(self, filepath: str, file_content: str) -> None:
        """Write a string to a file, encoding with the configured charset."""
        self.provider.write_file(filepath, file_content)

    def read_file_bytes(self, filepath: str) -> bytes:
        """Read a file and return its content as raw bytes."""
        return self.provider.read_file_bytes(filepath)

    def write_file_bytes(self, filepath: str, file_bytes: bytes) -> None:
        """Write raw bytes to a file."""
        self.provider.write_file_bytes(filepath, file_bytes)

    def exists(self, filepath: str) -> bool:
        """Return True if the file exists."""
        return self.provider.exists(filepath)

    def resolve_path(self, filepath: str) -> str:
        """Return the full resolved path or key for the given filepath.

        For local storage, returns the absolute filesystem path.
        For S3, returns ``s3://<bucket>/<key>``.
        """
        return self.provider.resolve_path(filepath)
