#!/bin/bash

function list_files_from_find {
    if [[ $opt_verbose = 1 ]]; then
        verbose find ${directories[*]} $cmd_part_ignore -type f -and \( $opt_name_filter \) $cmd_size -print
    fi
    find ${directories[*]} $cmd_part_ignore -type f -and \( $opt_name_filter \) $cmd_size -print
}

function iterate_through_targets {
    local file_lister_function=$1
    local retval=0

    "$file_lister_function"|\
    while read -r filename; do
        printf '%s\0' "$filename"
    done|\
    tee\
        >($prefilter_progress_function)\
        >(xargs\
            -0\
            $cmd_part_parallelism\
            -n 100\
            python 
        )\
    
    return $retval
}

function prefilter_progress_none {
    cat >/dev/null
}

function prefilter_progress_dots {
    while IFS= read -r -d '' filename; do
        echo -n "." >&2
    done
}
