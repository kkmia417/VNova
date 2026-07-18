# Red-Team Regression Corpus

Status: Governance skeleton; no production fixtures exist yet

This protected suite will contain non-secret, reviewable regression fixtures for:

- direct and indirect prompt injection;
- control-character and delimiter attacks;
- malicious or unsafe usernames and spoken-name normalization;
- SSML, markup, phoneme, and TTS control-token injection;
- persona and character-integrity attacks;
- memory poisoning and authority-claim persistence;
- rewrite-loop and fallback-path bypass attempts;
- multilingual and obfuscated policy evasion;
- stale approval, signed-task replay, and artifact substitution.

Every fixture must declare its input surface, expected safety category, expected action by autonomy mode, policy version, and a short rationale. Fixtures must not include real secrets, unnecessary personal data, or prohibited content beyond the minimum needed to reproduce the safety behavior.

Safety-relevant changes must run the affected subset. Policy or classifier changes must also report intended decision deltas; silently updating expected results to make a test pass is forbidden.
