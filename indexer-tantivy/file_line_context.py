import logging
import sys

def _log():
    return logging.getLogger( __name__ )

def line_id_to_number( line_id ):
    num = int(line_id.split(".")[0])
    return num

def get_file_lines( filename, line_id, context_size ):
    lines = []
    line_num = line_id_to_number( line_id )
    start_line = line_num - context_size
    end_line = line_num + context_size
    with open( filename ) as f:
        for i, line in enumerate(f):
            line = line.strip()
            if i >= start_line and i <= end_line:
                lines.append( (i, line) )
            if i >= end_line:
                break
    return lines

if __name__ == "__main__":

    logging.basicConfig( level=logging.INFO )
    
    filename = sys.argv[1]
    line_id = sys.argv[2]
    context_size = int(sys.argv[3])
    _log().info( "File='%s' at line %s +/- %s", filename, line_id, context_size)

    result = get_file_lines( filename, line_id, context_size )
    line_num = line_id_to_number( line_id )
    print("-----")
    for l in result:
        rel_num = l[0] - line_num
        label = "{0:04d}".format(rel_num)
        if rel_num == 0:
            label = " -->"
        print( "{0} |  {1}".format( label, l[1] ) )
    print("-----")
