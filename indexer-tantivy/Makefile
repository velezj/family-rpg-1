.ONESHELL:

.PHONY: all

all: SHELL := /usr/bin/fish
all: venv
	./build-session-indices.fish ../../session-recordings/google-speech-to-text/ ../march-2021/


venv: SHELL := /usr/bin/fish
venv:
	python3.7 -m venv venv
	source venv/bin/activate.fish
	pip install -r requirements.txt


clean:
	rm -rf venv
	rm -rf session-index-001
	rm -rf temp_lines.dump
