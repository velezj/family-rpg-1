import io
import json
import re

def _get_roll20_attribute( data, name ):
    for att in data.get( 'attribs', [] ):
        if att.get('name','') == name:
            return att
    return None

def _classlevel_function( att, data ):
    return [( 'ClassLevel',
              "{} ({}) Level {}".format(
                  _get_roll20_attribute( data, 'class' ).get( 'current', ''),
                  _get_roll20_attribute( data, 'subclass').get( 'current', ''),
                  _get_roll20_attribute( data, 'level' ).get( 'current', '' ) ) )]

Roll20_To_Sheet_Map = {
    'class': _classlevel_function,
    'race':'Race ',
    'strength':'STR',
    'dexterity':'DEX',
    'constitution':'CON',
    'intelligence':'INT',
    'wisdom':'WIS',
    'charisma':'CHA',
    'strength_mod':'STRmod',
    'dexterity_mod':'DEXmod ',
    'constitution_mod':'CONmod',
    'intelligence_mod':'INTmod',
    'wisdom_mod':'WISmod',
    'charisma_mod':'CHamod',
    'ac':'AC',
    'hp': [('HPCurrent','current'),('HPMax', 'max')],
    'name': 'CharacterName',
    'initiative_bonus': 'Initiative',
    'speed':'Speed',
    'strength_save_bonus':'ST Strength',
    'dexterity_save_bonus':'ST Dexterity',
    'constitution_save_bonus':'ST Constitution',
    'intelligence_save_bonus':'ST Intelligence',
    'wisdom_save_bonus':'ST Wisdom',
    'charisma_save_bonus':'ST Charisma',
    'acrobatics_bonus': 'Acrobatics',
    'animal_handling_bonus': 'Animal',
    'arcana_bonus':'Arcana',
    'athletics_bonus':'Athletics',
    'deception_bonus':'Deception ',
    'history_bonus':'History ',
    'insight_bonus':'Insight',
    'intimidation_bonus':'Intimidation',
    'investigation_bonus':'Investigation ',
    'medicine_bonus':'Medicine',
    'nature_bonus':'Nature',
    'perception_bonus':'Perception ',
    'performance_bonus': 'Performance',
    'persuasion_bonus':'Persuasion',
    'religion_bonus':'Religion',
    'sleight_of_hand_bonus':'SleightofHand',
    'stealth_bonus':'Stealth ',
    'survival_bonus':'Survival',
}


def _compute_sheet_values( mapper, roll20_attribute, roll20_data ):
    if isinstance( mapper, str ):
        return [( mapper, roll20_attribute.get('current','') )]
    if isinstance( mapper, tuple ):
        return [( mapper[0], roll20_attribute.get( mapper[1], '' ) )]
    if isinstance( mapper, list ):
        values = []
        for m in mapper:
            values.extend( _compute_sheet_values( m, roll20_attribute, roll20_data ) )
        return values
    if callable( mapper ):
        return mapper( roll20_attribute, roll20_data )
    raise RuntimeError( "Unknown Mapper: {0}".format( mapper ) )

def compute_sheet_pairs( roll20_json_data ):
    pairs = []
    for att in roll20_json_data.get( 'attribs', []):
        if att['name'] in Roll20_To_Sheet_Map:
            values = _compute_sheet_values( Roll20_To_Sheet_Map[att['name']], att, roll20_json_data )
            pairs.extend( values )
    return pairs


def _write_fdf_header( out ):
    bh = bytearray.fromhex('25 46 44 46 2d 31 2e 32  0a 25 e2 e3 cf d3 0a 31')
    head = """ 0 obj 
<<
/FDF 
<<
/Fields [
"""
    out.write( bh )
    out.write( head.encode('utf-8') )

def _write_fdf_footer( out ):
    foot = """]
>>
>>
endobj 
trailer

<<
/Root 1 0 R
>>
%%EOF"""
    out.write( foot.encode('utf-8') )

def _write_fdf_field( out, pair ):
    dat = """<<
/V ({1})
/T ({0})
>>
""".format( *pair )
    out.write( dat.encode('utf-8') )

def write_out_filled_data_fdf( pairs, out ):
    _write_fdf_header( out )
    for p in pairs:
        _write_fdf_field( out, p )
    _write_fdf_footer( out )

def save_filled_fdf( filename, pairs ):
    with open( filename, 'wb' ) as f:
        write_out_filled_data_fdf( pairs, f )

    


####
#####
###### NOTES
#####
###
# checkboxes 3031, 3032 are 3rd level spell prepared.
#
#
#


def _compose_new_chunk( c ):
    m = re.search( r'/T \((.*)\)', c )
    if m:
        newc = c.sub( r'/V \(\)', "/V )" + m.group(1) + ")", c )
    else:
        newc = c
    return newc
    
def _create_hack_labeled_fdf( fdf_in, fdf_out ):
    all_indata = fdf_in.read()
    chunks = all_indata.decode('utf-8').split('<<')
    for c in chunks:
        if "/V" in c:
            new_c = _compose_new_chunk( c )
        else:
            new_c = c
        fdf_out.write( new_c.encode('utf-8') )


