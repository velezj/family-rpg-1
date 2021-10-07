#!/usr/bin/fish

##-----------------------------------------------------------------------
## Read in Root Audio and Notes paths
##-----------------------------------------------------------------------
set root_audio_path $argv[1]
set root_notes_path $argv[2]
echo "ROOT PATHS: AUDIO='$root_audio_path'  NOTES='$root_notes_path'" 

##-----------------------------------------------------------------------
## Rebuild from scratch all the indices :)
##-----------------------------------------------------------------------

rm -rf session-index-001/
mkdir session-index-001
cp meta.json session-index-001

##-----------------------------------------------------------------------
## Session Transcripts
##-----------------------------------------------------------------------

for i in (ls $root_audio_path/*.json)
    echo "Found '$i'"
    set filename (basename "$i")
    set absolute_filename (realpath "$i")
    set datestring (basename "$i" | cut --delimiter '.' --fields 1)
    set datepart (echo "$datestring" | cut --delimiter '_' --fields 1)
    set timepartraw (echo "$datestring" | cut --delimiter '_' --fields 2)
    set timepart (echo "$timepartraw" | tr "-" ":")
    set datetimeformated (echo -s "$datepart" "T" "$timepart" "Z" )
    cat "$i" | jq --compact-output " .results[]|.alternatives[0] | {filename: \"$absolute_filename\", session_date: \"$datetimeformated\", start_audio_time:.words[0].startTime?, start_line_number: \"\", line: .transcript?}" > "$i.lineobjects"
    set wcount (cat "$i.lineobjects" | wc -c)
    echo "Built '$i.lineobjects' $wcount"
end

echo '' > all-sessions.merged-lineobjects
for i in (ls $root_audio_path/*.lineobjects)
    echo "Merging '$i'"
    cat "$i" >> all-sessions.merged-lineobjects
end

cat all-sessions.merged-lineobjects | tantivy index --index session-index-001

##-----------------------------------------------------------------------
## Notes in Markdown
##-----------------------------------------------------------------------

find "$root_notes_path" -iname '*.md' -print0 | xargs --null python3 index_file_by_lines.py session-index-001 
