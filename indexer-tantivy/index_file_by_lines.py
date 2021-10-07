import logging
import sys
import tempfile
import json
import subprocess
import pathlib

import spacy
nlp = spacy.load( 'en_core_web_sm' )

def _log():
    return logging.getLogger( __name__ )

def index_file( filename, index_dir ):
    lines = []
    full_json_string = ""
    with tempfile.NamedTemporaryFile() as tempf:
        with open(filename,'r') as f:
            for i, line in enumerate(f):
                line = line.strip()
                doc = nlp(line)
                for idno, sentence in enumerate(doc.sents):
                    jsondata = json.dumps({
                        'filename' : filename,
                        'session_date' : '',
                        'start_audio_time': '',
                        'start_line_number': "{}.{}".format(i,idno),
                        'line' : sentence,
                    })
                    tempf.write( (jsondata + "\n").encode('utf-8') )
                    lines.append( jsondata )
                    full_json_string += jsondata + "\n"
        tempf.flush()
        with open( tempf.name, 'r') as inputf:
            res = subprocess.run(
                [ 'tantivy',
                  'index',
                  '--index',
                  index_dir ],
                stdin=inputf)
        if res.returncode != 0 or True:
            with open( 'temp_lines.dump', 'w') as dumpf:
                for lin in lines:
                    dumpf.write( (lin + "\n") )
        res.check_returncode()


def index_files_batch( index_dir, filenames ):
    lines = []
    with tempfile.NamedTemporaryFile() as tempf:
        for filename in filenames:
            _log().info( "processing file '%s'", filename )
            with open(filename,'r') as f:
                for i, line in enumerate(f):
                    line = line.strip()
                    doc = nlp(line)
                    for idno, sentence in enumerate(doc.sents):
                        jsondata = json.dumps({
                            'filename' : filename,
                            'session_date' : '',
                            'start_audio_time': '',
                            'start_line_number': "{}.{}".format(i,idno),
                            'line' : str(sentence),
                        })
                        tempf.write( (jsondata + "\n").encode('utf-8') )
                        lines.append( jsondata )
        tempf.flush()
        _log().info("Building index in '%s' (#%d lines)", index_dir, len(lines))
        with open( tempf.name, 'r') as inputf:
            res = subprocess.run(
                [ 'tantivy',
                  'index',
                  '--index',
                  index_dir ],
                stdin=inputf)
        if res.returncode != 0 or True:
            with open( 'temp_lines.dump', 'w') as dumpf:
                for lin in lines:
                    dumpf.write( (lin + "\n") )
        res.check_returncode()
            

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    index_dir_path = sys.argv[1]
    filenames = []
    for fn in sys.argv[2:]:
        fn = str(pathlib.Path( fn ).resolve())
        filenames.append( fn )
    _log().info( "Using index '%s'", index_dir_path )
    # for fn in filenames:
    #     _log().info( "Indexing file '%s'", fn )
    #     index_file( fn, index_dir_path )
    index_files_batch( index_dir_path, filenames )
