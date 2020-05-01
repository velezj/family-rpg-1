#!/bin/bash

pandoc --css pandoc.css --from markdown --to html5 --standalone $*
