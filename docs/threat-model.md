# Threat model (initial)

## Assets

Citizen profile and eligibility answers; uploaded certificate images; extracted names/DOB/income; interview state; source snapshots; rule registry; browser sessions; portal applications and credentials.

## Principal threats and controls

- **False entitlement / outdated rules:** authoritative source links, source hashes, review-required compilation, temporal versioning, golden tests, visible abstention and official verification.
- **Prompt injection in GR or certificate text:** source is explicitly treated as untrusted data, limited AST schema, no code execution, deterministic evaluator, output validation.
- **Sensitive-data exposure:** no full Aadhaar schema field, local-only model endpoint, transient image handling, no profile logging, retention default, no browser storage reuse. Production still requires encryption, access control, audited deletion and a DPIA.
- **SSRF / malicious URLs during ingestion:** HTTPS-only official host allowlist, re-check redirects, bounded responses, explicit URL invocation, robots policy.
- **Browser automation reaches live government site:** hard-coded loopback hostname and `/demo-form` path, browser route blocks remote hosts, no URL is accepted from the profile, mandatory typed confirmation.
- **Cross-document false positive:** name similarity/phonetic matching is advisory only; language-specific spellings can vary; all mismatches require human inspection.
- **Document image bombs / oversized files:** byte and pixel limits, image decode validation. Production must add malware scanning and CPU/memory sandboxing.
- **Checkpoint leaks:** in-memory demo loses state on restart; production needs an encrypted serializer, key rotation, per-user authorization, strict TTL and delete workflows.
- **Malicious application submit:** demo only; no real submit endpoint is implemented. A future official integration needs written authorization, scope limits, auditability and per-case confirmation.

## Out of scope for the scaffold

Legal advice, certificate authenticity guarantees, automated entitlement decisions, collection of Aadhaar numbers/OTP, bypassing portal restrictions, making representations on a citizen's behalf, and submitting real applications.
