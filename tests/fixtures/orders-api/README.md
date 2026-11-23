# orders-api — intentionally flawed test fixture

**Do not deploy or copy this code.** This tiny Express service is a test fixture for ArchProof. It contains deliberate defects (SQL injection, an insecure direct object reference, a non-idempotent payment flow, an unbounded cache, money stored as FLOAT) so that the plugin's findings, validator and PDF builder can be tested end to end.

Nothing here is executed by the plugin: it is only read as source text. It has no dependencies installed and contains no real credentials.
