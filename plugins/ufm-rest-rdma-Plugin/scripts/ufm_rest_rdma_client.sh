#!/bin/bash -eE
running_dir="`dirname $0`"
running_dir=`cd $running_dir; pwd`
ufm_rdma_utility_name=/opt/ufm/ufm-plugin-ufm-rest/src/ufm_rdma.py
#--------------------------------------------------------------------------------------
usage() {
    echo "Usage: "
    echo -e "    Run $basename to start  \n"
    echo -e " -i     ib device name (mlx5_0, mlx5_1 ...) - to be used for data transfer"
    echo -e " -s     name or IP address of UFM server (optional - if not set - localhost will be used. Must for client certificate.)"
    echo -e " -t     requested action type (simple, ibdiagnet, complicated)"
    echo -e " -a     REST action (GET,POST,PUT,PATCH,DELETE)"
    echo -e " -u     username to connect UFM server"
    echo -e " -p     password to connect UFM server"
    echo -e " -w     reqested REST URL"
    echo -e " -l     reqested REST payload"
    echo -e " -c     Path to the config file name."
    echo -e " -d     Path to the client certificate file name (located inside docker container)."
    echo -e " -k     Token for authentication."
    echo -e " -v     Get utility version."
    echo -e " -h     Show help"
    echo -e "\nExamples:"
    echo -e "     $0 -u username -p password -t ibdiagnet -a POST -w ufmRest/reports/ibdiagnetPeriodic -l '{"general": {"name": "IBDiagnet_CMD_1234567890_199", "location": "local", "running_mode": "once"}, "command_flags": {"--pc": ""}}'"
    echo -e "     $0 -u username -p password -t simple -a GET -w ufmRest/resources/systems"
    echo -e "     $0 -k [token string] -t simple -a GET -w ufmRestV3/app/ufm_version"
    echo -e "     $0 -s [defined for client certificate host name] -d [path to client certificate pfx file] -t simple -a GET -w ufmRest/app/ufm_version"
    echo
}

get_version() {
    command_line="docker exec ufm-plugin-ufm-rest $ufm_rdma_utility_name -v"
    eval $command_line
}

# #--------------------------------------------------------------------------------------
parse_args() {
    while getopts :h:i:u:p:a:t:w:l:s:c:d:k:v opt 
        do
        #echo $opt, "-----------------------------------------------------------"
        case "$opt" in
        i)
            port_name=${OPTARG}
            ;;
        l)
            payload=${OPTARG}
            ;;
        a)
            action=${OPTARG}
            ;;
        w)
            rest_url=${OPTARG}
            ;;
        t)
            action_type=${OPTARG}
            ;;
        u)
            username=${OPTARG}
            ;;
        p)
            password=${OPTARG}
            ;;
        s)
            server_name=${OPTARG}
            ;;
        c)  
            config_file=${OPTARG}
            ;;
        d)
            client_certificate=${OPTARG}
            ;;
        k)
            token=${OPTARG}
            ;;
        v)
            get_version
            exit 0
            ;;
        h)
            usage
            exit 0
            ;;
        *)
            usage
            exit 1
            ;;
        esac
    done
}

if [ $# -eq 0 ];
then
   usage
   exit 0
fi

parse_args "$@"

command_line="docker exec ufm-plugin-ufm-rest $ufm_rdma_utility_name -r client -t $action_type -a $action -w $rest_url"
if [ ! -z $token ];
then
    command_line+=" -k $token"
fi
if [ ! -z $client_certificate ];
then
    command_line+=" -d $client_certificate"
fi
if [ ! -z $config_file ];
then
    command_line+=" -c $config_file"
fi
if [ ! -z $username ];
then
    command_line+=" -u $username"
fi
if [ ! -z $password ];
then
    command_line+=" -p $password"
fi
if [ ! -z $server_name ];
then
    command_line+=" -s $server_name"
fi
if [ ! -z "${payload}" ];
then
    command_line+=" -l \"$payload\""
fi

eval $command_line

