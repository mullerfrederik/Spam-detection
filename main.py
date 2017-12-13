#!/usr/bin/env python3

import sys
import eml_parser
import simplejson as json
import datetime

def emailsToAnalyze():

    emails = []

    if len (sys.argv) != 2:
        print ('Usage: ./antispam email.eml email2.eml email3.eml email4.eml"')
        sys.exit (1)

    for email in sys.argv[1:]:
        emails.append(email)

    return emails

def json_serial(obj):
    if isinstance(obj, datetime.datetime):
        serial = obj.isoformat()
        return serial

def parseEmails(emails):

    parsedEmails = []

    for email in emails:

        try:
            with open(email, 'rb') as fhdl:
                raw_email = fhdl.read()
        except OSError:
            print('Cannot read file')
            sys.exit (1)

        parsed_eml = eml_parser.eml_parser.decode_email_b(raw_email)

        parsedEmails.append({email: parsed_eml})

    return parsedEmails

def main():

    emails = emailsToAnalyze()
    print(emails)

    parsedEmails = parseEmails(emails)


    for parsedEmail in parsedEmails:

        for key, value in parsedEmail.items():
            print(key)
            # print(eml_parser.eml_parser.parse_email(value))
            print(json.dumps(value, default=json_serial))

if __name__ == "__main__":
    main()
