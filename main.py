#!/usr/bin/env python3

import sys
import simplejson as json
import datetime
import email
import html2text
import os
import nltk
from nltk.tokenize import word_tokenize
import re
import porter

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

        print(mail)

        if ".DS_Store" in mail: 
            continue

        try:
            with open(mail, 'r', encoding="latin2") as file:
                raw_email = file.read()
        except OSError:
            print('Cannot read file')
            sys.exit (1)

        message = email.message_from_string(raw_email)

        subject = message["Subject"]
        if subject is None:
            subject = ""

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

def create_word_features(words):
    my_dict = dict( [ (word, True) for word in words] )
    return my_dict

def getAllEmails(directory):
    filesPath = []
    for subdir, dirs, files in os.walk(directory):
        for file in files:
            filepath = subdir + os.sep + file

            filesPath.append(filepath)
    return filesPath


stop_words = nltk.corpus.stopwords.words('english')
porter = nltk.PorterStemmer()
# Normalization http://inmachineswetrust.com/posts/sms-spam-filter/
def normalize(string):
    normalized = re.sub(r'\b[\w\-.]+?@\w+?\.\w{2,4}\b', 'emailaddr', string)
    normalized = re.sub(r'(http[s]?\S+)|(\w+\.[A-Za-z]{2,4}\S*)', 'httpaddr', normalized)
    normalized = re.sub(r'£|\$', 'moneysymb', normalized)
    normalized = re.sub(r'\b(\+\d{1,2}\s)?\d?[\-(.]?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b', 'phonenumbr', normalized)
    normalized = re.sub(r'\d+(\.\d+)?', 'numbr', normalized)
    normalized = re.sub(r'[^\w\d\s]', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = re.sub(r'^\s+|\s+?$', '', normalized.lower())
    return ' '.join(porter.stem(term) for term in normalized.split() if term not in set(stop_words))

def prepareForBoyson(emails, string):

    emailList = []

    for mail in emails:
        for mailLocation, message in mail.items():
            words = word_tokenize(normalize(message))
            emailList.append((create_word_features(words), string))

    return emailList


def trainData():

    hamEmailsFiles = getAllEmails('examples/ham/')
    parsedHamEmails = parseEmails(hamEmailsFiles)
    hamList = prepareForBoyson(parsedHamEmails, "ham")

    spamEmailsFiles = getAllEmails('examples/spam/')
    parsedSpamEmails = parseEmails(spamEmailsFiles)
    spamList = prepareForBoyson(parsedHamEmails, "spam")

    print(hamList)
    print(spamList)

def main():

    trainData()
    
    # parsedEmails = parseEmails(emails)

    # for parsedEmail in parsedEmails:

    #     for mailLocation, message in parsedEmail.items():
    #         print(mailLocation)
    #         print(message)

if __name__ == "__main__":
    main()
