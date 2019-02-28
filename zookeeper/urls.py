from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='index'),
#    path('show_write_form/', views.show_write_form),
    path('DeleteNode/', views.DeleteNode),
    path('DeleteExclude/', views.DeleteExclude),
    path('InsertExclude/', views.InsertExclude),
    path('nodelist/', views.nodelist),
    path('excludenode/', views.excludenode),
    path('sendmsg/', views.sendmsg),
    path('DaemonState/', views.DaemonState),
    path('MsgState/', views.MsgState),
    path('MsgDelay/', views.MsgDelay),
]

