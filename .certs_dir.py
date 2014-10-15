import sys
import os
import re
import subprocess
import shlex
import io
import time
import datetime
import hashlib
# import jsbeautifier
# import json
import pexpect

# for debug trouble shooting , to display  dict 
# def display(j_Dict,style=1):
    # if(style == 1):
        # print(jsbeautifier.beautify(str(j_Dict)))
    # else:
        # print(json.dumps(j_Dict,sort_keys=True,indent=4))


# shell cmd
def pipe_Shell_CMD(shell_CMDs):
    len = shell_CMDs.__len__()
    p = {}
    p[1] = subprocess.Popen(shlex.split(shell_CMDs[1]), stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    for i in range(2,len):
        p[i] = subprocess.Popen(shlex.split(shell_CMDs[i]), stdin=p[i-1].stdout, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if(len > 1):
        p[len] = subprocess.Popen(shlex.split(shell_CMDs[len]), stdin=p[len-1].stdout, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    result = p[len].communicate()
    if(len > 1):
        for i in range(2,len+1):
            returncode = p[i].wait()
    else:
        returncode = p[len].wait()
    list_Result = list(result)
    list_Result.append(returncode)
    return(list_Result)

# get all group names and certs names  from ./config  and remove note 
def get_Config_Matrix():
    shell_CMDs = {1:'more .config',2:'egrep -v "####"'} 
    tmp_Config_RM_note = pipe_Shell_CMD(shell_CMDs)[0].decode()
    fd = open('.tmp_Work_Dir/.config','w+')
    fd.write(tmp_Config_RM_note)
    fd.close()
    regex_RM_LFCRSPACE = re.compile('\n|\r|" "')
    regex_Config = re.compile('#.*?#',re.DOTALL)
    regex_Each = re.compile('#(.*?)#',re.DOTALL)
    fd = open('.tmp_Work_Dir/.config','r')
    content = fd.read()
    fd.close()
    content = regex_RM_LFCRSPACE.sub('',content,0)
    m = regex_Config.findall(content)
    config_Groups_Certs_Matrix = {}
    for i in range(0,m.__len__()):
        m[i] = eval(regex_Each.search(m[i]).group(1))
        config_Groups_Certs_Matrix[m[i]['equip_group']] = m[i]['certs']
    return(config_Groups_Certs_Matrix)

# 读取配置文件中的组  和  证书  
config_Groups_Certs_Matrix = get_Config_Matrix()

### similiar  to  linux tree function
# if node  is a  DIR  return  'ls DIR'
def is_Leaf(node):
    if(os.path.isdir(node)):
        return(0)
    else:
        return(1)

def get_Sub_Tree_Mehtod(node):
    if(is_Leaf(node)):
        cmd = ''
    else:
        cmd = 'ls {0}'.format(node)
    return(cmd)

def ls_Result_Dict(ls_Result,parent):
    ls_Dict = {}
    ls_List = ls_Result.split('\n')
    ls_List.pop(-1)
    for i in range(1,ls_List.__len__()+1):
        ls_Dict[i] = ''.join((parent,'/',ls_List[i-1]))
    return(ls_Dict)

def get_Sub_Tree_Sons(node,result_Dictize):
    cmd = get_Sub_Tree_Mehtod(node)
    if(cmd==''):
        sons_Dict = {}
    else:
        shell_CMDs = {}
        shell_CMDs[1] = cmd
        result = pipe_Shell_CMD(shell_CMDs)[0].decode()
        sons_Dict = result_Dictize(result,node)
    return(sons_Dict)


###

# 读取当前组 和 证书目录中 的 实际的组合文件
def get_Current_Matrix():
    current_Groups_Certs_Matrix = {}
    groups_Dir_Dict = get_Sub_Tree_Sons(os.getcwd(),ls_Result_Dict)
    for each in groups_Dir_Dict:
        key = os.path.basename(groups_Dir_Dict[each])
        current_Groups_Certs_Matrix[key] = []
        group_Dir = groups_Dir_Dict[each]
        certs_Dir_Dict = get_Sub_Tree_Sons(group_Dir,ls_Result_Dict)
        for i in range(1,certs_Dir_Dict.__len__()+1):
            cert_Dir = certs_Dir_Dict[i]
            certs_Dict = get_Sub_Tree_Sons(cert_Dir,ls_Result_Dict)
            for j in range(1,certs_Dict.__len__()+1):
                regex_IPHN = re.compile('#(.*)')
                m = regex_IPHN.search(os.path.dirname(certs_Dict[j]))
                if(m == None):
                    pass
                else:
                    cert_IPHN = (os.path.basename(certs_Dict[j]),m.group(1))
                    current_Groups_Certs_Matrix[key].append(cert_IPHN)
    return(current_Groups_Certs_Matrix)

current_Groups_Certs_Matrix  = get_Current_Matrix()



# compare all current group names  with all config group names  
# delete group  and certs in group 

def get_Current_Cert_Base_Name(current_Cert_Full_Name):
    regex_Cert_Base = re.compile('(.*)#(.*)')
    m = regex_Cert_Base.search(current_Cert_Full_Name)
    return(m.group(1))

def find_Current_Cert_In_Config(current_Cert_Base_Name,config_Certs_Dir_Dict,config_Certs_Dir_Dict_Len):
    for i in range(0,config_Certs_Dir_Dict_Len):
        if(current_Cert_Base_Name == config_Certs_Dir_Dict[i][0]):
            return(True)
    return(False)


#############################################################################################
for each in current_Groups_Certs_Matrix:
    if(each in config_Groups_Certs_Matrix):# 在当前组 在 配置中的 组, 那么继续深入检查
        current_Certs_Dir_Dict = current_Groups_Certs_Matrix[each]
        current_Certs_Dir_Dict_Len = current_Certs_Dir_Dict.__len__()
        config_Certs_Dir_Dict = config_Groups_Certs_Matrix[each]
        config_Certs_Dir_Dict_Len = config_Certs_Dir_Dict.__len__()
        for i in range(0,current_Certs_Dir_Dict_Len):
            curr_Cert_Full_Name = current_Certs_Dir_Dict[i][0]
            curr_Cert_Base_Name = get_Current_Cert_Base_Name(curr_Cert_Full_Name)
            cond = find_Current_Cert_In_Config(curr_Cert_Base_Name,config_Certs_Dir_Dict,config_Certs_Dir_Dict_Len)
            if(cond):#当前证书存在于配置中
                pass
            else: #删除证书
                curr_Cert_IPHN = current_Groups_Certs_Matrix[each][i]
                curr_Cert_Name = curr_Cert_IPHN[0]
                curr_Cert_IP = curr_Cert_IPHN[1]
                curr_Cert_Dir = '{0}/{1}/{2}#{3}'.format(os.getcwd(),each,cert_Name,cert_IP)
                curr_Cert_Path = '{0}/{1}'.format(curr_Cert_Dir,curr_Cert_Name)
                if(os.path.isdir(curr_Cert_Dir)):
                    pass
                elif(os.path.isdir(os.path.dirname(curr_Cert_Dir))):
                    shell_CMDs = {}
                    shell_CMDs[1] = 'mkdir "{0}/.CRTS_deleted_From_Groups/{1}"'.format(os.getcwd(),os.path.basename(curr_Cert_Dir))
                    list_Result = pipe_Shell_CMD(shell_CMDs)
                else:
                    shell_CMDs = {}
                    shell_CMDs[1] = 'mkdir "{0}/.CRTS_deleted_From_Groups/{1}"'.format(os.getcwd(),each)
                    list_Result = pipe_Shell_CMD(shell_CMDs)
                    shell_CMDs = {}
                    shell_CMDs[1] = 'mkdir "{0}/.CRTS_deleted_From_Groups/{1}"'.format(os.getcwd(),os.path.basename(curr_Cert_Dir))
                    list_Result = pipe_Shell_CMD(shell_CMDs)
                shell_CMDs = {}
                shell_CMDs[1] = 'cp -R "{0}" "{1}/.CRTS_deleted_From_Groups/{2}/"'.format(curr_Cert_Path,os.getcwd(),each)
                list_Result = pipe_Shell_CMD(shell_CMDs)
                shell_CMDs = {}
                shell_CMDs[1] = 'rm -R "{0}"'.format(curr_Cert_Path)
                list_Result = pipe_Shell_CMD(shell_CMDs)
                fd = open('{0}/.log'.format(curr_Cert_Dir),'a+')
                msg = '<{0}>\n<CMD: rm -R "{1}">\n<NOTES: cert {2} deleted>\n<stdout: {3}>\n<stderr: {4}>\n<returncode: {5}#>\n'.format(get_Datetime(),curr_Cert_Path,each,curr_Cert_Name,list_Result[0].decode(),list_Result[1].decode(),list_Result[2])
                print(msg)
                fd.write(msg)
                fd.close()
    else:# 在当前组 当时不在 配置中的 组
        shell_CMDs = {}
        shell_CMDs[1] = 'cp -R "{0}/{1}" "{0}/.CRTS_deleted_From_Groups/{1}"'.format(os.getcwd(),each)
        list_Result = pipe_Shell_CMD(shell_CMDs)
        shell_CMDs = {}
        shell_CMDs[1] = 'rm -R "{0}/{1}"'.format(os.getcwd(),each)
        list_Result = pipe_Shell_CMD(shell_CMDs)
        fd = open('{0}/.log'.format(os.getcwd()),'a+')
        msg = '<{0}>\n<CMD: rm -R "{1}/{2}">\n<NOTES: group {2} deleted>\n<stdout: {3}>\n<stderr: {4}>\n<returncode: {5}#>\n'.format(get_Datetime(),os.getcwd(),each,list_Result[0].decode(),list_Result[1].decode(),list_Result[2])
        print(msg)
        fd.write(msg)
        fd.close()







###########################33














# get date
def get_Datetime():
    date='Wed, 11 Apr 2012 09:37:05 +0800'
    dd=datetime.datetime.strptime(date,'%a, %d %b %Y %H:%M:%S %z')
    current_DD = dd.fromtimestamp(time.time())
    return(current_DD.strftime("#%Y-%m-%d_%H:%M:%S:%f"))

# creat group_Dir for each equip group:
# group_Dir = ''.join((os.getcwd(),'/',each))   #  for each in config_Groups_Certs_Matrix
def check_Equip_Group_Dir(group_Dir):
    logfilename = ''.join((os.getcwd(),'/','.log'))
    fd = open(logfilename,'a+')
    if(os.path.isdir(group_Dir)):
        list_Result = [b'',b'',0]
    else:
        shell_CMDs = {}
        shell_CMDs[1] = 'mkdir "{0}"'.format(group_Dir)
        list_Result = pipe_Shell_CMD(shell_CMDs)
        msg = '<{0}>\n<CMD: mkdir "{1}">\n<stdout: {2}>\n<stderr: {3}>\n<returncode: {4}#>\n'.format(get_Datetime(),group_Dir,list_Result[0].decode(),list_Result[1].decode(),list_Result[2])
        print(msg)
        fd.write(msg)
    fd.close()
    return(list_Result)

# creat cert_Dir for each cert in  each equip group:
# cert_IPHN = config_Groups_Certs_Matrix[each][i] 
# cert_Dir = '{0}#{1}'.format(cert_IPHN[0],cert_IPHN[1])
# cert_Dir = ''.join((group_Dir,'/',cert_Dir))

def check_Cert_Dir(cert_Dir):
    logfilename = ''.join((group_Dir,'/','.log'))
    fd = open(logfilename,'a+')
    if(os.path.isdir(cert_Dir)):
        list_Result = [b'',b'',0]
    else:
        shell_CMDs = {}
        shell_CMDs[1] = 'mkdir "{0}"'.format(cert_Dir)
        list_Result = pipe_Shell_CMD(shell_CMDs)
        msg = '<{0}>\n<CMD: mkdir "{1}">\n<stdout: {2}>\n<stderr: {3}>\n<returncode: {4}#>\n'.format(get_Datetime(),cert_Dir,list_Result[0].decode(),list_Result[1].decode(),list_Result[2])
        print(msg)
        fd.write(msg)
    fd.close()
    return(list_Result)

# compare all config group names  with all current group names
# add group  and certs in group 
# check md5
def check_MD5(filename):
    fd = open(filename,'rb')
    bytes_Content = fd.read()
    m = hashlib.md5()
    m.update(bytes_Content)
    m = hashlib.md5()
    m.update(bytes_Content)      
    return(m.hexdigest())

# 检查将要从.CRTS_ready_To_Groups copy 进入相应group_Dir/Cert_Dir 的证书 是否 已经存在(检查MD5,而不是文件名，因为文件名有时间后缀，每一个都不相同)
# src = ''.join((os.getcwd(),'/.CRTS_ready_To_Groups/',cert_Name))
# dst = ''.join((cert_Dir,'/',cert_Name,'#',get_Datetime())) 
# logfilename = ''.join((os.path.dirname(dst),'/.log',))
def check_Cert(src,dst,config_Cert_IP):
    logfilename = ''.join((os.path.dirname(dst),'/.log',))
    fd = open(logfilename,'a+')
    shell_CMDs = {}
    shell_CMDs = {1:'ls  "{0}"'.format(os.path.dirname(dst)),2:'egrep "{0}"'.format(os.path.basename(src))}
    list_Result = pipe_Shell_CMD(shell_CMDs)
    if(list_Result[0] == b''):
        shell_CMDs = {}
        shell_CMDs[1] = 'cp "{0}" "{1}"'.format(src,dst)
        list_Result = pipe_Shell_CMD(shell_CMDs)
        msg = '<{0}>\n<CMD: cp "{1}" "{2}">\n<stdout: {3}>\n<stderr: {4}>\n<returncode: {5}#>\n'.format(get_Datetime(),src,dst,list_Result[0].decode(),list_Result[1].decode(),list_Result[2])
        print(msg)
        fd.write(msg)
    else:
        src_MD5 = check_MD5(os.path.abspath(src))
        dsts = list_Result[0].decode().split('\n')
        dsts.pop(-1)
        for i in range(0,dsts.__len__()):
            if(check_MD5(''.join((os.path.dirname(dst),'/',dsts[i])))== src_MD5):
                #list_Result = [b'',b'',0]
                shell_CMDs = {}
                shell_CMDs[1] = 'cp "{0}" "{1}"'.format(src,dst)
                list_Result = pipe_Shell_CMD(shell_CMDs)
                msg = '<{0}>\n<CMD: same MD5 already exsit<{1}> but {2} will still be saved>\n<stdout: {3}>\n<stderr: {4}>\n<returncode: {5}#>\n'.format(get_Datetime(),''.join((os.path.dirname(dst),'/',dsts[i])),dst,list_Result[0].decode(),list_Result[1].decode(),list_Result[2])
                print(msg)
                fd.write(msg)
            else:
                shell_CMDs = {}
                shell_CMDs[1] = 'cp "{0}" "{1}"'.format(src,dst)
                list_Result = pipe_Shell_CMD(shell_CMDs)
                msg = '<{0}>\n<CMD: cp "{1}" "{2}">\n<stdout: {3}>\n<stderr: {4}>\n<returncode: {5}#>\n'.format(get_Datetime(),src,dst,list_Result[0].decode(),list_Result[1].decode(),list_Result[2])
                print(msg)
                fd.write(msg)
    #scp
    scpcmd = ''.join(('scp "',src,'" "root@',config_Cert_IP,':',scp_Dst_Path,'"'))
    index,msg = exec_SCP(scpcmd,scp_PassWD)
    if(index < 3):
        print('{0}\n ===>sucessful <{1}>'.format(scpcmd,msg))
        msg = '<{0}>\n<CMD: {1}>\n<stdout: {2}>\n<stderr: {3}>\n<returncode: {4}#>\n'.format(get_Datetime(),scpcmd,dst,msg,'','')
        fd.write(msg)
    else:
        print('{0}\n ===>failed < {1}>'.format(scpcmd,msg))
        msg = '<{0}>\n<CMD: {1}>\n<stdout: {2}>\n<stderr: {3}>\n<returncode: {4}#>\n'.format(get_Datetime(),scpcmd,dst,'',msg,'')
        fd.write(msg)
    #scp
    mv_To = ''.join((os.getcwd(),'/.CRTS_handled_For_Groups/',os.path.basename(src)))
    shell_CMDs = {}
    shell_CMDs = {1:'mv  "{0}" "{1}"'.format(src,mv_To)}
    list_Result = pipe_Shell_CMD(shell_CMDs)
    fd.close()



scp_PassWD = sys.argv[1]
scp_Dst_Path = sys.argv[2]

def exec_SCP(scpcmd,scp_PassWD):
    child = pexpect.spawn(scpcmd)
    index = child.expect(['assword: ','\(yes/no\)\? ',pexpect.EOF,pexpect.TIMEOUT])
    if(index == 0):
        child.send('{0}\r'.format(scp_PassWD))
        index = child.expect(['# ','\$ ',pexpect.EOF,pexpect.TIMEOUT])
    elif(index == 1):
        child.send('yes\r')
        index = child.expect(['assword: ','dumb',pexpect.EOF,pexpect.TIMEOUT])
        if(index>0):
            pass
        else:
            child.send('{0}\r'.format(scp_PassWD))
            index = child.expect(['# ','\$ ',pexpect.EOF,pexpect.TIMEOUT])
    else:
        index = 4
    return((index,child.before.decode('utf-8','ignore')))





for each in config_Groups_Certs_Matrix:
    group_Dir = ''.join((os.getcwd(),'/',each))
    check_Equip_Group_Dir(group_Dir)
    total_Certs = config_Groups_Certs_Matrix[each].__len__()
    for i in range (0,total_Certs):
        cert_IPHN = config_Groups_Certs_Matrix[each][i]
        cert_Name = cert_IPHN[0]
        cert_IP = cert_IPHN[1]
        cert_Dir = '{0}#{1}'.format(cert_Name,cert_IP)
        #如果更换了IP 会产生一个新文件夹
        cert_Dir = ''.join((group_Dir,'/',cert_Dir))
        check_Cert_Dir(cert_Dir)
        src = ''.join((os.getcwd(),'/.CRTS_ready_To_Groups/',cert_Name))
        dst = ''.join((cert_Dir,'/',cert_Name,get_Datetime()))
        check_Cert(src,dst,cert_IP)


###################################################################################
# chmod 777 .run.sh

# alias show_log='more `pwd`/.log'
# alias show_log_cmd='more `pwd`/.log | grep CMD'
# alias show_log_rcode='more `pwd`/.log | egrep "#>"'
# alias show_log_stderr='more `pwd`/.log | egrep "stderr"'
# alias show_log_stdout='more `pwd`/.log | egrep "stdout"'
# alias show_log_time='more `pwd`/.log | egrep "<#"'

# printf "please input scp password: "
# read scp_PassWD
# printf "please input scp destination path ,such as </usr/local/squid/etc/>:"
# read scp_PassWD
# python3 .certs_dir.py $scp_PassWD $scp_Dst_Path

# cmd=''
# while [[ $cmd != "quit" ]]; do
    # read cmd
    # if [[ $cmd == "quit" ]]; then
        # break
    # fi
    # eval $cmd
    # printf "\n"
    # printf "####"
    # printf "\n"
# done


# unalias show_log
# unalias show_log_cmd
# unalias show_log_rcode
# unalias show_log_stderr
# unalias show_log_stdout
# unalias show_log_time

# source .run.sh
###################################################################################


