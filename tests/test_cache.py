from __future__ import annotations

from pathlib import Path

from filelayer.cache import S3FileCache


class TestS3FileCache:
    def test_put_and_get(self, tmp_path: Path) -> None:
        cache = S3FileCache(cache_dir=tmp_path)
        cache.put("bucket", "key.txt", b"hello", '"etag123"')

        result = cache.get("bucket", "key.txt")
        assert result is not None
        data, etag = result
        assert data == b"hello"
        assert etag == '"etag123"'

    def test_get_miss(self, tmp_path: Path) -> None:
        cache = S3FileCache(cache_dir=tmp_path)
        assert cache.get("bucket", "missing.txt") is None

    def test_get_etag(self, tmp_path: Path) -> None:
        cache = S3FileCache(cache_dir=tmp_path)
        cache.put("bucket", "key.txt", b"hello", '"etag123"')

        assert cache.get_etag("bucket", "key.txt") == '"etag123"'

    def test_get_etag_miss(self, tmp_path: Path) -> None:
        cache = S3FileCache(cache_dir=tmp_path)
        assert cache.get_etag("bucket", "missing.txt") is None

    def test_evict(self, tmp_path: Path) -> None:
        cache = S3FileCache(cache_dir=tmp_path)
        cache.put("bucket", "key.txt", b"hello", '"etag123"')
        cache.evict("bucket", "key.txt")

        assert cache.get("bucket", "key.txt") is None
        assert cache.get_etag("bucket", "key.txt") is None

    def test_evict_nonexistent_is_noop(self, tmp_path: Path) -> None:
        cache = S3FileCache(cache_dir=tmp_path)
        cache.evict("bucket", "nope.txt")  # should not raise

    def test_put_overwrites(self, tmp_path: Path) -> None:
        cache = S3FileCache(cache_dir=tmp_path)
        cache.put("bucket", "key.txt", b"v1", '"etag1"')
        cache.put("bucket", "key.txt", b"v2", '"etag2"')

        result = cache.get("bucket", "key.txt")
        assert result is not None
        assert result[0] == b"v2"
        assert result[1] == '"etag2"'

    def test_different_keys_are_isolated(self, tmp_path: Path) -> None:
        cache = S3FileCache(cache_dir=tmp_path)
        cache.put("bucket", "a.txt", b"aaa", '"etag-a"')
        cache.put("bucket", "b.txt", b"bbb", '"etag-b"')

        a = cache.get("bucket", "a.txt")
        b = cache.get("bucket", "b.txt")
        assert a is not None and a[0] == b"aaa"
        assert b is not None and b[0] == b"bbb"

    def test_default_cache_dir(self) -> None:
        cache = S3FileCache()
        assert cache.cache_dir.name == "filelayer_cache"
        assert cache.cache_dir.exists()

    def test_corrupt_meta_evicts_entry(self, tmp_path: Path) -> None:
        cache = S3FileCache(cache_dir=tmp_path)
        cache.put("bucket", "key.txt", b"hello", '"etag123"')

        # Corrupt the meta file
        base = cache._cache_path("bucket", "key.txt")
        base.with_suffix(".meta").write_text("not json", encoding="utf-8")

        assert cache.get("bucket", "key.txt") is None
        # After failed read, entry should be evicted
        assert not base.with_suffix(".data").exists()
        assert not base.with_suffix(".meta").exists()
