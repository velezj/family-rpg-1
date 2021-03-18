"""
Simple server that serves files, but if they end in .md will pass them 
through Pandoc first
"""

import http.server
import socketserver
import subprocess


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
            
    
def _ensure_rendered( path ):
    path = path[1:]
    args = ["pandoc",
            "--standalone",
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
