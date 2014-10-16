#! /bin/sh
chmod 777 .run.sh

alias show_log='more `pwd`/.log'
alias show_log_cmd='more `pwd`/.log | grep CMD'
alias show_log_rcode='more `pwd`/.log | egrep "#>"'
alias show_log_stderr='more `pwd`/.log | egrep "stderr"'
alias show_log_stdout='more `pwd`/.log | egrep "stdout"'
alias show_log_time='more `pwd`/.log | egrep "<#"'

printf "please input scp password: "
read scp_PassWD
printf "please input scp destination path ,such as </usr/local/squid/etc/>:"
read scp_Dst_Path
python3 .certs_dir.py $scp_PassWD $scp_Dst_Path

cmd=''
while [[ $cmd != "quit" ]]; do
    read cmd
    if [[ $cmd == "quit" ]]; then
        break
    fi
    eval $cmd
    printf '\n'
    printf '####'
    printf '\n'    
done

unalias show_log
unalias show_log_cmd
unalias show_log_rcode
unalias show_log_stderr
unalias show_log_stdout
unalias show_log_time
