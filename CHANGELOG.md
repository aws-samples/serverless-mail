# Changelog

## 2025-07-24

### Updated

- **ses-credential-rotation/automatic-rotation**: Upgraded Lambda runtime from Python 3.10 to Python 3.12
- **ses-credential-rotation/manual-rotation**: Upgraded Lambda runtime from Python 3.10 to Python 3.12 (all 5 functions)
- **vdm-to-rds/cloudformation**: Upgraded Lambda runtime from Python 3.9 to Python 3.12 (`downloadvdmqsfiles`, `createsesvdmtables`)

### Rationale

Python 3.9 reached end-of-life in October 2025. Python 3.10 reaches end-of-life in October 2026. Upgrading to Python 3.12 (EOL October 2028) ensures continued security patches and AWS Lambda runtime support.
