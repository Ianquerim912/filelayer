# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in filelayer, please report it responsibly.

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, please email **security@sireto.io** with:

- A description of the vulnerability
- Steps to reproduce the issue
- The potential impact
- Any suggested fixes (optional)

We will acknowledge receipt within 48 hours and aim to provide a fix or mitigation plan within 7 days.

## Security Considerations

filelayer includes the following security measures:

- **Path traversal protection**: The local filesystem provider prevents access outside the configured storage root.
- **Secret handling**: S3 credentials are stored using Pydantic's `SecretStr` to prevent accidental logging.
- **Input validation**: File paths are normalized and validated before use.
