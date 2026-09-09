#!/usr/bin/env python3
"""Check the fixed Avenzo mailbox without reading/sending mail or changing flags.

Standard library only. Credentials are read from AVENZO_MAIL_PASSWORD. The
report contains only predefined status values, never provider error responses,
message counts, headers, message bodies, or credentials. This is a connection
preflight, NOT a ChatGPT connector, delivery test, or scheduled mail worker.
"""
from __future__ import annotations

import imaplib
import json
import os
import smtplib
import ssl
from datetime import datetime, timezone
from typing import Any, Mapping

HOST = "mail.zxcs.nl"
MAILBOX = "info@avenzodigital.nl"
SECRET_NAME = "AVENZO_MAIL_PASSWORD"
TIMEOUT = 12


class CheckFailure(Exception):
    """A fixed, non-sensitive status, rather than a provider error message."""


def tls_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context


def check_imap(password: str) -> None:
    client: Any = None
    try:
        client = imaplib.IMAP4_SSL(
            HOST, 993, ssl_context=tls_context(), timeout=TIMEOUT
        )
        status, _ = client.login(MAILBOX, password)
        if status != "OK":
            raise CheckFailure("authentication_failed")
        # EXAMINE rather than SELECT: do not change seen flags or delete mail.
        status, _ = client.select("INBOX", readonly=True)
        if status != "OK":
            raise CheckFailure("inbox_unavailable")
        # No SEARCH, FETCH, STORE, APPEND, CLOSE or EXPUNGE.
    finally:
        if client is not None:
            try:
                client.logout()
            except Exception:
                pass  # Do not leak provider responses or credentials on cleanup.


def check_smtp(password: str) -> None:
    client: Any = None
    try:
        client = smtplib.SMTP_SSL(
            HOST, 465, context=tls_context(), timeout=TIMEOUT
        )
        # AUTH only. No MAIL FROM, RCPT TO, DATA, sendmail or send_message.
        client.login(MAILBOX, password)
    finally:
        if client is not None:
            try:
                client.quit()
            except Exception:
                try:
                    client.close()
                except Exception:
                    pass


def error_status(error: Exception) -> str:
    if isinstance(error, CheckFailure):
        return str(error)  # Raised only with fixed literals in this module.
    if isinstance(error, ssl.SSLCertVerificationError):
        return "certificate_verification_failed"
    if isinstance(error, ssl.SSLError):
        return "tls_failed"
    if isinstance(error, (imaplib.IMAP4.error, smtplib.SMTPAuthenticationError)):
        return "authentication_or_protocol_failed"
    if isinstance(error, (OSError, TimeoutError)):
        return "connection_failed"
    if isinstance(error, smtplib.SMTPException):
        return "smtp_protocol_failed"
    return "unexpected_failure"


def run_check(environ: Mapping[str, str] | None = None) -> tuple[dict[str, Any], int]:
    source = os.environ if environ is None else environ
    report: dict[str, Any] = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "mailbox": MAILBOX,
        "scope": "IMAP read-only inbox access and SMTP authentication only",
        "status": "blocked",
        "imap": "not_checked",
        "smtp": "not_checked",
        "mail_content_read": False,
        "mail_sent": False,
        "settings_changed": False,
        "automation_enabled": False,
        "limitations": [
            "Successful login does not prove incoming or outgoing delivery.",
            "This check does not connect ChatGPT to the mailbox.",
            "This check does not create, change or validate scheduled follow-up.",
        ],
    }
    password = source.get(SECRET_NAME, "")
    if not password:
        report["reason"] = "missing_mailbox_secret"
        return report, 2
    try:
        check_imap(password)
        report["imap"] = "authenticated_readonly_inbox"
    except Exception as error:
        report["status"] = "failed"
        report["imap"] = error_status(error)
        report["smtp"] = "skipped_after_imap_failure"
        return report, 1
    try:
        check_smtp(password)
        report["smtp"] = "authenticated_no_message_sent"
    except Exception as error:
        report["status"] = "failed"
        report["smtp"] = error_status(error)
        return report, 1
    report["status"] = "authenticated"
    return report, 0


def main() -> int:
    report, exit_code = run_check()
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
