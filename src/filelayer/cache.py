"""Local filesystem cache for S3 objects, using ETags for revalidation."""

from __future__ import annotations

import hashlib
import json
import logging
import tempfile
from pathlib import Path

from .logging_utils import StructuredLogger


class S3FileCache:
    """Caches S3 object content on the local filesystem.

    Each cached object is stored as two files under the cache directory:
    - ``<hash>.data`` — the raw bytes of the object
    - ``<hash>.meta`` — JSON with the ETag and the original S3 key

    Revalidation is done externally by the caller (S3FileProvider) using
    the stored ETag and S3 conditional requests.
    """

    def __init__(
        self,
        cache_dir: Path | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        if cache_dir is None:
            cache_dir = Path(tempfile.gettempdir()) / "filelayer_cache"
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.log = StructuredLogger(logger or logging.getLogger(self.__class__.__name__))

    def _cache_path(self, bucket: str, key: str) -> Path:
        """Return a deterministic path for a given bucket/key pair."""
        digest = hashlib.sha256(f"{bucket}/{key}".encode()).hexdigest()
        return self.cache_dir / digest

    def get(self, bucket: str, key: str) -> tuple[bytes, str] | None:
        """Return cached ``(content_bytes, etag)`` or ``None`` if not cached."""
        base = self._cache_path(bucket, key)
        data_path = base.with_suffix(".data")
        meta_path = base.with_suffix(".meta")

        if not data_path.exists() or not meta_path.exists():
            return None

        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            data = data_path.read_bytes()
            self.log.info("cache_hit", bucket=bucket, key=key, etag=meta["etag"])
            return data, meta["etag"]
        except Exception:
            self.log.warning("cache_read_failed", bucket=bucket, key=key)
            self.evict(bucket, key)
            return None

    def get_etag(self, bucket: str, key: str) -> str | None:
        """Return the cached ETag for a key, or ``None`` if not cached."""
        base = self._cache_path(bucket, key)
        meta_path = base.with_suffix(".meta")

        if not meta_path.exists():
            return None

        try:
            meta: dict[str, str] = json.loads(meta_path.read_text(encoding="utf-8"))
            return meta["etag"]
        except Exception:
            return None

    def put(self, bucket: str, key: str, data: bytes, etag: str) -> None:
        """Store content and its ETag in the cache."""
        base = self._cache_path(bucket, key)
        data_path = base.with_suffix(".data")
        meta_path = base.with_suffix(".meta")

        try:
            data_path.write_bytes(data)
            meta_path.write_text(
                json.dumps({"bucket": bucket, "key": key, "etag": etag}),
                encoding="utf-8",
            )
            self.log.info("cache_put", bucket=bucket, key=key, etag=etag, size_bytes=len(data))
        except Exception:
            self.log.warning("cache_write_failed", bucket=bucket, key=key)
            # Clean up partial writes
            data_path.unlink(missing_ok=True)
            meta_path.unlink(missing_ok=True)

    def evict(self, bucket: str, key: str) -> None:
        """Remove a cached entry."""
        base = self._cache_path(bucket, key)
        base.with_suffix(".data").unlink(missing_ok=True)
        base.with_suffix(".meta").unlink(missing_ok=True)
