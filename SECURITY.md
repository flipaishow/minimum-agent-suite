# Security policy

## Scope

This project is an evaluation harness. It is not a production tool gateway and does not provide authorization for destructive actions.

## Do not publish

Do not include any of the following in issues, pull requests, commits, or attached logs:

- API keys, access tokens, passwords, SSH private keys, or `.env` files
- Full raw tool/API traces containing private data
- Internal IP addresses, hostnames, absolute home directories, or production service details
- Model weights or private model caches

## Reporting a problem

For a suspected security issue, avoid posting credentials or private traces publicly. Contact the repository owner privately with a minimal reproduction and redact all secrets before sharing.

## Operational boundary

The suite should run against loopback or an explicitly isolated test endpoint. Production services must not be restarted, reconfigured, or used as test targets.
