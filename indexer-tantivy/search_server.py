"""
Super simple web interface to run a query and return the results
"""

import logging
import subprocess
import json

from flask import Flask, Response
import flask

APP = Flask(__name__, static_url_path='')

INDEX_PATH = "session-index-001"

def _log():
    return logging.getLogger(__name__)

@APP.route("/")
def _root():
    return "<p>root</p>"

@APP.route('/static/<path:path>')
def send_static(path):
    return flask.send_from_directory('static', path)

def _get_transcript_lines(path):
    data = {'results': []}
    with open(path) as f:
        data = json.load(f)
    lines = []
    for res in data['results']:
        if ('alternatives' in res
                and len(res['alternatives']) > 0
                and 'transcript' in res['alternatives'][0]
                and 'words' in res['alternatives'][0]
                and len(res['alternatives'][0]['words']) > 0
                and 'startTime' in res['alternatives'][0]['words'][0]):
            line = res['alternatives'][0]['transcript']
            time = res['alternatives'][0]['words'][0]['startTime']
            lines.append((time, line))
    return lines


def _is_file_markdown_notes(filepath):
    return filepath.endswith(".md")
def _is_file_transcript(filepath):
    if not filepath.endswith(".json"):
        return False
    try:
        with open(filepath) as f:
            data = json.load(f)
            return ("results" in data
                    and isinstance(data['results'], list)
                    and "alternatives" in data['results'][0])
    except json.JSONDecodeError:
        return False
    return False

def _load_markdown_notes(filepath):
    data = {
        "filepath": filepath,
        "lines": None
    }
    with open(filepath) as f:
        data["lines"] = map(lambda x: x.rstrip(), f.readlines())
    return data

def _load_transcript(filepath):
    data = {
        "filepath": filepath,
        "lines": None
    }
    with open(filepath) as f:
        original_data = json.load(f)
    lines = []
    for item in original_data['results']:
        if not 'alternatives' in item:
            continue
        if not 'transcript' in item['alternatives'][0]:
            continue
        line_string = item['alternatives'][0]['transcript']
        time = item['alternatives'][0]['words'][0]['startTime']
        lines.append({'line': line_string, 'time': time})
    data['lines'] = lines
    return data

def _load_raw_file(filepath):
    with open(filepath) as f:
        return {'filepath': filepath,
                'data': f.read()}


"""
A list of ( predicate, loader, template ) for files. Each is a function
that takes a single argument, the file path. The predicate returns
true IFF the paired loader should be used to load the file into
data and the given template should be used to render it
"""
VIEW_FILE_TEMPLATES = [
    (_is_file_markdown_notes,
     _load_markdown_notes,
     "view_markdown_notes_template.jinja2"),
    (_is_file_transcript,
     _load_transcript,
     "view_transcript_template.jinja2"),
    (lambda x: True, _load_raw_file, "view_raw_file_template.jinja2")
]

@APP.route("/view/file/<mark_index>/<path:filepath>")
def _view_file(mark_index,filepath):
    data = None
    template_name = None
    filepath = "/" + filepath
    for predicate, loader, template in VIEW_FILE_TEMPLATES:
        if predicate(filepath):
            data = loader(filepath)
            template_name = template
            print("Using VIEW: {}".format(template_name))
            break
    data['mark_index'] = mark_index
    try:
        data['mark_index'] = int(mark_index)
    except:
        pass
    return flask.render_template(template_name, data=data)


@APP.route("/absolute_file/<path:filepath>")
def _send_absolute_file(filepath):
    if filepath.endswith(".md"):
        with open("/" + filepath) as f:
            return Response(f.read(), mimetype='text/plain')
    elif filepath.endswith(".json"):
        lines = _get_transcript_lines("/" + filepath)
        return flask.render_template('transcript_template.jinja2',
                                     filename="/" + filepath,
                                     lines=lines)
    else:
        return flask.send_file("/" + filepath)

def _buildup_html_li_for_search_result_item(data, context_size=5):
    filename = data['filename'][0]
    line_id = data['start_line_number'][0]
    fragment = ""
    fragment += '<div class="search_item">'
    fragment += '<div class="filename"><a target="_blank" href="/absolute_file{0}">{0}</a></div>'.format(filename)
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


def _augment_data_items(data_items, context_size):
    augmented = []
    for item in data_items:
        augmented.append(_augment_single_item(item, context_size))
    return augmented

def _line_number_from_id(line_id):
    if line_id.strip() == "":
        return None
    if "." in line_id:
        return int(line_id[:line_id.index(".")])
    return int(line_id)

def _augment_single_item(data, context_size):
    filename = data['filename'][0].strip()
    line_id = data['start_line_number'][0].strip()
    line_number = _line_number_from_id(line_id)
    target_index = context_size
    if line_number is not None and line_number <= context_size:
        target_index -= (context_size - line_number + 1)
    before_lines = []
    target_line = data['line'][0]
    mark_index = line_number
    if line_id == '':
        mark_index = data['start_audio_time'][0]
    after_lines = []
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
        for i, line in enumerate(lines):
            if i < target_index:
                before_lines.append(line)
            elif i > target_index:
                after_lines.append(line)
    return {
        'item': data,
        'filename': filename,
        'line_number': line_number,
        'before_lines': before_lines,
        'after_lines': after_lines,
        'target_line': target_line,
        'context_size': context_size,
        'target_index': target_index,
        'mark_index': mark_index
    }


def _run_query(text_query, context_size=5):
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
        return (None, res.stderr)
    data_items = []
    for line in res.stdout.split("\n"):
        if line.strip() != "":
            data_items.append(json.loads(line))
    data_items = _augment_data_items(data_items, context_size)
    return (data_items, res.stderr)

@APP.route("/search/")
@APP.route("/search/<text_query>")
def _search(text_query=None):
    if text_query is None:
        text_query = flask.request.args.get('search')
    data_items = None
    errstring = None
    if text_query is None:
        data_items = []
        errstring = ""
    else:
        data_items, errstring = _run_query(text_query)
    if data_items is None:
        return flask.render_template("search_error_template.jinja2",
                                     query=text_query,
                                     errstring=errstring)
    return flask.render_template("search_results_template.jinja2",
                                 query=text_query,
                                 data_items=data_items)

@APP.route("/search/old/<text_query>")
def _search_old(text_query):
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
