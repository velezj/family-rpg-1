import logging
import json
import re


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

