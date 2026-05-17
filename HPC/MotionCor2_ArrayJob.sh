#!/bin/bash
#
# Execute this as follows:
# ./motioncor2_array_job_prep.sh -d path_to_directory_with_mrcs -of _output.mrc -lf _log.txt -dpn 2
 
helpfunction()
{
    echo -e "Usage:    `basename $0` [OPTION] [ARGUMENT]... FILE_TO_CREATE"
    echo -e "Options:"
    echo -e "Required:"
    echo -e "\t-d, --directory path_to_directory"
    echo -e "\t\t\tpath to the directory containing the MRC files to"
    echo -e "\t\t\tbe processed."
    echo -e "\t-of, --outputfile string_to_append_to_output_file"
    echo -e "\t\t\tString to append to the filename for the corrected"
    echo -e "\t\t\tresults."
    echo -e "Optional:"
    echo -e "\t-lf, --logfile string_to_append_to_log_file"
    echo -e "\t\t\t-String to append to the filename for the log file."
    echo -e "\t-dpn, --devicespernode number"
    echo -e "\t\t\tNumber of GPU devices available on a node."
    echo -e "\t-h, --help"
    echo -e "\t\t\tPrint this help information"
    exit 1
}
while [[ $# -gt 1 ]]
do
key="$1"
case $key in
    -d|--directory)
    DIRECTORY="$2"
    shift # past argument
    ;;
    -of|--outputfile)
    OUTPUTFILE="$2"
    shift # past argument
    ;;
    -lf|--logfile)
    LOGFILE="$2"
    shift # past argument
    ;;
    -dpn|--devicespernode)
    DEVICES="$2"
    shift # past argument
    ;;
    -h|--help)
    HELP="1"
    ;;
    *)
            # unknown option
    ;;
esac
shift # past argument or value
done
if [[ $HELP == 1 ]]; then
    helpfunction
fi
if [[ -z $DIRECTORY ]] || [[ -z $OUTPUTFILE ]] || [[ -z $1 ]]; then
    echo "ERRROR:"
    echo "Missing one or more required options."
    echo ""
    helpfunction
    exit 2
fi
if [[ -n ${DEVICES} ]]; then
    gpu_num="0"
    for i in $( ls ${DIRECTORY}/*.mrc ); do
        filename=`basename ${i}`
        inmrc=${filename}
        outmrc=${filename%.mrc}${OUTPUTFILE}
        if [[ -n $LOGFILE ]]; then
            logfile="-LogFile ${filename%.mrc}${LOGFILE}"
        fi
        if [[ ${gpu_num} -eq ${DEVICES} ]]; then
            gpu_num="0"
        fi
        gpu="-Gpu ${gpu_num}"
        echo "-InMrc ${inmrc} -OutMrc ${outmrc} ${logfile} ${gpu}" >> ${DIRECTORY}/${1}
        gpu_num=$[$gpu_num+1]
    done
    echo "Use this in your job submission script #PBS -t 1-`cat ${DIRECTORY}/${1} | wc -l`"
    exit 0
fi
if [[ -z ${DEVICES} ]]; then
    for i in $( ls ${DIRECTORY}/*.mrc ); do
        filename=`basename ${i}`
        inmrc=${filename}
        outmrc=${filename%.mrc}${OUTPUTFILE}
        if [[ -n $LOGFILE ]]; then
            logfile="-LogFile ${filename%.mrc}${LOGFILE}"
        fi
        echo "-InMrc ${inmrc} -OutMrc ${outmrc} ${logfile}" >> ${DIRECTORY}/${1}
    done
    echo "Use this in your job submission script #PBS -t 1-`cat ${DIRECTORY}/${1} | wc -l`"
 
    exit 0
fi
