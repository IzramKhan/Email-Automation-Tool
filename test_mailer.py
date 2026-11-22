import smtplib
from datetime import date
from email import message_from_bytes, policy
from unittest.mock import MagicMock, patch

import pytest

import mailer
import main
from mailer import build_message, get_credentials, save_preview, send_message
from reporting import build_report, read_rows

CSV_TEXT = "date,product,quantity,price\n2026-11-01,Notebook,10,2.50\n2026-11-02,Pen,20,0.50\n"


@pytest.fixture
def csv_file(tmp_path):
    path = tmp_path / "sales.csv"
    path.write_text(CSV_TEXT, encoding="utf-8")
    return path


@pytest.fixture
def fake_smtp():
    """Replace the SMTP connection and return the fake server object."""
    server = MagicMock()
    with patch("mailer.smtplib.SMTP") as smtp_class:
        smtp_class.return_value.__enter__.return_value = server
        smtp_class.server = server
        yield smtp_class


# --- reporting ---------------------------------------------------------------


def test_read_rows_returns_one_dictionary_per_row(csv_file):
    rows = read_rows(csv_file)

    assert len(rows) == 2
    assert rows[0] == {"date": "2026-11-01", "product": "Notebook", "quantity": "10", "price": "2.50"}


def test_build_report_summarises_numeric_columns(csv_file):
    report = build_report(read_rows(csv_file))

    assert report.splitlines()[0] == "Rows: 2"
    assert "quantity: total=30.00 average=15.00 min=10.00 max=20.00" in report
    assert "price: total=3.00 average=1.50 min=0.50 max=2.50" in report


def test_build_report_skips_text_and_date_columns(csv_file):
    report = build_report(read_rows(csv_file))

    assert "product:" not in report
    assert "date:" not in report


def test_build_report_ignores_blank_cells_in_numeric_columns():
    rows = [{"amount": "10"}, {"amount": ""}, {"amount": "20"}]

    assert "amount: total=30.00 average=15.00 min=10.00 max=20.00" in build_report(rows)


def test_build_report_with_no_rows():
    assert build_report([]) == "Rows: 0"


# --- mailer ------------------------------------------------------------------


def test_build_message_sets_headers_and_recipients():
    msg = build_message("me@example.com", ["a@example.com", "b@example.com"], "report text")

    assert msg["From"] == "me@example.com"
    assert msg["To"] == "a@example.com, b@example.com"
    assert msg["Subject"] == f"Report {date.today():%d %B %Y}"


def test_build_message_attaches_the_report():
    msg = build_message("me@example.com", ["a@example.com"], "Rows: 2")

    (attachment,) = msg.iter_attachments()
    assert attachment.get_filename() == "report.txt"
    assert attachment.get_content().strip() == "Rows: 2"


def test_save_preview_writes_a_readable_eml_file(tmp_path):
    msg = build_message("me@example.com", ["a@example.com"], "Rows: 2")
    path = tmp_path / "preview.eml"

    save_preview(msg, path)

    parsed = message_from_bytes(path.read_bytes(), policy=policy.default)
    assert parsed["To"] == "a@example.com"
    assert [part.get_filename() for part in parsed.iter_attachments()] == ["report.txt"]


def test_get_credentials_reads_the_environment(monkeypatch):
    monkeypatch.setenv("EMAIL_USER", "me@example.com")
    monkeypatch.setenv("EMAIL_PASSWORD", "secret")

    assert get_credentials() == ("me@example.com", "secret")


def test_get_credentials_asks_when_the_environment_is_empty(monkeypatch):
    monkeypatch.delenv("EMAIL_USER", raising=False)
    monkeypatch.delenv("EMAIL_PASSWORD", raising=False)
    monkeypatch.setattr("builtins.input", lambda prompt: "typed@example.com")
    monkeypatch.setattr(mailer, "getpass", lambda prompt: "typed-secret")

    assert get_credentials() == ("typed@example.com", "typed-secret")


def test_send_message_uses_starttls_login_and_send(fake_smtp):
    msg = build_message("me@example.com", ["a@example.com"], "Rows: 2")

    send_message(msg, "smtp.example.com", 587, "me@example.com", "secret")

    assert fake_smtp.call_args.args == ("smtp.example.com", 587)
    fake_smtp.server.starttls.assert_called_once()
    fake_smtp.server.login.assert_called_once_with("me@example.com", "secret")
    fake_smtp.server.send_message.assert_called_once_with(msg)


# --- main (whole program, nothing is ever sent) ---------------------------------


def test_main_saves_a_preview_and_sends_nothing_by_default(csv_file, tmp_path, monkeypatch, fake_smtp, capsys):
    monkeypatch.chdir(tmp_path)

    assert main.main([str(csv_file), "--to", "a@example.com"]) == 0

    assert (tmp_path / "preview.eml").exists()
    fake_smtp.assert_not_called()
    assert "Nothing was sent" in capsys.readouterr().out


def test_main_sends_with_the_send_flag(csv_file, monkeypatch, fake_smtp, capsys):
    monkeypatch.setenv("EMAIL_USER", "me@example.com")
    monkeypatch.setenv("EMAIL_PASSWORD", "secret")

    exit_code = main.main([str(csv_file), "--to", "a@example.com", "b@example.com", "--send"])

    assert exit_code == 0
    sent = fake_smtp.server.send_message.call_args.args[0]
    assert sent["From"] == "me@example.com"
    assert sent["To"] == "a@example.com, b@example.com"
    assert "Email sent to a@example.com, b@example.com" in capsys.readouterr().out


def test_main_returns_1_when_sending_fails(csv_file, monkeypatch, fake_smtp, capsys):
    monkeypatch.setenv("EMAIL_USER", "me@example.com")
    monkeypatch.setenv("EMAIL_PASSWORD", "wrong")
    fake_smtp.server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"bad credentials")

    assert main.main([str(csv_file), "--to", "a@example.com", "--send"]) == 1
    assert "could not send" in capsys.readouterr().err


def test_main_returns_1_when_the_csv_file_is_missing(tmp_path, capsys):
    assert main.main([str(tmp_path / "missing.csv"), "--to", "a@example.com"]) == 1
    assert "could not read" in capsys.readouterr().err


def test_main_returns_1_when_the_csv_file_has_no_data(tmp_path, capsys):
    empty = tmp_path / "empty.csv"
    empty.write_text("date,product,quantity\n", encoding="utf-8")

    assert main.main([str(empty), "--to", "a@example.com"]) == 1
    assert "no data rows" in capsys.readouterr().err


def test_main_requires_a_recipient(csv_file):
    with pytest.raises(SystemExit) as error:
        main.main([str(csv_file)])

    assert error.value.code == 2