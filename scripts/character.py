'''
A simple modukle that defines a dictionary/object hiearchy for cahracters
of table top RPG games (such ad D&D)
'''

import logging


## ==========================================================================


def _log():
    return logging.getLogger( __name__ )


## ==========================================================================

def is_int(x):
    try:
        y = int(x)
        return True
    except:
        return False


## ==========================================================================

##
# A sequence of access operations for a deep hiearchy object.
# When called, returns the node at the end AND the actual steps
# taken to get to it. This means that if a step cannot be taken,
# we return the latest valid node and return the step only until
# this latest valid access.
class Getter( object ):
    def __init__( self, steps ):
        self.steps = steps
        
    def __call__(self, x):
        node = x
        taken_steps = []
        for access in self.steps:
            if hasattr( node, str(access) ):
                node = getattr( node, access )
            elif callable( access ):
                try:
                    res, success = access( node, x )
                except Exception:
                    break
                if not success:
                    break
                node = res
            elif isinstance( node, dict ) and access in node:
                node = node[access]
            elif isinstance( node, (tuple,list)) and is_int(access) and len(node) > int(access):
                node = node[int(access)]
            else:
                break
            taken_steps.append( access )
        return (node, taken_steps, len(taken_steps) == len( self.steps ) )
        
    def __str__(self):
        return str(self.steps)
    def __repr__(self):
        return self.__str__()


## ==========================================================================

##
# simple interface to get a path or return a default if we can't
def get( root, path, default=None ):
    node, _, success =  Getter( path )( root )
    if not success:
        return default
    return node

## ==========================================================================

##
# Creates an access method that will search through a list for the first
# element where the predicate is true, otherwise raise exception
class FindFirst( object ):
    def __init__(self, predicate):
        self.predicate = predicate
    def __call__( self, node, root ):
        if not isinstance( node, list ):
            raise RuntimeError(
                "Wrong node type: '{}' need list, root={}".format(
                    node, root ))
        for n in node:
            if self.predicate( n, root ):
                return ( n, True )
        return ( None, False )
    
## ==========================================================================

##
# An esy to use function to create a FindFirst based on the name
def find_first_name( name ):
    return FindFirst( lambda x,parent: x.get("name","") == name)

## ==========================================================================

APPEND = object()
EMPTY_SEQUENCE = -1

## ==========================================================================

##
# Given a root node, makes sure that the given path exists from the root.
# This will create nodes along the path.
#
# It will be smart enough to notice if the path elemtn *after* the current
# node is an integer it will create an empty list node, otehrwise it
# defaults to creating an empty dictionary node.
#
# The return is ( parent, leaf ) so that we are able to reasign the
# value at the node from it's parent using hte last path element
def _ensure_structure( root, path, taken=None, parent=None, empty_leafs=True ):
    if path is None or len(path) < 1:
        return ( parent, root, taken )
    p = path[0]
    next_p = None
    rest = path[1:]
    new_root = None
    if len(path) > 1:
        next_p = path[1]
    if isinstance(p,str) and isinstance( root, dict ):
        if p not in root:
            if next_p is None or isinstance( next_p, (str,dict) ):
                root[p] = {}
                new_root = root[p]
            elif isinstance( next_p, int ):
                root[p] = []
                new_root = root[p]
                for i in range( next_p + 1 ):
                    root[p].append( {} )
                    new_root = root[p]
        else:
            new_root = root[p]
    if ( isinstance(p,int) or p is APPEND ) and isinstance( root, list ):
        if isinstance(p,int):
            for i in range( p + 1):
                if i >= len(root):
                    if next_p is None or isinstance( next_p, (str,dict) ):
                        root.append( {} )
                    elif isinstance( next_p, int ):
                        root.append( [] )
                    else:
                        raise RuntimeError( "can't create root={} path={} p={}".format(
                            root, path, p))
            if int(p) == EMPTY_SEQUENCE and empty_leafs is True and len(rest) < 1:
                new_root = object()
            else:
                new_root = root[ p ]
        else: # APPEND case
            if next_p is None or isinstance( next_p, (str,dict) ):
                root.append( {} )
            elif isinstance( next_p, int ):
                root.append( [] )
            else:
                raise RuntimeError( "can't create root={} path={} p={}".format(
                    root, path, p))
            new_root = root[-1]
            p = len(root) - 1
                

    if new_root is None:
        raise RuntimeError( "can't create root={} path={} p={}".format(
            root, path, p))
    return _ensure_structure( new_root, rest, taken=p, parent=root )
    
## ==========================================================================

##
# Creates the given path and sets the last node to the given value.
# This means that get( root, path ) == value at the end
def _ensure_value( root, path, value ):
    parent, node, taken = _ensure_structure( root, path )
    parent[ taken ] = value
    return (parent, node, taken)

## ==========================================================================

##
# Make the top-level structure needed for a character
def _ensure_toplevel_character( root ):
    _ensure_structure( root, ['name'] )
    _ensure_structure( root, ['player'] )
    _ensure_structure( root, ['stats',EMPTY_SEQUENCE] )
    _ensure_structure( root, ['narrative_features',EMPTY_SEQUENCE] )
    _ensure_structure( root, ['structured_features',EMPTY_SEQUENCE] )
    _ensure_structure( root, ["sources",EMPTY_SEQUENCE] )

## ==========================================================================

##
# Make the structure for a single stat at the given node
def _ensure_stat( root ):
    _ensure_structure( root, ['name'] )
    _ensure_structure( root, ['types', EMPTY_SEQUENCE] )
    _ensure_structure( root, ['min'] )
    _ensure_structure( root, ['max'] )
    _ensure_structure( root, ['value'] )
    _ensure_structure( root, ['description'] )
    _ensure_structure( root, ['dice'] )
    _ensure_structure( root, ['equation'] )
    _ensure_structure( root, ['is_core'] )
    _ensure_structure( root, ["sources", EMPTY_SEQUENCE] )

## ==========================================================================

##
# make the structure for a narrative feature at the given node.
def _ensure_narrative_feature( root ):
    _ensure_structure( root, ["name"] )
    _ensure_structure( root, ["types", EMPTY_SEQUENCE] )
    _ensure_structure( root, ["description"] )
    _ensure_structure( root, ["dice"] )
    _ensure_structure( root, ["equation"] )
    _ensure_structure( root, ["is_core"] )
    _ensure_structure( root, ["sources", EMPTY_SEQUENCE] )

## ==========================================================================

##
# Make the structure for a feature (structured) at the given node
def _ensure_structured_feature( root ):
    _ensure_structure( root, ["name"] )
    _ensure_structure( root, ["types", EMPTY_SEQUENCE] )
    _ensure_structure( root, ["description"] )
    _ensure_structure( root, ["is_core"] )
    _ensure_structure( root, ["value"] )
    _ensure_structure( root, ["dice"] )
    _ensure_structure( root, ["equation"] )
    _ensure_structure( root, ["sources", EMPTY_SEQUENCE] )


## ==========================================================================

def _append_stat( character, **kw ):
    _, _, index = _ensure_structure( character, ['stats',APPEND], {})
    _ensure_structured_feature( get( character, ['stats',index] ) )
    for key, value in kw.items():
        _ensure_value( character, ['stats',index,key], value )

## ==========================================================================

def _append_narrative_feature( character, **kw ):
    _, _, index = _ensure_structure( character, ['narrative_features',APPEND], {})
    _ensure_structured_feature( get( character, ['narrative_features',index] ) )
    for key, value in kw.items():
        _ensure_value( character, ['narrative_features',index,key], value )

## ==========================================================================

def _append_structured_feature( character, **kw ):
    _, _, index = _ensure_structure( character, ['structured_features',APPEND], {})
    _ensure_structured_feature( get( character, ['structured_features',index] ) )
    for key, value in kw.items():
        _ensure_value( character, ['structured_features',index,key], value )

## ==========================================================================

##
# set a core DND stat
def _fill_core_dnd_stat( name, character, roll20_data, result_name=None ):

    if result_name is None:
        result_name = name

    types = ['stat']
    if "_mod" in name:
        types.append( "modifier" )
    if "_save" in name:
        types.append( "saving_throw" )

    # the stats are just a list in roll20, so *search* for the named
    # on first
    node = get( roll20_data, ['attribs',
                              FindFirst(lambda x,root: x['name'] == name )] )
    if node is None:
        raise RuntimeError( "Unable to fill core dnd stat '{}'".format(
            name ))
    _append_stat( character,
                  name=result_name,
                  types=types,
                  min=0,
                  value=node['current'],
                  max=node['max'],
                  is_core=True )

## ==========================================================================

##
# set a core DND skill
def _fill_core_dnd_skill( name, character, roll20_data, result_name=None ):

    if result_name is None:
        result_name = name

    # the stats are just a list in roll20, so *search* for the named
    # on first
    node = get( roll20_data, ['attribs',
                              FindFirst(lambda x,root: x['name'] == name )] )
    if node is None:
        raise RuntimeError( "Unable to fill core dnd stat '{}'".format(
            name ))
    _append_stat( character,
                  name=result_name,
                  min=0,
                  value=node['current'],
                  max=node['max'],
                  is_core=True,
                  types=['skill_proficiency'] )


## ==========================================================================

##
# Fill in the core character stats
def _fill_character_core_stats_from_roll20_data( character, roll20_data ):
    # grab core stats
    _fill_core_dnd_stat( 'strength', character, roll20_data )
    _fill_core_dnd_stat( 'dexterity', character, roll20_data )
    _fill_core_dnd_stat( 'constitution', character, roll20_data )
    _fill_core_dnd_stat( 'wisdom', character, roll20_data )
    _fill_core_dnd_stat( 'intelligence', character, roll20_data )
    _fill_core_dnd_stat( 'charisma', character, roll20_data )
    _fill_core_dnd_stat( 'strength_mod', character, roll20_data,
                         "strength_modifier" )
    _fill_core_dnd_stat( 'dexterity_mod', character, roll20_data,
                         "dexterity_modifier" )
    _fill_core_dnd_stat( 'constitution_mod', character, roll20_data,
                         "constitution_modifier" )
    _fill_core_dnd_stat( 'wisdom_mod', character, roll20_data,
                         "wisdom_modifier" )
    _fill_core_dnd_stat( 'intelligence_mod', character, roll20_data,
                         "intelligence_modifier" )
    _fill_core_dnd_stat( 'charisma_mod', character, roll20_data,
                         "charisma_modifier" )
    _fill_core_dnd_stat( 'ac', character, roll20_data,
                         "armor_class" )
    _fill_core_dnd_stat( 'hp', character, roll20_data,
                         "hit_points" )
    _fill_core_dnd_stat( 'speed', character, roll20_data,
                         "speed" )
    _fill_core_dnd_stat( 'initiative_bonus', character, roll20_data,
                         "initiative" )
    _fill_core_dnd_stat( 'strength_save_bonus', character, roll20_data,
                         "strength_saving_throw" )
    _fill_core_dnd_stat( 'dexterity_save_bonus', character, roll20_data,
                         "dexterity_saving_throw" )
    _fill_core_dnd_stat( 'constitution_save_bonus', character, roll20_data,
                         "constitution_saving_throw" )
    _fill_core_dnd_stat( 'wisdom_save_bonus', character, roll20_data,
                         "wisdom_saving_throw" )
    _fill_core_dnd_stat( 'intelligence_save_bonus', character, roll20_data,
                         "intelligence_saving_throw" )
    _fill_core_dnd_stat( 'charisma_save_bonus', character, roll20_data,
                         "charisma_saving_throw" )
    _fill_core_dnd_stat( "hit_dice", character, roll20_data, "hit_dice" )
    _fill_core_dnd_stat( "pb", character, roll20_data, "proficiency_bonus" )
    _fill_core_dnd_stat( "hitdietype", character, roll20_data, "hit_dice_type" )
    _fill_core_dnd_stat( "spell_attack_mod", character, roll20_data, "spell_attack_modifier")
    _fill_core_dnd_stat( "spell_attack_bonus", character, roll20_data, "spell_attack_bonus" )
    _fill_core_dnd_stat( "spell_save_dc", character, roll20_data, "spell_save_dc" )
    _fill_core_dnd_stat( "passive_wisdom", character,roll20_data )
    
    

## ==========================================================================

def _fill_character_core_skills_ability_checks_from_roll20_data( character, roll20_data ):
    # skill/abilit checks
    _fill_core_dnd_skill( 'acrobatics_bonus',
                          character,
                          roll20_data,
                          'acrobatics' )
    _fill_core_dnd_skill( 'animal_handling_bonus',
                          character,
                          roll20_data,
                          'animal_handling' )
    _fill_core_dnd_skill( 'arcana_bonus',
                          character,
                          roll20_data,
                          'arcana' )
    _fill_core_dnd_skill( 'athletics_bonus',
                          character,
                          roll20_data,
                          'athletics' )
    _fill_core_dnd_skill( 'deception_bonus',
                          character,
                          roll20_data,
                          'deception' )
    _fill_core_dnd_skill( 'history_bonus',
                          character,
                          roll20_data,
                          'history' )
    _fill_core_dnd_skill( 'insight_bonus',
                          character,
                          roll20_data,
                          'insight' )
    _fill_core_dnd_skill( 'intimidation_bonus',
                          character,
                          roll20_data,
                          'intimidation' )
    _fill_core_dnd_skill( 'investigation_bonus',
                          character,
                          roll20_data,
                          'investigation' )
    _fill_core_dnd_skill( 'medicine_bonus',
                          character,
                          roll20_data,
                          'medicine' )
    _fill_core_dnd_skill( 'nature_bonus',
                          character,
                          roll20_data,
                          'nature' )
    _fill_core_dnd_skill( 'perception_bonus',
                          character,
                          roll20_data,
                          'perception' )
    _fill_core_dnd_skill( 'performance_bonus',
                          character,
                          roll20_data,
                          'performance' )
    _fill_core_dnd_skill( 'persuasion_bonus',
                          character,
                          roll20_data,
                          'persuasion' )
    _fill_core_dnd_skill( 'religion_bonus',
                          character,
                          roll20_data,
                          'religion' )
    _fill_core_dnd_skill( 'sleight_of_hand_bonus',
                          character,
                          roll20_data,
                          'sleight_of_hand' )
    _fill_core_dnd_skill( 'stealth_bonus',
                          character,
                          roll20_data,
                          'stealth' )
    _fill_core_dnd_skill( 'survival_bonus',
                          character,
                          roll20_data,
                          'survival' )

## ==========================================================================

def _add_roll_as_structured_feature( character, roll20_node ):
    _append_structured_feature( character,
                                name=roll20_node.get("name",""),
                                min=None,
                                max=None,
                                value=None,
                                equation=roll20_node.get("current",""),
                                types=['calculation'] )


## ==========================================================================

def _fill_character_rolls_from_roll20_data( character, roll20_data ):
    attribs = roll20_data.get( "attribs", [] )
    for node in attribs:
        if node.get('name',"").endswith( "_roll" ):
            _add_roll_as_structured_feature( character, node )
        elif node.get('name',"").endswith( "_prof" ):
            _add_roll_as_structured_feature( character, node )

## ==========================================================================

##
# Returns a list of single structure with the information in the flattend
# reapeated_X pattern used in roll20 json
def _compose_repeated_elements( roll20_data ):
    typename = {} # map[ type -> map[ id -> structure ] ]
    for node in roll20_data.get( "attribs", [] ):
        if node.get( "name", "" ).startswith( "repeating_" ):
            raw_name = node['name']
            index = raw_name.index("-")
            rep_name = raw_name[:index]
            rest_name = raw_name[index:]
            id_index = rest_name.index( "_" )
            repeat_id = rest_name[:id_index]
            repeat_attribute = rest_name[id_index+1:]
            repeat_type = rep_name[ len("repeating_") : ]
            if repeat_type not in typename:
                typename[ repeat_type ] = {}
            repmap = typename[ repeat_type ]
            if repeat_id not in repmap:
                repmap[ repeat_id ] = {}
            obj = repmap[ repeat_id ]
            obj[ repeat_attribute ] = node.get("current","")
            obj[ 'repeat_id' ] = repeat_id
            obj[ 'repeat_type' ] = repeat_type
            
    return typename


## ==========================================================================

def _fill_character_common_DND_structured_features( character, roll20_data ):


    node = get( roll20_data, [ 'attribs', find_first_name( "background" ) ] )
    _append_structured_feature( character,
                                name="background",
                                types=['background'],
                                value=node.get('current'),
                                min=None,
                                max=None)

    node = get( roll20_data, ['attribs', find_first_name("personality_traits") ] )
    sentences = node.get("current","").split("\n\n")
    for s in sentences:
        _append_structured_feature( character,
                                    name="personality_trait",
                                    types=[ 'personality_trait' ],
                                    value=s,
                                    min=None,
                                    max=None )

    node = get( roll20_data, ['attribs', find_first_name("ideals") ] )
    _append_structured_feature( character,
                                name="ideals",
                                types=['ideals'],
                                value=node.get('current'),
                                min=None,
                                max=None)

    node = get( roll20_data, ['attribs', find_first_name("bonds") ] )
    _append_structured_feature( character,
                                name="bonds",
                                types=['bonds'],
                                value=node.get('current'),
                                min=None,
                                max=None)

    node = get( roll20_data, ['attribs', find_first_name("flaws") ] )
    _append_structured_feature( character,
                                name="flaws",
                                types=['flaws'],
                                value=node.get('current'),
                                min=None,
                                max=None)

    node = get( roll20_data, ['attribs', find_first_name("ideals") ] )
    _append_structured_feature( character,
                                name="ideals",
                                types=['ideals'],
                                value=node.get('current'),
                                min=None,
                                max=None)

    repeated = _compose_repeated_elements( roll20_data )
    for reptype in repeated:
        for _, rep in repeated[ reptype ].items():
            types = [ rep.get("repeat_type") ]
            for name, value in rep.items():
                if "source" in name or "type" in name:
                    types.append( value )
            _append_structured_feature( character,
                                        name=rep.get('name'),
                                        description=rep.get("description"),
                                        types=types,
                                        min=None,
                                        max=None,
                                        value=rep.get('name'))



## ==========================================================================
## ==========================================================================
## ==========================================================================
## ==========================================================================
## ==========================================================================
## ==========================================================================
## ==========================================================================
## ==========================================================================
## ==========================================================================
## ==========================================================================
## ==========================================================================
## ==========================================================================
## ==========================================================================
## ==========================================================================
## ==========================================================================
## ==========================================================================
## ==========================================================================
## ==========================================================================
## ==========================================================================
## ==========================================================================
## ==========================================================================
## ==========================================================================

##
# Fill the given character (which is just a dictionary) using the
# data from Roll20's JSON export data
def fill_character_from_roll20_data( character, roll20_data ):

    # fill in the structure of a character
    _ensure_toplevel_character( character )

    # Fill In player and character name
    _ensure_value( character, ['name'], get( roll20_data, ['name'], None ) )


    _fill_character_core_stats_from_roll20_data( character, roll20_data )
    _fill_character_core_skills_ability_checks_from_roll20_data( character, roll20_data )
    _fill_character_rolls_from_roll20_data( character, roll20_data )
    _fill_character_common_DND_structured_features( character, roll20_data )
