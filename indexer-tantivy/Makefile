.ONESHELL:

.PHONY: all

all: SHELL := /usr/bin/fish
all: index query.sh

index: SHEEL := /usr/bin/fish
index: venv
	./build-session-indices.fish ../../session-recordings/google-speech-to-text/ ../march-2021/


venv: SHELL := /usr/bin/fish
venv:
	python3.7 -m venv venv
	source venv/bin/activate.fish
	pip install -r requirements.txt

query.sh: venv
	echo "#!/bin/bash" > query.sh
	echo "" >> query.sh
	echo 'tantivy search --index session-index-001 --query "$$*"' >> query.sh
	chmod a+x query.sh

clean:
	rm -rf venv
	rm -rf session-index-001
	rm -rf temp_lines.dump
	rm -rf query.sh
