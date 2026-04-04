# filelayer

[![CI](https://github.com/sireto/filelayer/actions/workflows/ci.yml/badge.svg)](https://github.com/sireto/filelayer/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/filelayer.svg)](https://pypi.org/project/filelayer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)

`filelayer` is a small Python package that provides a simple file abstraction over:

- local filesystem
- S3-compatible object storage such as Wasabi

It exposes a minimal API:

- `read_file(filepath) -> str`
- `write_file(filepath, file_content) -> None`
- `read_file_bytes(filepath) -> bytes`
- `write_file_bytes(filepath, file_bytes) -> None`
- `exists(filepath) -> bool`

For S3-compatible backends, `filepath` is treated as the object key.
For local storage, `filepath` is resolved relative to the configured local base path.

## Installation

```bash
pip install filelayer
```

For development:

```bash
pip install -e .[dev]
```

## Quick start

No configuration needed — local filesystem is the default:

```python
from filelayer import StorageService

storage = StorageService.from_settings()

storage.write_file("documents/example.txt", "Hello from local storage")
content = storage.read_file("documents/example.txt")
print(content)

storage.write_file_bytes("documents/example.bin", b"\x00\x01\x02")
print(storage.read_file_bytes("documents/example.bin"))
print(storage.exists("documents/example.txt"))
```

By default, files are stored under `./data/storage`. You can customize this and other settings via environment variables or a `.env` file:

```env
STORAGE_PROVIDER=local          # default
STORAGE_DEFAULT_PREFIX=my-app   # optional path prefix
STORAGE_ENCODING=utf-8          # default
LOCAL_STORAGE_BASE_PATH=./data/storage  # default
```

## Wasabi / S3-compatible example

Environment:

```env
STORAGE_PROVIDER=s3
STORAGE_DEFAULT_PREFIX=my-app
STORAGE_ENCODING=utf-8

S3_ENDPOINT_URL=https://s3.eu-central-1.wasabisys.com
S3_ACCESS_KEY_ID=your-access-key
S3_SECRET_ACCESS_KEY=your-secret-key
S3_REGION_NAME=eu-central-1
S3_BUCKET=your-bucket
S3_USE_SSL=true
S3_VERIFY_SSL=true
S3_ADDRESSING_STYLE=virtual
S3_CONNECT_TIMEOUT=10
S3_READ_TIMEOUT=60
S3_MAX_ATTEMPTS=5
```

Usage:

```python
from filelayer import StorageService

storage = StorageService.from_settings()

storage.write_file("documents/example.txt", "Hello from Wasabi")
print(storage.read_file("documents/example.txt"))
print(storage.exists("documents/example.txt"))
```

## S3 caching

The S3 provider caches downloaded objects on the local filesystem to save bandwidth.
Caching is **enabled by default** and uses ETag-based revalidation — on repeated reads,
a conditional GET is sent to S3. If the object hasn't changed (304 Not Modified), the
cached copy is used. Writes are write-through: after a successful upload, the content
is stored in the cache immediately.

```env
S3_CACHE_ENABLED=true                    # default, set to false to disable
S3_CACHE_DIR=/tmp/filelayer_cache        # default: system temp directory
```

## Notes

- `STORAGE_DEFAULT_PREFIX` is prepended to all paths or keys.
- `write_file()` stores text using `STORAGE_ENCODING`.
- `write_file_bytes()` stores raw bytes unchanged.
- Local provider prevents path traversal outside the configured storage root.

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

This project is licensed under the [MIT License](LICENSE).
