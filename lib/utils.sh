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

function initialise_variables {
    set -f

    export LC_CTYPE=C
    export LANG=C

    export opt_debug=0
    export opt_verbose=0
    export opt_show_diff=0
    export opt_real_run=0
    export opt_backup=1
    export opt_dots=0
    export bash_arg

    export opt_whitelist_save=0
    export opt_whitelist_filename=".check-log-quality.ignore"

    export tmpfile=.check-log-quality.$$

    export cmd_part_ignore_scm="\
        -o -iname .git\
        -o -iname .svn\
        -o -iname .hg\
        -o -iname CVS"
    export cmd_part_ignore_bin="\
        -o -iname *.gif\
        -o -iname *.jpg\
        -o -iname *.jpeg\
        -o -iname *.png\
        -o -iname *.zip\
        -o -iname *.gz\
        -o -iname *.bz2\
        -o -iname *.xz\
        -o -iname *.rar\
        -o -iname *.po\
        -o -iname *.pdf\
        -o -iname *.woff\
        -o -iname *.mov\
        -o -iname *.mp4\
        -o -iname *.jar\
        -o -iname yarn.lock\
        -o -iname package-lock.json\
        -o -iname composer.lock\
        -o -iname *.mo"
    export cmd_part_ignore

    export cmd_part_parallelism

    export loop_function=apply_check_on_one_file
    export prefilter_progress_function=prefilter_progress_none

    export opt_name_filter=''
    export cmd_size="-and ( -size -1024k )"  # find will ignore files > 1MB

    export directories

    echo '/// ///' >$tmpfile.git.ignore
    trap 'rm -f $tmpfile.git.ignore' EXIT

    GREP=$(ggrep --version >/dev/null 2>&1 && \
        echo 'ggrep' || \
        echo 'grep')
    export GREP
}

function process_command_arguments {
    local OPTIND
    while getopts ":dvofibGmhN:P:w:" opt; do
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
            o)
                warning "-o Print dots for each file scanned."
                opt_dots=1
                prefilter_progress_function=prefilter_progress_dots
            ;;
            f)
                warning "-f Enable fast mode. (Equivalent with -P4)"
                cmd_part_parallelism="-P 4"
            ;;
            i)
                warning "-i Disable scm dir ignoring."
                cmd_part_ignore_scm=''
            ;;
            b)
                warning "-b Disable binary ignoring."
                cmd_part_ignore_bin=''
            ;;
            G)
                warning "-G Apply .gitignore."
                git ls-files --others --ignored --exclude-standard|\
                while read -r filename; do
                    printf './%s' "$filename"
                done >$tmpfile.git.ignore
            ;;
            m)
                warning "-m Disable max-size check. Default is to ignore files > 1MB."
                cmd_size=" "
            ;;
            N)
                warning "-N Enable name filter: $OPTARG"
                if [ -n "$opt_name_filter" ]; then
                    opt_name_filter="$opt_name_filter -or -name $OPTARG"
                else
                    opt_name_filter="-name $OPTARG"
                fi
            ;;
            P)
                warning "-P Enable parallelism: $OPTARG"
                cmd_part_parallelism="-P $OPTARG"
            ;;
            h)
                d="dirname ${BASH_SOURCE[0]}"
                if [[ -f "$($d)"/../README.md ]]; then
                    cat "$($d)"/../README.md
                else
                    zcat /usr/share/doc/check-log-quality/README.md.gz
                fi
                return 10
            ;;
            w)
                warning "-w Use $OPTARG as white list file instead of "\
                    "$opt_whitelist_filename."
                opt_whitelist_filename=$OPTARG
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
        -o -iname $opt_whitelist_filename\
        -o -iname *.BAK\
        $cmd_part_ignore_scm $cmd_part_ignore_bin\
        ) -prune -o "
    warning "Target directories: ${directories[*]}"

    if [[ $opt_show_diff = 1 ||\
        $opt_backup = 1 ||\
        $opt_real_run = 0 ||\
        $opt_verbose = 1 ]]
    then
        loop_function=decorate_one_iteration
    fi

    return 0
}