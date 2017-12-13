#!/usr/bin/env python3

import sys
import simplejson as json
import datetime
import email
import html2text

def emailsToAnalyze():

    emails = []

    if len (sys.argv) != 2:
        print ('Usage: ./antispam email.eml email2.eml email3.eml email4.eml"')
        sys.exit (1)

    for email in sys.argv[1:]:
        emails.append(email)

    return emails

def parseEmails(emails):

    parsedEmails = []

    for mail in emails:

        try:
            with open(mail, 'r', encoding="latin2") as file:
                raw_email = file.read()
        except OSError:
            print('Cannot read file')
            sys.exit (1)

        message = email.message_from_string(raw_email)

        subject = message["Subject"]    
        body = ""

        if message.is_multipart():
            for part in message.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get('Content-Disposition'))
                if ctype == 'text/plain' and 'attachment' not in cdispo:
                    body = part.get_payload(decode=True).decode("latin2") 
                    break
        else:
            body = message.get_payload(decode=True).decode("latin2") 

        text_maker = html2text.HTML2Text()
        text_maker.ignore_links = True
        text_maker.ignore_images = True
        bodyText = text_maker.handle(body)

        parsedEmails.append({mail: subject + "\n" + bodyText})

    return parsedEmails

def main():

    emails = emailsToAnalyze()

    # emails = iterateOverAllEmails()

    print(emails)

    parsedEmails = parseEmails(emails)

    for parsedEmail in parsedEmails:

        for mailLocation, message in parsedEmail.items():
            print(mailLocation)
            print(message)

if __name__ == "__main__":
    main()
