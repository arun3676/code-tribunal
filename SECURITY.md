# Security Policy

## Supported versions

Only the latest release of `code-tribunal` receives security fixes.

## Reporting a vulnerability

Please **do not** open a public issue for security reports. Instead, use
[GitHub private vulnerability reporting](https://github.com/arun3676/code-tribunal/security/advisories/new).

You can expect an acknowledgement within a few days. Please include a proof of
concept and the affected version.

## Scope notes

- The CLI/MCP server read provider API keys from environment variables only;
  keys are never logged or echoed (`tribunal doctor` masks them by design).
- The hosted demo backend is rate-limited and holds no user data beyond
  waitlist email addresses (stored in Resend).
