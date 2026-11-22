# Email Automation

A Python command-line tool that builds a report from a CSV file and emails it as an attachment. It uses only the Python standard library.

## Features

- Reads a CSV file and builds a plain-text summary report (row count, plus total, average, minimum and maximum for every numeric column)
- Creates an email with the report attached
- Sends to one or more recipients
- Previews by default: the email is saved as a `.eml` file and nothing is sent until `--send` is used
- Sends over SMTP with STARTTLS
- Reads credentials from environment variables, or asks for them when they are missing
- Clear error messages for unreadable or empty CSV files and for failed sending
- Includes tests that never send an email

## Working

`main.py` connects two modules and runs them in order:

1. `reporting.py` reads the CSV file and builds the report
2. `mailer.py` creates the email with the report attached, then saves a preview or sends it

## How to run

Requires Python 3.10 or newer.

```
python main.py sales.csv --to you@example.com
python main.py sales.csv --to you@example.com --send
```

`sales.csv` is a small sample file included in the project.

Options:

- `--to`: one or more recipient addresses (required)
- `--send`: send the email instead of saving a preview
- `--host`: SMTP server (default: `smtp.gmail.com`)
- `--port`: SMTP port, connects with STARTTLS (default: `587`)

Put `--to` after the CSV file name.

## Credentials

Sending reads the `EMAIL_USER` and `EMAIL_PASSWORD` environment variables and asks for any that are missing. Never put a password in the code.

Gmail requires an app password, which needs 2-step verification on the account. When testing, send only to your own address.

## Help

To see all arguments, run:

```
python main.py --help
```

## How to run the tests

```
pip install pytest
python -m pytest
```

## Notes

- A preview does not need credentials. Its sender address is a placeholder.
- Only numeric columns appear in the report. Columns with text or dates are skipped.

## Coming later

- Templates and HTML emails
- Scheduled sending
- Logging
- Organizing incoming email