from __future__ import annotations


class StorageError(Exception):
    """Base exception for storage-related errors."""


class StorageConfigurationError(StorageError):
    """Raised when storage configuration is invalid."""


class StorageReadError(StorageError):
    """Raised when reading fails."""


class StorageWriteError(StorageError):
    """Raised when writing fails."""


class StorageObjectNotFoundError(StorageError):
    """Raised when the requested file or object does not exist."""
