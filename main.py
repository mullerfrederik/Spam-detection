#!/usr/bin/env python3
# Frederik Muller 
# FIT VUT Brno
# Projekt BIS 
# Antispam -- machine learning

import sys
import email
import html2text
import os
import nltk
from nltk.tokenize import word_tokenize
import re
import porter
import random
from nltk import NaiveBayesClassifier
from email.header import decode_header
import pickle
import gzip

def emailsToAnalyze():

    emails = []

    if len (sys.argv) < 2:
        print ('Usage: ./antispam email.eml email2.eml email3.eml email4.eml"')
        sys.exit(1)

    for mail in sys.argv[1:]:
        emails.append(mail)

    return emails

def parseEmails(emails):

    parsedEmails = []

    for mail in emails:

        if ".DS_Store" in mail: 
            continue

        try:
            with open(mail, 'r', encoding="latin-1") as file:
                raw_email = file.read()
        except OSError:
            parsedEmails.append({mail: None})
            continue

        suplementarCharset = ""
        message = email.message_from_string(raw_email)
        if message['Content-Type'] is None:
            charset = 'iso-8859-2'
            suplementarCharset = 'utf-8'
        elif 'charset="iso-8859-2"' in message['Content-Type']:
            charset = 'iso-8859-2'
            suplementarCharset = 'utf-8'
        elif 'charset=UTF-8' in message['Content-Type']:
            charset = 'utf-8'
            suplementarCharset = 'iso-8859-2'
        else:
            charset = 'utf-8'
            suplementarCharset = 'iso-8859-2'

        subject = message["Subject"]
        if subject is None:
            subject = ""
        else:
            try:
                subject = decode_header(subject)[0][0].decode(charset)
            except:
                try:
                    subject = decode_header(subject)[0][0].decode(suplementarCharset)
                except:
                    subject = decode_header(subject)[0][0]

        body = ""

        if message.is_multipart():
            for part in message.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get('Content-Disposition'))
                if ctype == 'text/plain' and 'attachment' not in cdispo:
                    try:
                        body += part.get_payload(decode=True).decode(charset)
                    except:
                        try:
                            body += part.get_payload(decode=True).decode(suplementarCharset)
                        except:
                            body += part.get_payload()
                    break
        else:
            try:
                body += message.get_payload(decode=True).decode(charset)
            except:
                try:
                    body += message.get_payload(decode=True).decode(suplementarCharset)
                except:
                    body += message.get_payload()

        ## we do not care about HTML things
        text_maker = html2text.HTML2Text()
        text_maker.single_line_break = True
        text_maker.ignore_links = True
        text_maker.body_width = 0
        text_maker.ignore_images = True
        text_maker.ignore_emphasis = True
        bodyText = text_maker.handle(body)

        parsedEmails.append({mail: subject + " " + bodyText})

    return parsedEmails

def createFeatures(message):
    newDict = dict([(word, True) for word in message] )
    return newDict

def getAllEmails(directory):
    filesPath = []
    for subdir, dirs, files in os.walk(directory):
        for file in files:
            filepath = subdir + os.sep + file

            filesPath.append(filepath)
    return filesPath


def normalize(string):
    normalized = re.sub(r'\{.*?\}', '', string)
    normalized = re.sub(r'[?\n\.!,():"]', '', normalized)
    normalized = re.sub(r'\b[\w\-.]+?@\w+?\.\w{2,4}\b', 'emailaddr', normalized)
    normalized = re.sub(r'(http[s]?\S+)|(\w+\.[A-Za-z]{2,4}\S*)', 'httpaddr', normalized)
    normalized = re.sub(r'£|\$|€', 'moneysymb', normalized)
    normalized = re.sub(r'\b(\+\d{1,2}\s)?\d?[\-(.]?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b', 'phonenumbr', normalized)
    normalized = re.sub(r'\d+(\.\d+)?', 'numbr', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = re.sub(r'^\s+|\s+?$', '', normalized.lower())
    normalized = normalized.replace('``', '')
    return normalized

def prepareForBoyson(emails, string):

    emailList = []

    for mail in emails:
        for mailLocation, message in mail.items():
            words = word_tokenize(normalize(message))
            emailList.append((createFeatures(words), string))

    return emailList

def validate(hamList, spamList):
    mixedList = hamList + spamList
    random.shuffle(mixedList)
    trainingPart = int(len(mixedList) * 0.8)
    trainingSet = mixedList[:trainingPart]
    testSet = mixedList[trainingPart:]
    classifier = NaiveBayesClassifier.train(trainingSet)
    accuracy = nltk.classify.util.accuracy(classifier, testSet)
    print("accuracy: " + str(accuracy * 100) + "%")
    classifier.show_most_informative_features(20)

def trainData():

    hamEmailsFiles = getAllEmails('email_database/ham/')
    parsedHamEmails = parseEmails(hamEmailsFiles)
    hamList = prepareForBoyson(parsedHamEmails, "ham")

    spamEmailsFiles = getAllEmails('email_database/spam/')
    parsedSpamEmails = parseEmails(spamEmailsFiles)
    spamList = prepareForBoyson(parsedSpamEmails, "spam")

    # validate(hamList, spamList)

    trainingSet = hamList + spamList

    classifier = NaiveBayesClassifier.train(trainingSet)

    classifierFile = gzip.open('classifier.gzip', 'wb')
    pickle.dump(classifier, classifierFile)
    classifierFile.close()

def categorize(probabilities):
    if probabilities.prob('spam') > 0.8:
        return 'SPAM'
    else:
        return 'OK'

def main():

    # trainData()

    emailsFiles = emailsToAnalyze()

    parsedEmails = parseEmails(emailsFiles)

    classifierFile = gzip.open('classifier.gzip', 'rb')
    classifier = pickle.load(classifierFile)
    classifierFile.close()

    for parsedEmail in parsedEmails:

        for mailLocation, message in parsedEmail.items():
            if message is None:
                print(mailLocation + " - FAIL")
                continue
            words = word_tokenize(normalize(message))
            features = createFeatures(words)
            print(mailLocation + " - " + categorize(classifier.prob_classify(features)))


if __name__ == "__main__":
    main()
