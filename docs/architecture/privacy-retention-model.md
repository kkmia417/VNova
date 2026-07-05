# Privacy And Retention Model

Status: Stub

See ADR-017: `docs/adr/0017-data-retention-privacy-and-pii.md`.

VNova separates viewer memory from audit logs. Viewer memory uses typed slots and can be deleted with embedding cascade through source-record foreign keys. Audit logs use IDs and hashes, not viewer-memory content.

Exact retention durations require human-approved retention policy before production launch.
