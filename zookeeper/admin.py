from django.contrib import admin
from .models import excludelist, node, sendlist 

admin.site.register(excludelist)
admin.site.register(node)
admin.site.register(sendlist)
