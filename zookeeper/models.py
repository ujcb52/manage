from django.db import models


class node(models.Model):
    privateIpId = models.AutoField(primary_key=True)
#    privateIpId = models.IntegerField(default=0)
    privateIp = models.CharField(max_length=15)
    hosttype = models.CharField(max_length=40, blank=True, null=True)
    state = models.CharField(max_length=5)
    createtime = models.DateTimeField()
    deletetime = models.DateTimeField(blank=True, null=True)


class excludelist(models.Model):
#    privateIpId = models.IntegerField(default=0)
# on_delete = models.CASCADE 원본 삭제시 같이 삭제. SET_NULL 로 설정 null=True 값은 필수
#    privateIpId = models.ForeignKey('node', on_delete=models.CASCADE)
    privateIpId = models.ForeignKey('node', on_delete=models.SET_NULL, null=True)
    text = models.CharField(max_length=200)
    state = models.CharField(max_length=10)
    createtime = models.DateTimeField()
    deletetime = models.DateTimeField(blank=True, null=True)


class sendlist(models.Model):
#    privateIpId = models.IntegerField(default=0)
    privateIpId = models.ForeignKey('node', on_delete=models.SET_NULL, null=True)
    text = models.CharField(max_length=200)
    createtime = models.DateTimeField()

class daemon(models.Model):
    state = models.CharField(max_length=10)
    msgconfig = models.CharField(max_length=10, null=True)
    delay = models.CharField(max_length=3, null=True)
