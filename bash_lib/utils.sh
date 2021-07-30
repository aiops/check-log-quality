#!/bin/bash

function warning {
    echo "check-log-quality: $*" >&2
}
export -f warning

function verbose {
    if [[ $opt_verbose = 1 ]]; then
        warning "$@"
    fi
}
export -f verbose

function debug {
    if [[ $opt_debug = 1 ]]; then
        warning "$@"
    fi
}
export -f debug

function initialise_variables {
    set -f

    export LC_CTYPE=C
    export LANG=C

    export opt_debug=0
    export opt_verbose=0

    export tmpfile=".retrieved-logs"

    # Define log message retrieve scripts based on file extension
    retrieve_py="$source_directory/log_quality/retrieve_logs/retriever_py_ast.py"
    declare -gA retrieve_scripts=( [".py"]=$retrieve_py )
    export retrieve_scripts

    # Define log quality checking script
    check_quality_py="$source_directory/log_quality/log_quality/main.py"
    export check_quality_py

    # Build filter for find call
    cmd_part_include_files=""
    for file_extension in ${!retrieve_scripts[@]}; do
        if [ -z "${cmd_part_include_files}" ]; then
            cmd_part_include_files="-iname *$file_extension"
        else
            cmd_part_include_files="$cmd_part_include_files -o -iname *$file_extension"
        fi
    done
    export cmd_part_include_files

    # Ignore version directories
    export cmd_part_ignore_scm="\
        -o -iname .git\
        -o -iname .svn\
        -o -iname .hg\
        -o -iname CVS"
    
    export parallelism=1

    export opt_name_filter=''
    export cmd_size="-and ( -size -1024k )"  # find will ignore files > 1MB

    export directories
}

function process_command_arguments {
    local OPTIND
    while getopts ":dvfimN:P:" opt; do
        case $opt in
            d)
                warning "-d Enable debug mode."
                opt_debug=1
                bash_arg=x
            ;;
            v)
                warning "-v Enable verbose mode."
                opt_verbose=1
            ;;
            f)
                warning "-f Enable fast mode. (Equivalent with -P4)"
                parallelism=4
            ;;
            i)
                warning "-i Disable scm dir ignoring."
                cmd_part_ignore_scm=''
            ;;
            m)
                warning "-m Disable max-size check. Default is to ignore files > 1MB."
                cmd_size=" "
            ;;
            N)
                warning "-N Enable name filter: $OPTARG"
                if [ -z "$opt_name_filter" ]; then
                    opt_name_filter="-name $OPTARG"
                else
                    opt_name_filter="$opt_name_filter -or -name $OPTARG"
                fi
            ;;
            P)
                warning "-P Enable parallelism: $OPTARG"
                reg="^[1-9]([0-9]+)?"
                if ! [[ $OPTARG =~ $re ]] ; then
                    warning "error: Parallelsim must be an integer" 
                    exit 11
                else
                    parallelism=$OPTARG
                fi
            ;;
            \?)
                warning "Invalid option: -$OPTARG"
                return 100
            ;;
            :)
                warning "Option -$OPTARG requires an argument."
                return 101
            ;;
        esac
    done

    if [ -z "$opt_name_filter" ]; then
        opt_name_filter='-true'
    fi

    shift $((OPTIND-1))

    if [[ "$*" = "" ]]; then
        warning "Not enough arguments."\
            "(target directory not found) => Exiting."
        return 102
    fi

    directories=( "$@" )
    cmd_part_ignore="(\
        -iname $tmpfile*\
        $cmd_part_ignore_scm\ 
        ) -prune -o "
    warning "Target directories: ${directories[*]}"

    return 0
}
