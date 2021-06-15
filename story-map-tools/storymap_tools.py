"""
A set of utility functions for story maps.

Particularly these function work with graphml files.
"""

import logging
import xml.etree.ElementTree as ET

import networkx as nx
import pydot

## =========================================================================

def _log():
    return logging.getLogger( __name__ )

## =========================================================================

##
# Graphml namespace for ease searching using ElementTree
ns = { 'graphml': "http://graphml.graphdrawing.org/xmlns",
       "y": "http://www.yworks.com/xml/graphml" }

## =========================================================================

##
# Given a set of colors for the graph edges, returns a mapping from
# the edge color to the following types:
#   future-possible
#   chosen
#   not-chosen
#   cutoff-by-choice
#   relationship
EDGE_FUTURE     = "future-possible"
EDGE_CHOSEN     = "chosen"
EDGE_NOT_CHOSEN = "not-chosen"
EDGE_CUTOFF     = "cutoff-by-choice"
EDGE_RELATION   = "relationship"

def _color_tuple( c ):
    if not c.startswith("#") or len(c) != 7:
        raise RuntimeError( "Unknown color string: {}".format( c ))
    return ( int(c[1:3], 16),
             int(c[3:5], 16),
             int(c[5:7], 16 ) )

def _tuple_color( c ):
    return "#{:02x}{:02x}{:02x}".format( *c ).upper()

def _compute_edge_color_to_type_mapping( color_set ):
    # split colors to numerical tuples (RGB)
    tuple_set = [ _color_tuple(c) for c in color_set ]

    # find "most" green, red, blue
    most_green = sorted([
        ( min(c[1]-c[2], c[1]-c[0]), c )
        for c in tuple_set],
                        reverse=True)[0][1]
    most_red = sorted([
        ( min(c[0]-c[1], c[0]-c[2]), c )
        for c in tuple_set],
                      reverse=True)[0][1]
    most_blue = sorted([
        ( min(c[2]-c[1], c[2]-c[0]), c )
        for c in tuple_set],
                       reverse=True)[0][1]

    # find most dark
    most_dark = sorted([ (c[0]+c[1]+c[2],c) for c in tuple_set])[0][1]

    remainder = set(tuple_set) - set([ most_green, most_red, most_blue, most_dark])

    result = {
        _tuple_color(most_red): EDGE_FUTURE,
        _tuple_color(most_green): EDGE_CHOSEN,
        _tuple_color(most_blue): EDGE_NOT_CHOSEN,
        _tuple_color(most_dark): EDGE_RELATION }
    for x in remainder:
        result[_tuple_color(x)] = EDGE_CUTOFF
    return result

## =========================================================================

##
# Create a networkx graph from a graphml data stream
def compute_nx_graph_from_yed_graphml_data( graphml_data ):
    """
    Given a *string* containing GraphML data, we parse it and
    return a new NetworkX Directed Graph representing the data.
    The graphml is assumed to be specifically from the yEd
    application and so the parses may use some of the internal
    yEd specific attributes.

    We return ( nx-graph, edge color-set ) which computes the set
    of colors for the edges seen.
    """

    graph = nx.DiGraph()
    data = ET.fromstring( graphml_data )

    # right now we work with one and only one graph per data/file
    yed_graph_node = data.findall(".//graphml:graph", ns)
    if yed_graph_node is None:
        raise RuntimeError(
            "Unable to haandle GraphML data, "
            "can't find single graph node: {}".format( yed_graph_node ) )
    if len(yed_graph_node) > 1:
        _log().warning( "found multiple <graph> elements: %s", yed_graph_node )


    # create all the nodes i nthe nx graph using the graphml ids for names
    num_nodes = 0
    for node in data.findall('.//graphml:node', ns):
        nid = node.get('id')
        if nid is None or len(nid) < 1:
            _log().warning( "Strange node id found in graphml: id=%s %s",
                            nid, node)
        label = node.find('.//y:NodeLabel', ns ).text
        graph.add_node( nid, label=label )
        num_nodes += 1
    _log().info( "Found #%s nodes", num_nodes )

    # ok, connect all edges from the graphml in the nx graph
    num_edges = 0
    color_set = set([])
    for edge in data.findall('.//graphml:edge', ns):
        eid = edge.get('id')
        source = edge.get('source')
        target = edge.get('target')
        color = edge.find('.//y:LineStyle', ns).get('color')
        if color is None:
            continue
        color_set.add( color )
        if eid is None or source is None or target is None:
            _log().warning( "Strange edge found from graphml: "
                            "%s",
                            edge)
        graph.add_edge( source, target, color=color )
        num_edges += 1
    _log().info( "Found #%s edges", num_edges )

    # compute edge type from color
    color_type_map = _compute_edge_color_to_type_mapping( color_set )

    # ok, add edge type to all edges
    for (s,t) in graph.edges:
        graph.edges[s,t]['type'] = color_type_map.get(graph.edges[s,t]['color'])

    return graph, color_set, color_type_map

## =========================================================================
## =========================================================================
## =========================================================================

def edge_type_subgraph( graph, edge_type ):
    edge_types = []
    if isinstance( edge_types, list):
        edge_types = edge_type
    else:
        edge_types = [ edge_type ]
    subg = nx.edge_subgraph(
        graph,
        [ (e[0],e[1]) for e in graph.edges().data()
          if e[2]['type'] in edge_types ] )
    return subg
    

## =========================================================================

def return_current_story_points( graph ):
    subg = edge_type_subgraph( graph, EDGE_CHOSEN )
    nodes = []
    for n in subg.nodes:
        if len(subg[n]) == 0:
            nodes.append( n )
    return nodes

## =========================================================================

def return_possible_next_story_points( graph, max_depth = 1 ):
    future_graph = edge_type_subgraph( graph, EDGE_FUTURE )
    current_nodes = return_current_story_points( graph )
    to_explore = set(current_nodes)
    found_nodes = set([])
    depth = 0
    start_depth_nodes = set(current_nodes)
    while len(to_explore) > 0 and depth < max_depth:
        source = to_explore.pop()
        out_edges = future_graph.out_edges( [source] )
        out_nodes = set([ e[1] for e in out_edges ])
        out_nodes -= set(source)
        found_nodes |= out_nodes
        to_explore |= out_nodes
        if len( to_explore & start_depth_nodes ) < 1:
            start_depth_nodes = set(list(to_explore))
            depth += 1
    return list(found_nodes)

## =========================================================================

def write_out_reachable_graph( nx_graph, filename ):
    subgraph = edge_type_subgraph( nx_graph, EDGE_FUTURE )
    nx.drawing.nx_pydot.write_dot( subgraph, filename )
        

## =========================================================================

def print_story_map_report( graphml_filename, max_depth=3 ):
    with open( graphml_filename ) as f:
        data = f.read()
    graph, colors, color_type_map = compute_nx_graph_from_yed_graphml_data( data )
    current_points = return_current_story_points( graph )
    possible_next_points = return_possible_next_story_points( graph )

    reachable_graph_output_filename = graphml_filename + ".future-reachable.dot"
    write_out_reachable_graph( graph, reachable_graph_output_filename )

    current_scenes = list([
        graph.nodes.data()[n]['label'].replace( '\n', ' ')
        for n in current_points ])
    possible_next_scenes = list([
        graph.nodes.data()[n]['label'].replace('\n',' ')
        for n in possible_next_points ])
    print( "Story Map:" )
    print( "------------------------------" )
    print( "" )
    print( "Reachable Future Graph at: {}".format( reachable_graph_output_filename ) )
    print( "" )
    print( "Color Set: {}".format( sorted(list(colors))) )
    print( "Color->Type Map: {}".format(color_type_map) )
    print( "" )
    print( "Current Scene(s):")
    for i,x in enumerate(current_scenes):
        print( "  {0:02d}. {1}".format( i + 1, x ) )
    print( "" )
    print( "Possible Next Scenes:" )
    for i,x in enumerate(possible_next_scenes):
        print( "  {0:02d}. {1}".format( i + 1, x ) )
    print( "" )

    for d in range( 2, max_depth + 1 ):
        next_points = return_possible_next_story_points( graph, max_depth=d )
        next_scenes = list([
            graph.nodes.data()[n]['label'].replace('\n',' ')
            for n in next_points ])
        print( "Possble {}-Away Scenes:".format( d ) )
        for i,x in enumerate(next_scenes):
            print( "  {0:02d}. {1}".format( i + 1, x ) )
        print( "" )


## =========================================================================
## =========================================================================
## =========================================================================
## =========================================================================
## =========================================================================
## =========================================================================
## =========================================================================
## =========================================================================
## =========================================================================
## =========================================================================
## =========================================================================
## =========================================================================
## =========================================================================
## =========================================================================
## =========================================================================
## =========================================================================
## =========================================================================
