'''
A simple modukle that defines a dictionary/object hiearchy for cahracters
of table top RPG games (such ad D&D)
'''

import logging
import sys
import copy
import json

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
                  min=None,
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
                  min=None,
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

def _create_roll_description( node, character, roll20_data ):
    description = str(node.get("current",""))
    return description

## ==========================================================================

def _add_roll_as_structured_feature( character, roll20_node, roll20_data ):
    _append_structured_feature( character,
                                name=roll20_node.get("name",""),
                                description=_create_roll_description( roll20_node,
                                                                      character,
                                                                      roll20_data ),
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
            _add_roll_as_structured_feature( character, node, roll20_data )
        elif node.get('name',"").endswith( "_prof" ):
            _add_roll_as_structured_feature( character, node, roll20_data )

## ==========================================================================

def _norm_to_none( x ):
    if x is None:
        return None
    if isinstance( x, str ):
        if len(x.strip()) < 1:
            return None
    if isinstance( x, dict ):
        if len(x) < 1:
            return None
    return x

## ==========================================================================

def _access_equation_data( access, roll20_data ):
    if access in roll20_data:
        return roll20_data.get( access )
    for x in roll20_data.get("attribs",[]):
        if x.get("name") == access:
            return x.get("current")
    return None

## ==========================================================================

def _solve_equations( x, character, roll20_data ):
    if x is None:
        return None
    if "[[" not in x and "@" not in x:
        return x
    try:
        start_index = x.find("[[")
        end_index = x.find("]]")
        wrap_len = 2
        if start_index < 0:
            start_index = 0
            wrap_len = 0
        if end_index < 0:
            end_index = len(x)
            wrap_len = 0
        eq = x[start_index+wrap_len:end_index]
        _log().info( "  found eq: '%s' (%s,%s)", eq, start_index, end_index )
        while "@{" in eq:
            index = eq.index("@{")
            end_i = eq.index("}")
            access = eq[index+2:end_i]
            _log().info("    access: '%s' (%s,%s)", access, index, end_i )
            value = _access_equation_data( access, roll20_data )
            _log().info("    value: '%s'", value )
            eq = eq[:index] + str(value) + eq[end_i+1:]
            _log().info("    filling: eq='%s'", eq )
        _log().info("  filled equation: '%s'", eq )
        value = eval( eq )
        _log().info("  value: %s", value )
        x = x[:start_index] + str(value) + x[end_index+wrap_len:]
        _log().info( "  -> resutsing: '%s'", x )
        return x
    except:
        _log().info( "Unable to solve equation: '%s'",  x )
        _log().exception("")
        return x

## ==========================================================================

def _create_spell_description( repeated_element, character, roll20_data ):
    desc = _norm_to_none(get( repeated_element, ['spelldescription'] ))
    higher_levels = _norm_to_none(get( repeated_element, ['spellathigherlevels']))
    casting_time = _norm_to_none(get( repeated_element, ['spellcastingtime']))
    spell_attack = _norm_to_none(get( repeated_element, ['spellattack'] ))
    spell_class = _norm_to_none(get( repeated_element, ['spellclass'] ))
    spell_component_m = _norm_to_none(get( repeated_element, ['spellcomp_m']))
    spell_component_v = _norm_to_none(get( repeated_element, ['spellcomp_v']))
    spell_component_s = _norm_to_none(get( repeated_element, ['spellcomp_s']))
    spell_materials = _norm_to_none(get( repeated_element, ['spellcomp_materials']))
    spell_concentration = _norm_to_none(get( repeated_element, ['spellconcentration']))
    damage = _norm_to_none(get( repeated_element, ['spelldamage']))
    damage2 = _norm_to_none(get( repeated_element, ['spelldamage2']))
    spell_type = _norm_to_none(get( repeated_element, ['spelltype']))
    spell_type2 = _norm_to_none(get( repeated_element, ['spelltype2']))
    spell_range = _norm_to_none(get( repeated_element, ['spellrange']))
    spell_ritual = _norm_to_none(get( repeated_element, ['spellritual']))
    spell_save = _norm_to_none(get(repeated_element, ['spellsave']))
    spell_save_success = _norm_to_none(get( repeated_element, ['spellsavesuccess']))
    spell_school = _norm_to_none(get( repeated_element, ['spellschool'] ))
    spell_target = _norm_to_none(get( repeated_element, ['spelltarget'] ))
    spell_source = _norm_to_none(get( repeated_element, ['spellsource'] ))
    spell_duration = _norm_to_none(get( repeated_element, ['spellduration'] ))

    description = ""
    freshline = True
    freshlist = True

    if spell_school is not None:
        description += "School of {}".format( spell_school )
        freshline = False
        freshlist = False
    if spell_class is not None:
        if not freshlist and not freshlist:
            description += ", "
        description += str(spell_class)
        freshline = False
        freshlist = False
    if spell_source is not None:
        if not freshline and not freshlist:
            description += "/"
        description += str(spell_source)
        freshline = False
        freshlist = False
    if spell_ritual is not None:
        if not freshlist:
            description += ", "
        description += str(spell_ritual)
        freshlist = False
        freshlist = False
    if not freshline:
        description = "(" + description + ")" + "\n"
    freshline = True
    freshline = True

    
    if casting_time is not None:
        description += "Casting Time: {}".format( casting_time )
        freshline = False
        freshlist = False
    if spell_duration is not None:
        if not freshline and not freshline:
            description += ", "
        description += "Duration: {}".format( spell_duration )
        if spell_concentration is not None:
            description += "(concentration)"
        freshline = False
        freshlist = False
    if not freshline or not freshlist:
        description += "\n"
    freshline = True
    freshlist = True
    
    if any([ spell_component_m is not None,
             spell_component_v is not None,
             spell_component_s is not None,
             spell_materials is not None ]):
        description += "Components: "
        freshline = False
        freshlist = True
        if spell_component_v is not None:
            if not freshlist:
                description += ", "
            description += "Verbal"
            freshlist = False
        if spell_component_s is not None:
            if not freshlist:
                description += ", "
            description += "Sommatic"
            freshlist = False
        if spell_materials is not None:
            if not freshlist:
                description += ", "
            description += str(spell_materials)
    if not freshline:
        description += "\n"
    freshline = True
    freshlist = True

    if spell_attack is not None:
        if not freshline and not freshlist:
            description += ", "
        description += "Spell Attack: {}".format( spell_attack )
        freshline = False
        freshlist = False
    if spell_range is not None:
        if not freshlist:
            description += ", "
        description += "Range: {}".format( spell_range )
        freshlist = False
        freshline = False
    if spell_target is not None:
        if not freshlist:
            description += ", "
        description += "Target: {}".format( spell_target )
        freshline = False
        freshlist = False
    if not freshline:
        description += "\n"
    freshline = True
    freshlist = True
    
    if damage is not None:
        if not freshline and not freshlist:
            description += ", "
        description += "Damage: {}".format( damage )
        freshline = False
        freshlist = False
    if spell_type is not None:
        if not freshlist:
            description += " "
        description += "{}".format( spell_type )
        freshline = False
        freshlist = False
    if damage2 is not None:
        if not freshline and not freshlist:
            description += " and "
        description += "{}".format( damage2 )
        freshline = False
        freshlist = False
    if spell_type2 is not None:
        if not freshine and not freshlist:
            description += " "
        description += "{}".format( spell_type2 )
    if not freshline:
        description += "\n"
    freshline = True
    freshlist = True
    
    if spell_save is not None:
        description += "Save: {}".format( spell_save )
        freshline = False
        freshlist = False
    if spell_save_success is not None:
        if not freshline and not freshlist:
            description += ", "
        description += "on success {}".format( spell_save_success )
    if not freshline:
        description += "\n"
    freshline = True
    freshlist = True
    
    if desc is not None:
        description += desc
        freshline = False
        freshlist = False
    if higher_levels is not None:
        if not freshline:
            description += "\n"
        description += higher_levels

    # description = """Class: {} School: {} (ritual:{})  Source: {}
    # Casting Time: {}   Duration: {} (concentration:{}) Range: {} Target: {}
    # Spell Attack: {} Components: M{} V{} S{} Materials: {}
    # Damage: {} {} and {} {} damage
    # Save: {}, on success {}
    # {}
    # {}""".format(
    #     spell_class,
    #     spell_school,
    #     spell_ritual,
    #     spell_source,
    #     casting_time,
    #     spell_duration,
    #     spell_concentration,
    #     spell_range,
    #     spell_target,
    #     spell_attack,
    #     spell_component_m,
    #     spell_component_v,
    #     spell_component_s,
    #     spell_materials,
    #     damage, spell_type,
    #     damage2, spell_type2,
    #     spell_save, spell_save_success,
    #     desc,
    #     higher_levels )
    
    return description

## ==========================================================================

def _create_attack_description( repeated_element, character, roll20_data ):
    name = _norm_to_none(get( repeated_element, ["atkname"] ))
    damage_base = _norm_to_none( get(repeated_element, ['dmgbase'] ))
    damage_type = _norm_to_none( get(repeated_element, ['dmgtype'] ))
    damage2_base = _norm_to_none( get(repeated_element, ['dmg2base'] ))
    damage2_type = _norm_to_none( get(repeated_element, ['dmg2type'] ))
    attack_range = _norm_to_none( get(repeated_element, ['atkrange'] ))
    save_effect = _norm_to_none( get(repeated_element, ['saveeffect'] ))
    save_attribute = _norm_to_none( get(repeated_element, ['saveattr'] ))
    save_dc = _norm_to_none( get(repeated_element, ['savedc'] ))
    hldmg = _norm_to_none( get( repeated_element, ['hldmg'] ))
    attack_description = _norm_to_none( get(repeated_element, ['atk_desc'] ))
    attack_attribute_base = _norm_to_none( get(repeated_element, ['atkattr_base']))
    datastring = str(dict(
        name=name,
        damage_base = damage_base,
        damage_type = damage_type,
        damage2_base = damage2_base,
        damage2_type = damage2_type,
        attack_range = attack_range,
        save_effect = save_effect,
        save_attribute = save_attribute,
        save_dc = save_dc,
        hldmg = hldmg,
        attack_description = attack_description,
        attack_attribute_base = attack_attribute_base ) )

    # attack attribute base does not use normal "equation" or access syntax :( :(
    if ("[[" not in attack_attribute_base
        and "@" not in attack_attribute_base
        and not is_int(attack_attribute_base) ):
        attack_attribute_base = attack_attribute_base.replace(
            "spell",
            "[[@{spell_attack_bonus}]]" )


    damage_base = _solve_equations( damage_base, character, roll20_data )
    damage_type = _solve_equations( damage_type, character, roll20_data )
    damage2_base = _solve_equations( damage2_base, character, roll20_data )
    damage2_type = _solve_equations( damage2_type, character, roll20_data )
    attack_range = _solve_equations( attack_range, character, roll20_data )
    attack_attribute_base = _solve_equations( attack_attribute_base, character, roll20_data )
    attack_description = _solve_equations( attack_description, character, roll20_data )
    save_effect = _solve_equations( save_effect, character, roll20_data )
    save_attribute = _solve_equations( save_attribute, character, roll20_data )
    save_dc = _solve_equations( save_dc, character, roll20_data )
    hldmg = _solve_equations( hldmg, character, roll20_data )

    
    description = ""
    if attack_attribute_base is not None:
        description += "to hit: {0}".format( attack_attribute_base )
    if attack_range is not None:
        description += ", range: {0}".format( attack_range )
    if damage_base is not None:
        description += ", deals {0} {1} damage".format(
            damage_base,
            "" if damage_type is None else damage_type )
    if damage2_base is not None:
        description += " and an additional {0} {1} damage".format(
            damage2_base,
            "" if damage2_type is None else damage2_type )
    description += "."
    if attack_description is not None:
        description += attack_description
    if save_effect is not None:
        description += " Target rolls a {0} save roll with DC {1}. One a success {2}".format(
            save_attribute,
            save_dc,
            save_effect)
        if hldmg is not None:
            description += " else {0}.".format( hldmg )
    #description += "   data={0}".format( datastring )
    return description

## ==========================================================================

##
# Returns a list of single structure with the information in the flattend
# reapeated_X pattern used in roll20 json
def _compose_repeated_elements( roll20_data ):
    typename = {} # map[ type -> map[ id -> structure ] ]
    for node in roll20_data.get( "attribs", [] ):
        if node.get( "name", "" ).startswith( "repeating_" ):
            raw_name = node['name']
            #_log().info( "Found repeating: '%s'", raw_name)
            index = raw_name.index("-M")
            rep_name = raw_name[:index-1]
            rest_name = raw_name[index:]
            id_index = rest_name.index( "_" )
            repeat_id = rest_name[:id_index]
            repeat_attribute = rest_name[id_index+1:]
            repeat_type = rep_name[ len("repeating_") : ]
            #_log().info( "  type=%s attr=%s id=%s name=%s",
            #             repeat_type, repeat_attribute, repeat_id, rep_name )
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

    types_simple = ["traits","proficiencies","tool"]
    repeated = _compose_repeated_elements( roll20_data )
    for reptype in repeated:
        if reptype not in types_simple:
            continue
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
                                        value=rep.get('name'),
                                        extra=rep)

    # spells are special
    for reptype in repeated:
        if "spell" not in reptype:
            continue
        for _, rep in repeated[ reptype ].items():
            types = [ rep.get("repeat_type") ]
            types.append( rep.get("spelllevel") )
            types.append( "spell" )
            if rep.get("spellschool",None) is not None:
                types.append( rep.get("spellschool") )
            _append_structured_feature( character,
                                        name=rep.get('spellname'),
                                        description=_create_spell_description( rep,
                                                                               character,
                                                                               roll20_data ),
                                        types=types,
                                        min=None,
                                        max=None,
                                        value=rep.get('spellname'),
                                        extra=rep)

    # attacks are special
    if "attack" in repeated:
        reptype = "attack"
        for _, rep in repeated[ reptype ].items():
            types = [ rep.get("repeat_type") ]
            if len(rep.get('spellid',"")) > 1:
                types.append( "spell" )
                if rep.get("spelllevel",None) is not None:
                    types.append( "spell-" + str(rep.get("spelllevel")) )
                if rep.get("spell",None) is not None:
                    types.append( rep.get("spell") )
            _append_structured_feature( character,
                                        name=rep.get('atkname'),
                                        description=_create_attack_description(rep,
                                                                               character,
                                                                               roll20_data),
                                        types=types,
                                        min=None,
                                        max=None,
                                        value=rep.get('atkname'),
                                        extra=rep)


    # items are special
    if "inventory" in repeated:
        reptype = "inventory"
        for _, rep in repeated[ reptype ].items():
            types = [ rep.get("repeat_type") ]
            types.append( "item" )
            _append_structured_feature( character,
                                        name=rep.get('itemname'),
                                        description=rep.get("itemcontent"),
                                        types=types,
                                        min=None,
                                        max=None,
                                        value=rep.get('itemname'),
                                        extra=rep)



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

## ==========================================================================

def _is_empty( y ):
    return (   (isinstance(y,str) and y.strip() == "")
               or (isinstance(y,dict) and len(y) < 1)
               or y is None )

##
# Given a deep structure, normalize empty strings, None, and empty
# dicionatires into None
def _normalize_empty( x ):
    if x is None:
        return
    if isinstance( x, dict ):
        for k in x:
            y = x[k]
            if _is_empty(y):
                x[k] = None
            _normalize_empty(x[k])
    if isinstance( x, list ):
        for i in range(len(x)):
            if _is_empty(x[i]):
                x[i] = None
            _normalize_empty(x[i])

## ==========================================================================

##
# Write out a JSON representation.
# We take care of reducing several ways of saying "empty" to a single
# json null style
def write_character_as_json( character, outstream ):
    c = copy.deepcopy( character )
    _normalize_empty( c )
    json.dump( c, outstream, indent=2 )
