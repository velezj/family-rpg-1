import logging
import re
import time
import sys
import random

import bs4
import requests


##
# The webpage is assumed to have been saved using the **WebDeveloper**
# tools. Inspector->HTML->Right Click->Cpy->Copy Outer HTML-> Paste into doc

##
# Note: the charater *must* have been previsouly exported to pdf. So I
# suggest you simply automatically hit export when you create a
# new character and don't bother saving hte resulting pdf since this
# script will grab it and all others in a batch with sane names.


##
# This is the request headers taken from a sample request to export a character.
# Get this by:
# 1) Go to a character sheet
# 1b) Hit the "Preferences" to get the sidebar with export menu item
# 2) turn on developer tools
# 3) Go to network tab in developer tools
# 4) click on "Export to Pdf"
# 5) Check the POST request and grab those headers
POST_REQUEST_SNIFF = {
    
}


def _log():
    return logging.getLogger( __name__ )

## =====================================================================

def find_character_urls_and_ids( html ):
    url_regex = re.compile( r"jplankton/characters/(\d+)",
                            re.MULTILINE )
    matches = re.findall( url_regex, html )
    ids = []
    for m in matches:
        #_log().info( "match: %s", m )
        ids.append( m )
    ids = set(ids)
    urls = [
        ( x, "https://www.dndbeyond.com/profile/jplankton/characters/" + x )
        for x in ids ]
    return urls


## =====================================================================

def find_character_info( html, urls ):
    names = {}
    doc = bs4.BeautifulSoup( html, 'html.parser' )
    for (cid,u) in urls:
        thunk = doc.find( "a", href=u )
        topdiv = thunk.parent
        namediv = topdiv.find( "div", "ddb-campaigns-character-card-header-upper-character-info-primary" )
        names[ namediv.string ] = "https://www.dndbeyond.com/sheet-pdfs/jplankton_{}.pdf".format( cid )
    return names

## =====================================================================

def normalize_name( name ):
    name = re.sub( r"\s+", "-", name )
    name = name.lower()
    return name

## =====================================================================

def fetch_all_characters( dom_html_filename, output_directory, wait_time=(10.0, 20.0 ) ):
    dom_html = None
    with open( dom_html_filename ) as f:
        dom_html = f.read()
    urls = find_character_urls_and_ids( dom_html )
    names = find_character_info( dom_html, urls )
    success_infos  = []
    failed_infos = []
    for name, url in names.items():
        print( "Fetching '{}' ... ".format( name ), end="" )
        sys.stdout.flush()
        r = requests.get( url )
        name = normalize_name( name )
        output_filename = "{}/{}.pdf".format( output_directory, name )
        if len(r.content) > 100000:
            with open( output_filename, 'wb' ) as fout:
                fout.write( r.content )
                success_infos.append( (name,url) )
        else:
            failed_infos.append( (name,url) )
            print( " *FAILED* ", end="" )
        print( "done" )
        to_wait = random.randrange( *wait_time )
        time.sleep( to_wait )

    if len(failed_infos) > 0:
        print( "" )
        print( "------------------------------------" )
        print( "FAILED Characters:" )
        for i, info in enumerate( failed_infos ):
            print( "{0:03d}: {1}".format( i, info[0] ) )
        print( "------------------------------------" )    
    print( "done fetching {0} cahracters".format( len(urls) ))
    return (success_infos, failed_infos)

## =====================================================================
## =====================================================================
## =====================================================================
## =====================================================================
## =====================================================================
## =====================================================================
## =====================================================================
## =====================================================================
## =====================================================================
## =====================================================================
