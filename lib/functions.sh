#!/bin/bash

function list_files_from_find {
    if [[ $opt_verbose = 1 ]]; then
        verbose find ${directories[*]} $cmd_part_ignore -type f -and \( $opt_name_filter \) $cmd_size -print
    fi
    find ${directories[*]} $cmd_part_ignore -type f -and \( $opt_name_filter \) $cmd_size -print
}

command() {
    python $log_retrieve_script -i $1 -o $2
}

function iterate_through_targets {
    local all_files=$1
    local retval=0
    
    N=$parallelism
    i=0
    c=0
    for file in $all_files; do
        c=$(( c + 1 ))
        ((i=i%N)); ((i++==0)) && wait
        output_file=$tmpfile.$c
        command $file $output_file & 
    done
    wait
}

function merge_output_files {
    retrieved_files=$(ls -a | grep -i $tmpfile.[1-9])
    for file in $retrieved_files; do
        (cat "${file}"; echo) >> $tmpfile".all"
        rm "$file"
    done
}

