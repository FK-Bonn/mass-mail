#! /usr/bin/env python3
import argparse
import email
import imaplib
import json
import time
from csv import DictReader
from email.message import EmailMessage
from getpass import getpass
from pathlib import Path
from smtplib import SMTP
from time import sleep
from typing import List, Dict, Optional

CONFIG_FILE = Path(__file__).with_name('config.json')
LAST_DRY_RUN_FILE = Path(__file__).with_name('.last-dry-run')

PERMISSION_NAMES = {
    'read_files': '👀 Dateien anzeigen',
    'read_permissions': '👀 Berechtigungen anzeigen',
    'write_permissions': '✏️ Berechtigungen ändern',
    'read_public_data': '👀 FS-Daten anzeigen',
    'write_public_data': '✏️ FS-Daten ändern',
    'read_protected_data': '👀 geschützte FS-Daten anzeigen',
    'write_protected_data': '️✏️ geschützte FS-Daten ändern',
    'submit_payout_request': '️✏️ Anträge stellen',
    'locked': '🔒 Rechte-Bearbeitung nur durch FSK',
}

class DryRunBeforeActualRunException(Exception):
    pass


def check_last_dry_run():
    if LAST_DRY_RUN_FILE.is_file():
        last_run = float(LAST_DRY_RUN_FILE.read_text())
        now = time.time()
        if now - (30 * 60) < last_run:
            return
    msg = 'You gotta do a dry run before doing the actual run 🙈🙈🙈'
    raise DryRunBeforeActualRunException(msg)


def write_last_dry_run():
    now = time.time()
    LAST_DRY_RUN_FILE.write_text(str(now))


class Mail:
    def __init__(self, config: Dict, dry_run: Optional[Path]):
        self.dry_run = dry_run
        self.mail_user = config['mail_user']
        if dry_run:
            write_last_dry_run()
        else:
            check_last_dry_run()
            # considering the same user and pass for smtp an imap
            self.mail_pass = getpass()
            self.mail_host = config['mail_host']
            self.smtp = self.setup_smtp()
            self.imap = self.setup_imap()

    def setup_smtp(self):
        if self.dry_run:
            return
        smtp = SMTP(self.mail_host, port=587)
        smtp.starttls()
        smtp.login(self.mail_user, self.mail_pass)
        return smtp

    def setup_imap(self):
        if self.dry_run:
            return
        imap = imaplib.IMAP4_SSL(self.mail_host, 993)
        imap.login(self.mail_user, self.mail_pass)
        return imap

    def logout(self):
        if self.dry_run:
            return
        self.smtp.quit()
        self.imap.logout()

    def send_email(self, from_name: str, to: str, subject: str, body: str, fs_id: str):
        message = EmailMessage()
        message.set_content(body, charset='utf-8', cte='quoted-printable')
        message["From"] = f"{from_name} <{self.mail_user}>"
        message["To"] = to
        message["Subject"] = subject
        message["Date"] = email.utils.formatdate()

        text = message.as_string()

        if self.dry_run:
            self.dry_run.mkdir(parents=True, exist_ok=True)
            target_file = self.dry_run / f'{fs_id}.eml'
            target_file.write_text(text)
        else:
            self.smtp.send_message(message)
            self.imap.append('Sent', '\\Seen', imaplib.Time2Internaldate(time.time()), text.encode('utf8'))


def has_any_permission(permissions: dict):
    for key, substitution in PERMISSION_NAMES.items():
        if permissions[key]:
            return True
    return False


def format_permissions(permissions_json):
    data = json.loads(permissions_json)
    formatted = ''
    for permissions in sorted(data, key=lambda x: x['username']):
        if has_any_permission(permissions):
            formatted += f'» {permissions["username"]}:\n'
            for key, substitution in PERMISSION_NAMES.items():
                if permissions[key]:
                    formatted += f'  {substitution}\n'
            formatted += '\n'
    return formatted


def load_data(data_file: Path) -> List[Dict]:
    elements = []
    with data_file.open() as f:
        reader = DictReader(f, delimiter='\t')
        for line in reader:
            if 'permissions_json' in line:
                line['permissions'] = format_permissions(line['permissions_json'])
            elements.append(line)
    return elements


def load_template(template: Path):
    template_lines = template.read_text().splitlines(keepends=False)
    assert template_lines[0] != ''
    assert template_lines[1] == ''
    assert template_lines[2] != ''
    return template_lines[0], '\n'.join(template_lines[2:])


def load_config() -> Dict:
    return json.loads(CONFIG_FILE.read_text())


def main():
    args = parse_args()
    data = load_data(args.fs_data)
    subject_template, body_template = load_template(args.template)
    config = load_config()

    m = Mail(config, args.dry_run)
    for line in data:
        recipients = line['addresses']
        fs_id = line['fs_id']
        subject = subject_template.format(**line)
        body = body_template.format(**line)
        m.send_email(config['from_name'], recipients, subject, body, fs_id)
        print(f'Sent "{subject}" to "{recipients}"')
        if not args.dry_run:
            sleep(5)
    m.logout()
    print('done.')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('fs_data', type=Path)
    parser.add_argument('template', type=Path)
    parser.add_argument('--dry-run', type=Path)
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main()
