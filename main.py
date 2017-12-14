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
import random
from nltk import NaiveBayesClassifier
from email.header import decode_header
import pickle

def emailsToAnalyze():

    emails = []

    if len (sys.argv) != 2:
        print ('Usage: ./antispam email.eml email2.eml email3.eml email4.eml"')
        sys.exit(1)

    for mail in sys.argv[1:]:
        emails.append(mail)

    return emails

def parseEmails(emails):

    parsedEmails = []

    for mail in emails:

        print(mail)

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
                        body = part.get_payload(decode=True).decode(charset)
                    except:
                        body = part.get_payload(decode=True).decode(suplementarCharset)
                    break
        else:
            try:
                body = message.get_payload(decode=True).decode(charset)
            except:
                body = message.get_payload(decode=True).decode(suplementarCharset)

        # move to normalize?
        text_maker = html2text.HTML2Text()
        text_maker.single_line_break = True
        text_maker.ignore_links = True
        text_maker.body_width = 0
        text_maker.ignore_images = True
        text_maker.ignore_emphasis = True
        bodyText = text_maker.handle(body)

        parsedEmails.append({mail: subject + " " + bodyText})

    return parsedEmails

def createWordFeatures(words):
    my_dict = dict( [ (word, True) for word in words] )
    return my_dict

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
    normalized = re.sub(r'£|\$', 'moneysymb', normalized)
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
            emailList.append((createWordFeatures(words), string))

    return emailList


def trainData():

    hamEmailsFiles = getAllEmails('email_database/ham/')
    parsedHamEmails = parseEmails(hamEmailsFiles)
    hamList = prepareForBoyson(parsedHamEmails, "ham")


    spamEmailsFiles = getAllEmails('email_database/spam/')
    parsedSpamEmails = parseEmails(spamEmailsFiles)
    spamList = prepareForBoyson(parsedSpamEmails, "spam")
    combinedList = hamList + spamList

    # random.shuffle(combinedList)


    # trainingPart = int(len(combinedList) * .7)

    trainingSet = combinedList # trainingSet = combinedList[:trainingPart]

    # testSet = combinedList[trainingPart:]

    # print (len(trainingSet))
    # print (len(testSet))

    classifier = NaiveBayesClassifier.train(trainingSet)

    # accuracy = nltk.classify.util.accuracy(classifier, testSet)

    # print("Accuracy is: ", accuracy * 100)

    classifier.show_most_informative_features(20)

    model = open('my_classifier.pickle', 'wb')
    pickle.dump(classifier, model)
    model.close()

def categorize(probabilities):
    print(probabilities)
    print(probabilities.samples())
    print('ham: ' + str(probabilities.prob('ham')))
    print('spam: ' + str(probabilities.prob('spam')))
    if probabilities.prob('spam') > 0.95:
        return 'SPAM'
    else:
        return 'OK'

def main():

    # trainData()

    # exit(0)

    model = open('my_classifier.pickle', 'rb')
    classifier = pickle.load(model)
    model.close()
    
    emailsFiles = emailsToAnalyze()

    parsedEmails = parseEmails(emailsFiles)


    for parsedEmail in parsedEmails:

        for mailLocation, message in parsedEmail.items():
            if message is None:
                print(mailLocation + " - FAIL")
                continue
            words = word_tokenize(normalize(message))
            print(words)
            features = createWordFeatures(words)
            print(mailLocation + " - " + categorize(classifier.prob_classify(features)))


if __name__ == "__main__":
    main()
