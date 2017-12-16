.DEFAULT_GOAL := default

default: 
	chmod +x *.py
	pip3 install --user simplejson
	pip3 install --user html2text
	pip3 install --user porter
	pip3 install --user --upgrade nltk
	python3 -m nltk.downloader punkt
	ln -sf main.py antispam

