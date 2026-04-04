# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-31

### Added

- Initial release of filelayer.
- `StorageService` with text and bytes read/write operations.
- `LocalFileProvider` for local filesystem storage with path traversal protection.
- `S3FileProvider` for S3-compatible storage (AWS S3, Wasabi, MinIO, etc.).
- Pydantic-based configuration via environment variables and `.env` files.
- Factory function `create_file_provider()` for provider instantiation.
- Structured JSON logging via `StructuredLogger`.
- Custom exception hierarchy (`StorageError`, `StorageReadError`, `StorageWriteError`, etc.).

[0.1.0]: https://github.com/sireto/filelayer/releases/tag/v0.1.0
