"""Offline safety/regression tests; no real passwords or network access."""
import contextlib
import imaplib
import io
import json
import smtplib
import ssl
import unittest
from unittest.mock import patch

from operations import check_mail_connection as mail


class ConnectionTests(unittest.TestCase):
    def setUp(self):
        self.imap_patch = patch.object(mail.imaplib, "IMAP4_SSL")
        self.smtp_patch = patch.object(mail.smtplib, "SMTP_SSL")
        self.imap_factory = self.imap_patch.start()
        self.smtp_factory = self.smtp_patch.start()
        self.addCleanup(self.imap_patch.stop)
        self.addCleanup(self.smtp_patch.stop)
        self.imap = self.imap_factory.return_value
        self.imap.login.return_value = ("OK", [b"do not log this"])
        self.imap.select.return_value = ("OK", [b"9876"])
        self.secret = "fictional-offline-test-password-not-a-real-credential"

    def run_valid(self):
        return mail.run_check({mail.SECRET_NAME: self.secret})

    def test_missing_secret_blocks_without_network(self):
        report, code = mail.run_check({})
        self.assertEqual(code, 2)
        self.assertEqual(report["reason"], "missing_mailbox_secret")
        self.imap_factory.assert_not_called()
        self.smtp_factory.assert_not_called()

    def test_empty_secret_blocks_without_network(self):
        report, code = mail.run_check({mail.SECRET_NAME: ""})
        self.assertEqual(code, 2)
        self.imap_factory.assert_not_called()
        self.smtp_factory.assert_not_called()

    def test_success_reports_only_authentication(self):
        report, code = self.run_valid()
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "authenticated")
        self.assertFalse(report["mail_sent"])
        self.assertFalse(report["mail_content_read"])
        self.assertFalse(report["settings_changed"])
        self.assertFalse(report["automation_enabled"])
        self.assertIn("does not connect ChatGPT", " ".join(report["limitations"]))

    def test_fixed_destinations_accounts_ports_and_timeout(self):
        self.run_valid()
        self.assertEqual(self.imap_factory.call_args.args, ("mail.zxcs.nl", 993))
        self.assertEqual(self.smtp_factory.call_args.args, ("mail.zxcs.nl", 465))
        self.assertEqual(self.imap_factory.call_args.kwargs["timeout"], 12)
        self.imap.login.assert_called_once_with("info@avenzodigital.nl", self.secret)
        self.smtp_factory.return_value.login.assert_called_once_with("info@avenzodigital.nl", self.secret)

    def test_environment_cannot_override_account_or_destination(self):
        mail.run_check({mail.SECRET_NAME: self.secret, "SMTP_HOST": "attacker.invalid", "IMAP_HOST": "attacker.invalid", "MAILBOX": "other@example.invalid"})
        self.assertEqual(self.imap_factory.call_args.args[0], mail.HOST)
        self.assertEqual(self.smtp_factory.call_args.args[0], mail.HOST)
        self.imap.login.assert_called_once_with(mail.MAILBOX, self.secret)

    def test_inbox_is_readonly_and_no_message_operations(self):
        self.run_valid()
        self.imap.select.assert_called_once_with("INBOX", readonly=True)
        self.assertEqual([call[0] for call in self.imap.method_calls], ["login", "select", "logout"])
        self.assertEqual([call[0] for call in self.smtp_factory.return_value.method_calls], ["login", "quit"])

    def test_certificate_and_hostname_verification_enforced(self):
        self.run_valid()
        contexts = [self.imap_factory.call_args.kwargs["ssl_context"], self.smtp_factory.call_args.kwargs["context"]]
        for ctx in contexts:
            self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)
            self.assertTrue(ctx.check_hostname)
            self.assertGreaterEqual(ctx.minimum_version, ssl.TLSVersion.TLSv1_2)

    def test_password_and_provider_output_absent_from_report(self):
        report, _ = self.run_valid()
        text = json.dumps(report)
        self.assertNotIn(self.secret, text)
        self.assertNotIn("do not log this", text)
        self.assertNotIn("9876", text)

    def test_failed_imap_auth_is_redacted_and_smtp_skipped(self):
        self.imap.login.side_effect = imaplib.IMAP4.error(self.secret)
        report, code = self.run_valid()
        self.assertEqual(code, 1)
        self.assertNotIn(self.secret, json.dumps(report))
        self.smtp_factory.assert_not_called()
        self.imap.logout.assert_called_once()

    def test_explicit_login_failure(self):
        self.imap.login.return_value = ("NO", [self.secret.encode()])
        report, code = self.run_valid()
        self.assertEqual(code, 1)
        self.assertEqual(report["imap"], "authentication_failed")
        self.imap.select.assert_not_called()
        self.smtp_factory.assert_not_called()

    def test_unavailable_inbox_is_not_success(self):
        self.imap.select.return_value = ("NO", [b"sensitive server text"])
        report, code = self.run_valid()
        self.assertEqual(code, 1)
        self.assertEqual(report["imap"], "inbox_unavailable")
        self.smtp_factory.assert_not_called()
        self.imap.logout.assert_called_once()

    def test_tls_certificate_failure_never_retries_insecurely(self):
        self.imap_factory.side_effect = ssl.SSLCertVerificationError(1, self.secret)
        report, code = self.run_valid()
        self.assertEqual(code, 1)
        self.assertEqual(report["imap"], "certificate_verification_failed")
        self.imap_factory.assert_called_once()
        self.smtp_factory.assert_not_called()
        self.assertNotIn(self.secret, json.dumps(report))

    def test_timeout_is_failure_without_provider_error(self):
        self.imap_factory.side_effect = TimeoutError(self.secret)
        report, code = self.run_valid()
        self.assertEqual(code, 1)
        self.assertEqual(report["imap"], "connection_failed")
        self.assertNotIn(self.secret, json.dumps(report))

    def test_smtp_auth_failure_is_not_success(self):
        self.smtp_factory.return_value.login.side_effect = smtplib.SMTPAuthenticationError(535, self.secret.encode())
        report, code = self.run_valid()
        self.assertEqual(code, 1)
        self.assertEqual(report["status"], "failed")
        self.assertNotIn(self.secret, json.dumps(report))
        self.smtp_factory.return_value.quit.assert_called_once()

    def test_smtp_cleanup_exception_is_redacted_and_socket_closed(self):
        self.smtp_factory.return_value.quit.side_effect = RuntimeError(self.secret)
        report, code = self.run_valid()
        self.assertEqual(code, 0)
        self.smtp_factory.return_value.close.assert_called_once()
        self.assertNotIn(self.secret, json.dumps(report))

    def test_unexpected_error_is_redacted(self):
        self.imap.login.side_effect = RuntimeError(self.secret)
        report, code = self.run_valid()
        self.assertEqual(code, 1)
        self.assertEqual(report["imap"], "unexpected_failure")
        self.assertNotIn(self.secret, json.dumps(report))

    def test_cli_missing_secret_has_nonzero_exit_and_json_only(self):
        output = io.StringIO()
        with patch.dict(mail.os.environ, {}, clear=True), contextlib.redirect_stdout(output):
            code = mail.main()
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output.getvalue())["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
