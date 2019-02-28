from django.http import HttpResponse
#from django.shortcuts import render

import subprocess


def index(request):
    p = subprocess.Popen(["/home/ujcb52/test.sh"], stdout=subprocess.PIPE, shell=True)
    jsonresult = p.stdout.read()

    return HttpResponse(jsonresult, content_type="application/json")

