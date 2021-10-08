"""
Super simple web interface to run a query and return the results
"""

import logging
import subprocess
import json

from flask import Flask

APP = Flask(__name__)

INDEX_PATH = "session-index-001"

def _log():
    return logging.getLogger(__name__)

@APP.route("/")
def _root():
    return "<p>root</p>"


def _buildup_html_li_for_search_result_item(data, context_size=5):
    filename = data['filename'][0]
    line_id = data['start_line_number'][0]
    fragment = ""
    fragment += '<div class="search_item">'
    fragment += '<div class="filename">{}</div>'.format(filename)
    fragment += '<div class="line_id">{}</div>'.format(line_id)
    fragment += '<div class="context">\n'
    lines = [data['line'][0]]
    no_context = True
    if line_id != '':
        res = subprocess.run(
            ["python",
             "file_line_context.py",
             filename,
             line_id,
             str(context_size),
             "true"],
            capture_output=True,
            text=True)
        res.check_returncode()
        lines = json.loads(res.stdout)
        no_context = False
    for i, line in enumerate(lines):
        pre = ""
        suf = ""
        if i == context_size or no_context:
            pre = "<span class=\"target_line\"><b>"
            suf = "</b></span>"
        fragment += '<p>{}{}{}</p>\n'.format(pre, line, suf)
    fragment += "</div>"
    fragment += "</div>\n"
    fragment = "<li>" + fragment + "</li>"
    return fragment

@APP.route("/search/<text_query>")
def _search(text_query):
    res = subprocess.run(
        ["tantivy",
         "search",
         "--index",
         INDEX_PATH,
         "--query",
         text_query],
        capture_output=True,
        text=True)
    if res.returncode != 0:
        return "<h1>ERROR: {}</h1>".format(res.stderr)
    data_items = None
    body_string = None
    full_html = None
    try:
        raw_lines = ""
        data_items = []
        for line in res.stdout.split("\n"):
            raw_lines += line
            if len(line.strip()) > 0:
                data_items.append(json.loads(line))
        body_string = "<body>"
        body_string += "<div><div>QUERY: [<i>{}</i>] resulted in #{}</div></div>\n".format(text_query, len(data_items))
        body_string += "<ol>\n"
        for data in data_items:
            body_string += _buildup_html_li_for_search_result_item(data) + "\n"
        body_string += "</ol>\n"
        #body_string += "<p><p>{}</p></p>\n".format(raw_lines)
        body_string += "</body>\n"
        full_html = """
        <html>
        {}
        </thml>""".format(body_string)
        return full_html
    except Exception:
        raise
        # _log().exception()
        # return "ITEMS:{} \n\n\nBODY:{} \n\n\nFULL:{}".format(
        #     data_items, body_string, full_html)
