#  Copyright (c) 2019.
#  @author Fakhir Khan

import configparser
import logging
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re


class EmailNotify:

    def __init__(self, host, port, recipients: list, credentials_folder_name='.creds', credential_file='email.ini'):
        self.credential_file_path = os.path.join(credentials_folder_name, credential_file)
        if not os.path.isfile(self.credential_file_path):
            self.create_credentials()

        self.credentials = self.read_credentials()

        self.server = smtplib.SMTP(host=host, port=port)
        self.server.ehlo()
        self.server.starttls(context=ssl.create_default_context())
        # self.server.login(user = self._username, password = self._password)
        try:
            self.server.login(user=self.credentials['username'], password=self.credentials['password'])
        except smtplib.SMTPAuthenticationError:
            logging.error('Failed to login with the given credentials')
            os.remove(self.credential_file_path)

        self.recipient = recipients
        self.check_email_addresses()  # this will update the self.recipient variable
        if not self.credentials['username'] in self.recipient and 'no-reply' not in self.credentials['username']:
            self.recipient.insert(0, self.credentials['username'])

    def send_email(self, header, body):

        # _message = 'Subject: {0}\n\n {1}'.format(header, body)
        _message = MIMEMultipart('text')
        _message['Subject'] = header
        _message['To'] = ", ".join(self.recipient)
        # _message['cc'] =
        text = MIMEText(body, 'plain')
        _message.attach(text)

        self.server.sendmail(from_addr=self.credentials['username'],
                             to_addrs=self.recipient,
                             msg=_message.as_string())

    def close_server(self):
        self.server.quit()

    def credential_exist(self):
        return os.path.isfile(self.credential_file_path)

    def read_credentials(self):
        _email_config = configparser.ConfigParser()
        _email_config.read(self.credential_file_path)

        _username = _email_config['Email']['username']
        _password = _email_config['Email']['password']

        _credentials = {'username': _username, 'password': _password}
        return _credentials

    def create_credentials(self):
        _email_config = configparser.ConfigParser()
        _email_config.add_section('Email')
        logging.warning('Credentials are not encrypted and stored in an ini file.')
        _username = input('Enter username for creating credentials : ')
        _password = input('Enter Password for creating credentials : ')

        _email_config.set('Email', 'username', _username)
        _email_config.set('Email', 'password', _password)

        #  Create directory if it doesn't exist
        if not os.path.isdir(os.path.dirname(self.credential_file_path)):
            os.makedirs(os.path.dirname(self.credential_file_path))

        with open(self.credential_file_path, 'w') as _config_file:
            _email_config.write(_config_file)
            logging.warning('Email credential file created. Warning: Credentials are not encrypted')

    def set_senders(self, senders_list):
        self.recipient = senders_list

    def check_email_addresses(self):
        regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
        valid_email_addresses = list()
        for recipient in self.recipient:
            if re.search(regex, recipient):
                valid_email_addresses.append(recipient)
            else:
                logging.warning('Provided recipient is not valid: {}. Removing those from the list'.format(recipient))
        assert len(valid_email_addresses) > 0, 'No Valid Email Addresses left after running the checks. Please check ' \
                                               'recipients and run again '
        self.recipient = valid_email_addresses
