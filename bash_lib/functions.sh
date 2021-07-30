#!/bin/bash

function list_files_from_find {
    if [[ $opt_verbose = 1 ]]; then
        verbose find ${directories[*]} $cmd_part_ignore -type f -and \( $cmd_part_include_files \) -and \( $opt_name_filter \) $cmd_size -print
    fi
    find ${directories[*]} $cmd_part_ignore -type f -and \( $cmd_part_include_files \) -and \( $opt_name_filter \) $cmd_size -print
}

function parallel_command {
    python $1 -i $2 -o $3
}

function get_file_extension {
    debug "Extracting file extension from $1"

    filename=$(basename -- "$1")
    debug "File name : $filename"

    extension=$([[ "$filename" = *.* ]] && echo ".${filename##*.}" || echo '')
    debug "Extracted extension: $extension"

    echo $extension
}

function iterate_through_targets {
    local all_files=$1
    local all_files_arr=( $1 )
    local retval=0
    
    N=$parallelism
    i=0
    c=0
    for file in $all_files; do
        file_extension=$(get_file_extension $file)
        if [ -z "${file_extension}" ]; then
            verbose "Cannot extract file extension from $file."
            continue
        fi

        if [[ -z ${retrieve_scripts[${file_extension}]} ]]; then
            verbose "File extension $file_extension is not supported."
            continue
        fi

        c=$(( c + 1 ))
        ((i=i%N)); ((i++==0)) && wait
        
        echo -ne "Files processed: $c / ${#all_files_arr[@]}\r"

        retrieve_script=${retrieve_scripts[${file_extension}]}
        output_file=$tmpfile.$c
        parallel_command $retrieve_script $file $output_file & 
    done
    wait
}

function merge_output_files {
    rm $tmpfile".all" 2> /dev/null
    retrieved_files=$(ls -a | grep -i $tmpfile.[1-9])
    for file in $retrieved_files; do
        (cat "${file}"; echo) | awk NF >> $tmpfile".all"
        rm "$file"
    done
}

function check_quality {
    log_data_file=$tmpfile".all"
    python $1 -i $log_data_file
    rm "$log_data_file"
}
