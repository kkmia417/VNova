# VNova Safety Package Boundary

Status: Architecture skeleton; no safety implementation exists yet

This is the only package permitted to mint `ApprovedResponse`. Candidate text is unsafe by default, and every provider fallback, rewrite, retry, and manual approval path must enter this boundary.

The package implementation is blocked until its language scaffold, persistence contract, boundary checks, and tests are introduced together in a human-reviewed change governed by ADR-008 and ADR-017.

The eventual public surface will expose evaluation inputs, immutable decision/approval views, and identifier-based results. It will not export the concrete approval constructor or mint capability.

Required independent enforcement layers:

- private mint implementation and capability;
- import-linter dependency contracts;
- a nominal TypeScript public view carrying a readonly, non-exported `unique symbol` brand;
- a non-serializable, runtime-frozen approval capability with safety-owned authenticity and rehydration;
- Python AST and TypeScript compiler-AST guards against constructor, subtype, assertion, type-predicate, ambient-value, direct/nested structural or `any` flow, producer/clone calls, and private-module bypasses;
- strict TypeScript compilation as an independent proof that structurally similar values do not satisfy the private brand;
- strict type tests for identifier-only TTS/media interfaces;
- PostgreSQL approval-chain constraints;
- signed and expiry-bound `SpeechTask` verification;
- CODEOWNERS and required repository rules;
- red-team and fail-closed fault-injection tests.

All changes to this path require human review.
