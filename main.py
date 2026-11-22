"""Command-line entry point: build a report from a CSV file and email it."""

import argparse
import csv
import smtplib
import sys

from mailer import build_message, get_credentials, save_preview, send_message
from reporting import build_report, read_rows

PREVIEW_PATH = "preview.eml"
PREVIEW_SENDER = "sender@example.com"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a report from a CSV file and email it. "
            "By default the email is only saved as a preview; use --send to send it."
        )
    )
    parser.add_argument("csv_file", help="path to the CSV file")
    parser.add_argument(
        "--to",
        nargs="+",
        required=True,
        metavar="ADDRESS",
        help="one or more recipient addresses",
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="send the email instead of saving a preview",
    )
    parser.add_argument(
        "--host", default="smtp.gmail.com", help="SMTP server (default: %(default)s)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=587,
        help="SMTP port, connects with STARTTLS (default: %(default)s)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        rows = read_rows(args.csv_file)
    except (OSError, UnicodeDecodeError, csv.Error) as error:
        print(f"Error: could not read {args.csv_file}: {error}", file=sys.stderr)
        return 1
    if not rows:
        print("Error: the CSV file has no data rows", file=sys.stderr)
        return 1

    report = build_report(rows)

    if not args.send:
        save_preview(build_message(PREVIEW_SENDER, args.to, report), PREVIEW_PATH)
        print(f"Preview saved to {PREVIEW_PATH}. Nothing was sent; use --send to send it.")
        return 0

    user, password = get_credentials()
    msg = build_message(user, args.to, report)
    try:
        send_message(msg, args.host, args.port, user, password)
    except (smtplib.SMTPException, OSError) as error:
        print(f"Error: could not send the email: {error}", file=sys.stderr)
        return 1

    print(f"Email sent to {', '.join(args.to)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())