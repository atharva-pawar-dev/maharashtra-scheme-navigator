# Source and rule governance

## Source precedence

1. Current Government Resolution / gazette / legally operative notification.
2. Current departmental scheme guideline and official form/checklist.
3. Official portal help page and notified-service table.
4. myScheme summary or other official aggregator for discovery; not sufficient alone to resolve contradictory legal wording.

## Ingestion policy

- Supply exact URLs from the source registry. Do not crawl portal accounts or discover hidden endpoints.
- HTTPS and a small domain allowlist are mandatory; redirects are revalidated.
- Respect `robots.txt`; if policy cannot be read, the fetch fails closed unless a maintainer documents an authorized exception.
- Do not automate login, OTP, CAPTCHA, session replay, or authenticated scraping.
- Store fetched-byte SHA-256, final URL, fetch timestamp, extraction/parser version and document text. Treat extracted text as untrusted content.
- Never use a scheme summary alone to invent missing rules, exception clauses, validity periods or document dependencies.

## Rule review checklist

- Verify the exact GR/notification number, issue date, amendments and superseding documents.
- Capture the exact criteria, definitions and exceptions, preserving Marathi wording alongside the translation.
- Independently verify every AST leaf, operator and threshold boundary.
- Add positive, negative, missing-field and threshold-edge tests.
- Review proposed required certificates and dependency chain against official issuing-authority checklists.
- Require named reviewer, ticket, timestamp, rule version and source hashes.
- Publish atomically; support rollback and mark superseded rules as retired.
