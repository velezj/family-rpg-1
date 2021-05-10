import logging
import json
import re
import collections
import subprocess
import tempfile
import sys


#####
##### Expecting a pdf decoded and unwrapped by qpdf
##### `qpdf --qdf --decode-level=all X.pdf X_qpdf.pdf
def _process_pdf_through_qpdf( filename, outputfilename ):
    subprocess.run( [ "qpdf",
                      "--qdf",
                      "--decode-level=all",
                      filename,
                      outputfilename ],
                    check=True )


class Chunk( object ):
    def __init__(self, lines, line_start, line_end ):
        self.lines = lines
        self.string = '\n'.join( self.lines )
        self.line_start = line_start
        self.line_end = line_end
    def __str__(self):
        return "Chunk|{0},{1},{2}|".format(
            self.line_start,
            self.line_end,
            self.lines )
    def __repr__(self):
        return self.__str__()

##
# Simple rough grabbing of "objects" in the pdf delimited by
# '<<' and '>>'.  This will only grab the outermost delimiters
# as an abject with many more inside.
# this will not parse out a true pdf element but works for
# the purposes of this script :)
def _parse_pdf_chunks( pdf_raw_data_bytes ):
    chunks = []
    lines = pdf_raw_data_bytes.split(b'\n')
    skip_to = 0
    for i, line in enumerate( lines ):
        if i < skip_to:
            continue
        try:
            line = line.decode( 'utf-8' )
        except Exception:
            line = "😾"
        if line.startswith("<<"):
            chunk_lines = []
            level = 0
            for j, inner_line in enumerate( lines[ i+1: ] ):
                try:
                    inner_line = inner_line.decode( 'utf-8' )
                except Exception:
                    inner_line = "😾"
                if inner_line.strip().startswith('<<'):
                    level += 1
                if inner_line.startswith( ">>" ):
                    if level <= 0:
                        chunks.append( Chunk( chunk_lines, i, j ) )
                        skip_to = j+1
                        break
                    else:
                        level -= 1
                else:
                    chunk_lines.append( inner_line )
    return chunks



class PotentialField( object ):
    def __init__(self, chunk, name, value ):
        self.chunk = chunk
        self.name = name
        self.value = value
    def __str__(self):
        return "Field?( {0} = {1} )".format( self.name, self.value )
    def __repr__(self):
        return self.__str__()


##
# Returns a set of potential fields from a list of chunks
def _compute_potential_fields( chunks ):
    fields = []
    for c in chunks:
        for l in c.lines:
            if '/T ' in l:
                name = l.split('/T ')[-1].strip()
                value = "🍍"
                for l2 in c.lines:
                    if '/V ' in l2:
                        value = l2.split('/V ')[-1].strip()
                        break
                # unwrapped inner utf-16 encoded strings (why?? unclear why they use this)
                if value.startswith('<') and value.endswith('>'):
                    byte_data = bytearray.fromhex( value[1:-1] )
                    value = byte_data.decode( 'utf-16' )
                fields.append( PotentialField( c, name, value ) )
                break
    return fields


##
# normalize a potnetial filed name (removes '(' and ')' enclosures)
def _norm_fieldname( name ):
    name = name.strip()
    if name.startswith("("):
        name = name[1:]
    if name.endswith(")"):
        name = name[:-1]
    name = name.strip()
    #name = name.replace( "<", "&lt;" )
    #name = name.replace( ">", "&gt;" )
    name = name.replace( "<", "{" )
    name = name.replace( ">", "}" )
    name = name.replace( "\\n", "\n" )
    name = name.replace( "\\", "" )
    return name.lower()

##
# Normalize filed values
def _norm_fieldvalue( value ):
    if isinstance( value, str ):
        value = _norm_fieldname( value )
        if len(value) < 1:
            return None
        if value == "--":
            return None
        if value == "🍍":
            return None
    return value

##
# convert a list of fields to a mapping from field name to value
def _field_list_to_map( fields ):
    res = collections.OrderedDict({})
    for f in fields:
        norm_name = _norm_fieldname( f.name )
        norm_value = _norm_fieldvalue( f.value )
        if norm_value is not None:
            res[ norm_name ] = norm_value
    return res

##
# given a spell name, creates the dndbeyong url
def _dndbeyond_url_for_spell( name ):
    if "[" in name:
        name = name[: name.index("[")]
    if "{" in name:
        name = name[: name.index("{")]
    if "<" in name:
        name = name[: name.index("<")]
    name = name.strip()
    name = name.replace( " ", "-" )
    name = name.replace( "/", "-" )
    url = "https://www.dndbeyond.com/spells/{}".format( name )
    return url


##
# Given mediawiki markdown, return the markdown version
def _mediawiki_to_markdown( text ):
    with tempfile.NamedTemporaryFile() as f:
        if isinstance( text, str ):
            text = text.encode( 'utf8' )
        f.write( text )
        f.flush()
        res = subprocess.run( [ "pandoc",
                                "-f", "mediawiki",
                                "-t", "markdown",
                                "-s", f.name ],
                              check=True,
                              capture_output=True)
        return res.stdout.decode( 'utf8' )


##
# Given a set of potential fields,
# output out a "nice" markdown formatted character sheet
def _print_markdown_sheet( out, field_list ):

    # convet from list of fields to dictionary mapping field names
    fields = _field_list_to_map( field_list )

    # character basic info
    out.write( "# Character Basic Info\n\n" )
    out.write( "| | |\n|---|---|\n" )
    out.write( "|Name | {}|\n".format(
        fields.get("charactername","") ))
    out.write( "|Class/Level | {}|\n".format(
        fields.get("class  level","") ))
    out.write( "|Race | {}|\n".format(
        fields.get( "race", "") ))
    out.write( "|Background | {}|\n".format(
        fields.get( "background","" ) ))
    out.write( "\n\n" )

    # Attributes
    out.write( "# Attributes and Stats\n\n" )
    out.write( "**general attributes**\n\n" )
    out.write( "| | |\n" )
    out.write( "|---|---|\n" )
    out.write( "| Initiative | {}|\n".format(
        fields.get( "init", "0" )))
    out.write( "| AC| {}|\n".format(
        fields.get( "ac","" )))
    out.write( "| Prof Bonus| {}|\n".format(
        fields.get( "profbonus", "" )))
    out.write( "| Speed| {}|\n".format(
        fields.get( "speed", "" )))
    out.write( "| Max HP| {}\n".format(
        fields.get( "maxhp", "" )))
    out.write( "| Hit Dice| {}|\n".format(
        fields.get( "total", "" )))
    out.write( "\n\n" )
    out.write( "**base attributes**\n\n" )
    out.write( "| | |\n" )
    out.write( "|---|---|\n" )
    out.write( "|Strength | {} ({})|\n".format(
        fields.get( "str","" ),
        fields.get( "strmod","" )))
    out.write( "|Dexterity | {} ({})|\n".format(
        fields.get( "dex","" ),
        fields.get( "dexmod","" )))
    out.write( "|Constitution | {} ({})|\n".format(
        fields.get( "con","" ),
        fields.get( "conmod","" )))
    out.write( "|Intelligence | {} ({})|\n".format(
        fields.get( "int","" ),
        fields.get( "intmod","" )))
    out.write( "|Wisdom | {} ({})|\n".format(
        fields.get( "wis","" ),
        fields.get( "wismod","" )))
    out.write( "|Charisma | {} ({})|\n".format(
        fields.get( "cha","" ),
        fields.get( "chamod","" )))
    out.write( "\n\n" )
    out.write( "**saving throws**\n\n" )
    out.write( "| | |\n" )
    out.write( "|---|---|\n")
    out.write( "| {}| Strength Saving Throw | {}|\n".format(
        fields.get( "strprof", "" ),
        fields.get( "st strength", "" ) ))
    out.write( "| {}| Dexterity Saving Throw | {}|\n".format(
        fields.get( "dexprof", "" ),
        fields.get( "st dexterity", "" ) ))
    out.write( "| {}| Constitution Saving Throw | {}|\n".format(
        fields.get( "conprof", "" ),
        fields.get( "st constitution", "" ) ))
    out.write( "| {}| Intelligence Saving Throw | {}|\n".format(
        fields.get( "intprof", "" ),
        fields.get( "st intelligence", "" ) ))
    out.write( "| {}| Wisdom Saving Throw | {}|\n".format(
        fields.get( "wisprof", "" ),
        fields.get( "st wisdom", "" ) ))
    out.write( "| {}| Charisma Saving Throw | {}|\n".format(
        fields.get( "chaprof", "" ),
        fields.get( "st charisma", "" ) ))
    out.write( "\n\n" )
    
    skillnames = [ "acrobatics", ("animal","animal handling"), "arcana",
                   "athletics", "deception", "history", "insight",
                   "intimidation", "investigation", "medicine", "nature",
                   "perception", "performance", "persuasion", "religion",
                   "sleightofhand", "stealth", "survival" ]
    out.write( "**skills**\n\n" )
    out.write( "| Prof | Name | Mod | Base |\n" )
    out.write( "|---|---|---|---|\n" )
    for skill in skillnames:
        label = skill
        key = skill
        if isinstance( skill, tuple ):
            key, label = skill
        out.write( "| {}| {}| {}| {}|\n".format(
            fields.get( key + "prof", "" ),
            label,
            fields.get( key, "0" ),
            fields.get( key + "mod", "" ) ) )
    out.write( "\n\n" )

    out.write( "# Actions\n\n" )
    action_numbers = []
    for k in fields.keys():
        if k.startswith("actions"):
            action_numbers.append( k[ len("actions") : ] )
    alltext = ""
    for num in action_numbers:
        key = "actions" + num
        val = fields.get( key )
        if val.startswith( "===" ):
            val = "\n" + val
        alltext += val + "\n"
    alltext = _mediawiki_to_markdown( alltext )
    out.write( alltext )
    out.write( "\n\n" )

    out.write( "# Features/Traits\n\n" )
    feature_numbers = []
    for k in fields.keys():
        if k.startswith( "featurestraits" ):
            feature_numbers.append( k[ len("featurestraits") : ] )
    alltext = ""
    for num in feature_numbers:
        key = "featurestraits" + num
        val = fields.get( key )
        if val.startswith( "===" ):
            val = "\n" + val
        alltext += val + "\n"
    alltext = _mediawiki_to_markdown( alltext )
    out.write( alltext )
    out.write( "\n\n" )

    out.write( "# Proficiencies And Languages\n\n")
    out.write( _mediawiki_to_markdown(
        fields.get( "proficiencieslang", "") + "\n\n" ) )


    # spells
    spell_numbers = []
    spell_headers_for = []
    current_header = ""
    for k,_ in fields.items():
        if k.startswith( "spellheader" ):
            current_header = k[ len("spellheader") : ]
        if k.startswith( "spellname" ):
            spell_numbers.append( k[len("spellname"):] )
            spell_headers_for.append( current_header )
    out.write( "# Spells\n\n" )
    for spell_h in set(spell_headers_for):
        out.write( "**{}**\n".format(
            fields.get( "spellheader" + spell_h )))
        out.write( "{}\n\n".format(
            fields.get( "spellslotheader" + spell_h )))
        for spell_num, spell_header in zip( spell_numbers,
                                            spell_headers_for):
            if spell_header != spell_h:
                continue
            name = fields.get( "spellname" + spell_num )
            url = _dndbeyond_url_for_spell( name )
            out.write( "- <a href=\"{}\">{}</a>\n".format(
                url, name ))
        out.write(  "\n\n" )


    # equipment
    equip_numbers = []
    for name, _ in fields.items():
        if name.startswith( "eq name" ):
            equip_numbers.append( name[len("eq name"):])
    out.write( "# Equipment\n\n" )
    for num in equip_numbers:
        out.write( "- {} (x{})\n".format(
            fields.get( "eq name" + num, "" ),
            fields.get( "eq qty" + num, "" )))
    out.write( "\n\n" )

    # Characteristics
    out.write( "# Characteristics\n\n" )
    out.write( "**Appearance**\n\n" )
    out.write( "Skin: {}\n".format(
        fields.get( "skin", "" ) ) )
    out.write( "Hair: {}\n".format(
        fields.get( "Hair", "" ) ) )
    out.write( "Eyes: {}\n".format(
        fields.get( "Eyes", "" ) ) )
    out.write( fields.get( "appearance", "" ) + "\n\n" )
    out.write( "**Personlaity**\n\n" )
    out.write( fields.get( "personalitytraits", "" ) + "\n\n" )
    out.write( "**Ideals**\n\n" )
    out.write( fields.get( "ideals", "" ) + "\n\n" )
    out.write( "**Bonds**\n\n" )
    out.write( fields.get( "bonds", "" ) + "\n\n" )
    out.write( "**Flaws**\n\n" )
    out.write( fields.get( "flaws","" ) + "\n\n" )

    # background
    out.write( "# Background\n\n" )
    out.write( fields.get( "backstory", "" ) + "\n\n" )

    # notes
    out.write( "# Notes\n\n" )
    note_numbers = []
    for k in fields.keys():
        if k.startswith( "additionalnotes" ):
            note_numbers.append( k[ len("additionalnotes") : ] )
    for num in note_numbers:
        key = "additionalnotes" + num
        out.write( fields.get( key, "" ) + "\n" )
    out.write( "\n\n" )



## ===============================================================

if __name__ == "__main__":

    inputfilename = sys.argv[1]
    outputfilename = sys.argv[2]
    with tempfile.NamedTemporaryFile() as f:
        _process_pdf_through_qpdf( inputfilename,
                                   f.name )
        f.flush()
        data = f.read()
        chunks = _parse_pdf_chunks( data )
        potential_fields = _compute_potential_fields( chunks )
        with open( outputfilename, 'w' ) as outf:
            _print_markdown_sheet( outf, potential_fields )
