"""
careersarthi.utils
────────────────────
Shared, security-relevant utilities used by every agent:

  • pii_redactor – strips PII from text before it reaches an LLM call
  • audit_log     – append-only JSON-lines record of every agent action
  • storage       – encrypted SQLite store for applications + a generic kv cache
"""
