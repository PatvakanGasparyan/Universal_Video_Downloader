# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public GitHub issue
2. Email the maintainers with a detailed description
3. Include steps to reproduce if possible

We will acknowledge receipt within 48 hours and provide an estimated timeline for a fix.

## Security Measures

This project implements:

- Input validation and URL sanitization
- Path traversal protection
- Rate limiting on API endpoints
- Security headers (CORS, CSP-ready, X-Frame-Options)
- Environment-based secrets management
- Secure temporary file handling

## Best Practices for Deployment

- Always use HTTPS in production
- Change the default `SECRET_KEY`
- Run behind a reverse proxy (Nginx)
- Keep yt-dlp and dependencies updated
- Restrict network access to the download directory
