import itertools

def is_there( node, key ):
    x = node.get(key,None)
    if x is None:
        return False
    if isinstance( x, str ) and len(x) < 1:
        return False
    if isinstance( x, (dict,list,tuple) ) and len(x) < 1:
        return False
    return True

def grab_items_with_types( character, types ):
    result = []
    for x in itertools.chain( character['stats'],
                              character['narrative_features'],
                              character['structured_features'] ):
        source_types = x.get("types")
        keep = True
        for t in types:
            if t not in source_types:
                keep = False
                break
        if not keep:
            continue
        result.append( x )
    return result


def compute_all_types( character ):
    types = set()
    for x in itertools.chain( character['stats'],
                              character['narrative_features'],
                              character['structured_features'] ):
        s = x.get("types",[])
        types |= set(s)
    return sorted(list(types))
                              
        

def print_character_summary( character ):
    print( "CHARACTER" )
    sections = ["background","personality_trait","ideals","bonds","flaws","stat","skill_proficiency","traits","item","spell","attack"]
    for s in sections:
        print( "\n" + "___"*20 + s + "___"*20 + "\n" )
        items = grab_items_with_types( character, [s] )
        for i in items:
            heading_line = "  " + str(i.get("name")) + "  " + str(i.get("types"))
            if is_there( i, "value" ):
                heading_line += "  " + str(i.get("value"))
            print( heading_line )
            if is_there( i, "description" ):
                print( "    " + str(i.get("description")).replace("\n","\n    ") )
            print( "" )
        
