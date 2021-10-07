.ONESHELL:
.PHONY: all

all: SHELL := /usr/bin/fish
all:
	rm -rf venv
	python3 -m venv venv
	source venv/bin/activate.fish
	pip install -r requirements.txt
	./build-session-indices.fish ../../session-recordings/google-speech-to-text/ ../march-2021/
