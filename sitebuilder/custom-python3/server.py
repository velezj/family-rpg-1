"""
Simple server that serves files, but if they end in .md will pass them 
through Pandoc first
"""

import http.server
import socketserver
import subprocess
import os
import urllib
import sys
import io
import html

from http import HTTPStatus

class CustomHandler( http.server.SimpleHTTPRequestHandler ):

    def do_GET(self):
        if self.path.endswith( '.md' ):
            _ensure_rendered( self.path )
        return super().do_GET()

    def translate_path(self, path):
        p = super().translate_path(path)
        if p.endswith( '.md' ):
            p += ".html"
        return p


    def list_directory(self, path):
        """Helper to produce a directory listing (absent index.html).
        Return value is either a file object, or None (indicating an
        error).  In either case, the headers are sent, making the
        interface the same as for send_head().
        """
        try:
            listA = os.listdir(path)
        except OSError:
            self.send_error(
                HTTPStatus.NOT_FOUND,
                "No permission to list directory")
            return None
        listA.append( ".." )
        listA.sort(key=lambda a: a.lower())
        r = []
        try:
            displaypath = urllib.parse.unquote(self.path,
                                               errors='surrogatepass')
        except UnicodeDecodeError:
            displaypath = urllib.parse.unquote(path)
        displaypath = html.escape(displaypath, quote=False)
        enc = sys.getfilesystemencoding()
        title = 'Directory listing for %s' % displaypath
        r.append('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" '
                 '"http://www.w3.org/TR/html4/strict.dtd">')
        r.append('<html>\n<head>')
        r.append('<meta http-equiv="Content-Type" '
                 'content="text/html; charset=%s">' % enc)
        r.append('<title>%s</title>\n</head>' % title)
        r.append('<body>\n<h1>%s</h1>' % title)
        r.append('<hr>\n<ul>')
        for name in listA:
            if name.endswith(".md.html"):
                continue
            if name.endswith( "~" ):
                continue
            fullname = os.path.join(path, name)
            displayname = linkname = name
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
                # Note: a link to a directory displays with @ and links with /
            r.append('<li><a href="%s">%s</a></li>'
                    % (urllib.parse.quote(linkname,
                                          errors='surrogatepass'),
                       html.escape(displayname, quote=False)))
        r.append('</ul>\n<hr>\n</body>\n</html>\n')
        encoded = '\n'.join(r).encode(enc, 'surrogateescape')
        f = io.BytesIO()
        f.write(encoded)
        f.seek(0)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-type", "text/html; charset=%s" % enc)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        return f

    
    
def _ensure_rendered( path ):
    path = path[1:]
    tufte_style="https://raw.githubusercontent.com/otsaloma/markdown-css/master/tufte.css"
    buttondown_style="https://gist.githubusercontent.com/ryangray/1882525/raw/2a6e53f645b960f0bed16d686ba3df36505f839f/buttondown.css"
    style=tufte_style

    args = ["pandoc",
            "--standalone",
            "--self-contained",
            "--toc",
            "--to=html5",
            "-o",
            path + ".html",
            path]
    print( "Calling PANDOC as '{}'".format( args ) )
    res = subprocess.run(args)
    try:
        res.check_returncode()
    except Exception:
        print( "Failed running pandoc: {}".format( res ) )



if __name__ == "__main__":
    PORT=8000
    Handler = CustomHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("serving at port", PORT)
        httpd.serve_forever()
