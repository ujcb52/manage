from django.http import HttpResponseRedirect
#from django.template import loader
from django.shortcuts import render
#from django.db.models import Q

from .models import node, excludelist, sendlist, daemon

import datetime, os, subprocess

def index(request):
    cmd = "ps -ef | grep 'python3.6 /home/ujcb52/scripts/zookeeper-watcher.py' |grep -v 'grep' | awk '{print $2}'"
    check = subprocess.check_output([cmd], stderr=subprocess.STDOUT, shell=True)
#    subprocess 의 경우 stdout 은 byte 로 넘어온다. string 으로는 decode 필요
#    print(type(check))
#    print(check.decode("utf-8"))
    if check:
#        print("## check is not null ##")
        p = daemon.objects.filter(pk=1)
        p.update(state='running')
    else:
#        print("## check is null ##")
        p = daemon.objects.filter(pk=1)
        p.update(state='stop')

    daemonstate = daemon.objects.order_by('state')
    context = {'daemon' : daemonstate}
    return render(request, 'zookeeper/index.html', context)


def nodelist(request):
    node_list = node.objects.order_by('privateIpId')
    context = {'node_list' : node_list}
    return render(request, 'zookeeper/nodelist.html', context)


def excludenode(request):
#    exclude_list = excludelist.objects.filter(node_list=node_list).select_related()
#    exclude_list = excludelist.objects.filter(state='normal', ~Q(privateIpId_id=NULL)).order_by('-createtime')
    exclude_list = excludelist.objects.filter(privateIpId__isnull=False, state='normal').order_by('-createtime')
    context = {'exclude_list' : exclude_list}
    return render(request, 'zookeeper/excludelist.html', context)


def sendmsg(request):
#    send_list = sendlist.objects.order_by('-createtime')[:5]
    send_list = sendlist.objects.order_by('-createtime')
    context = {'send_list' : send_list}
    return render(request, 'zookeeper/sendlist.html', context)


def DeleteNode(request):
    urls = "http://182.162.104.10:8880/zookeeper/nodelist/"
    try:
        privateIpId = request.GET['privateIpId']
        p = node.objects.get(privateIpId=privateIpId)
        p.delete()
    except:
        return HttpResponseRedirect(urls)
    return HttpResponseRedirect(urls)


def DeleteExclude(request):
    urls = "http://182.162.104.10:8880/zookeeper/excludenode/"
    try:
        privateIpId = request.GET['privateIpId']
        p = excludelist.objects.filter(privateIpId=privateIpId)
        p.update(state='delete')
    except:
        return HttpResponseRedirect(urls)
    return HttpResponseRedirect(urls)


#@csrf_exempt
def InsertExclude(request):
    urls = "http://182.162.104.10:8880/zookeeper/excludenode/"
    try:
        privateIp = request.POST['privateIp'].strip()
        nodeIpId = node.objects.filter(privateIp=privateIp).values('privateIpId')
        text = request.POST['text']
        now = datetime.datetime.now()
        p = excludelist.objects.create(privateIpId_id=nodeIpId[0]['privateIpId'], text=text, createtime=now, state='normal')
        p.save()
    except:
        return HttpResponseRedirect(urls)

#    br = excludelist (privateIpId_id = int(nodeIpId),
#                      text = texts,
#                      createtime = now
#                     )
#    br.save()
    return HttpResponseRedirect(urls)


def DaemonState(request):
    urls = "http://182.162.104.10:8880/zookeeper/"
    try:
        state = request.GET['state']
        if state == 'running':
            os.system('python3.6 /home/ujcb52/scripts/zookeeper-watcher.py &')
            p = daemon.objects.filter(pk=1)
            p.update(state='running')
        elif state == 'stop':
            cmd = "kill -9 `ps -ef | grep 'python3.6 /home/ujcb52/scripts/zookeeper-watcher.py' |grep -v 'grep' | awk '{print $2}'`"
            subprocess.Popen(cmd, shell=True).communicate()
            p = daemon.objects.filter(pk=1)
            p.update(state='stop')
        elif state == 'check':
#            subprocess 의 경우 stdout 은 byte 로 넘어온다. string 으로는 decode 필요
            cmd = "ps -ef | grep 'python3.6 /home/ujcb52/scripts/zookeeper-watcher.py' |grep -v 'grep' | awk '{print $2}'"
            check = subprocess.check_output([cmd], stderr=subprocess.STDOUT, shell=True)
            if check:
                p = daemon.objects.filter(pk=1)
                p.update(state='running')
            else:
                p = daemon.objects.filter(pk=1)
                p.update(state='stop')
    except:
        return HttpResponseRedirect(urls)

    return HttpResponseRedirect(urls)


def MsgState(request):
    urls = "http://182.162.104.10:8880/zookeeper/"
    try:
        msgstate = request.GET['msgstate']
#        delay = request.GET['delay']
        if msgstate == 'yes':
            p = daemon.objects.filter(pk=1)
            p.update(msgconfig='yes')
        elif msgstate == 'no':
            p = daemon.objects.filter(pk=1)
            p.update(msgconfig='no')
    except:
        return HttpResponseRedirect(urls)

    return HttpResponseRedirect(urls)


def MsgDelay(request):
    urls = "http://182.162.104.10:8880/zookeeper/"
    try:
        delay = request.POST['delay'].strip()
        p = daemon.objects.update(delay=delay, msgconfig='yes')
        p.save()
    except:
        return HttpResponseRedirect(urls)

#    br = excludelist (privateIpId_id = int(nodeIpId),
#                      text = texts,
#                      createtime = now
#                     )
#    br.save()
    return HttpResponseRedirect(urls)


def check_privateIp(request):
    pass
