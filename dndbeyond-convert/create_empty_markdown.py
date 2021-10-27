import logging
import pathlib
import re
import sys

template_markdown = """
---
title: {name}
toc-title: Table of Contents
---

# Summary

# History

# Appearance

# Goals

# Hooks

"""

def normalize_name( name ):
    name = re.sub( r"\s+", "-", name )
    name = name.lower()
    return name

def markdown_filename_from_sheet( sheet_filename ):
    return pathlib.Path( sheet_filename ).stem.replace("-sheet","") + ".md"

def is_corresponding_markdown_for_sheet_found( directory,
                                               sheet_filename ):
    markdown_filename = markdown_filename_from_sheet( sheet_filename )
    p = directory / pathlib.Path( markdown_filename )
    return (p.exists(),p)

def parse_human_name_from_sheet( directory, sheet_filename ):
    p = pathlib.Path( directory ) / sheet_filename
    with open( p ) as f:
        for line in f:
            if line.startswith( "|Name |" ):
                toks = line.split("|")
                if len(toks) >= 3:
                    return toks[2].strip()
                break
    return p.stem.replace("-sheet","").title()

def create_empty_markdown_if_needed( directory,
                                     sheet_filename ):
    found, p = is_corresponding_markdown_for_sheet_found( directory,
                                                          sheet_filename )
    if not found:
        human_name = parse_human_name_from_sheet( directory,
                                                  sheet_filename )
        print( "Creating empty template for '{}'".format( human_name ) )
        with open( p, 'w' ) as f:
            f.write( template_markdown.format(name=human_name) )
            f.write( "\n" )
    else:
        print( "Skipping found '{}'".format(p) )


def create_needed_markdowns( directory ):
    for p in pathlib.Path( directory ).glob( "*-sheet.md" ):
        create_empty_markdown_if_needed( directory,
                                         p.name )


if __name__ == "__main__":

    directory = sys.argv[1]
    print( "Creating markdown for missing from sheet pdfs in '{}'".format(
        directory) )
    create_needed_markdowns( directory )
    print( "done" )
