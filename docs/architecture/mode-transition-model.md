# Mode Transition Model

Status: Stub

Mode transitions are operational safety behavior, not UI decoration.

Required future ADR: ADR-020.

Expected binding shape from the review:

- Downward transitions are instant and always allowed.
- Upward transitions require preconditions and operator confirmation.
- Provider failure auto-degrades.
- Safety escalation auto-degrades.
- Operator absence in higher autonomy auto-degrades.
- Some content categories, such as sponsor reads, may have autonomy caps.
