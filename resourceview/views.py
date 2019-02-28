from django.shortcuts import render
from django.http import HttpResponse

import glob, datetime, subprocess, json, sys, re, copy, os, httplib2, smtplib, configparser, io, time, ipaddress
from http.client import HTTPConnection
from email.mime.text import MIMEText
from operator import itemgetter

config = configparser.ConfigParser()
config.read('/home/ujcb52/fabric/jw_dailyparam/conf/config.ini')

ccip = config['mgmtsrvlist']['CC'] + ':8111'
ckey = config['farm']['key']

def index(request):
    url = "http://"+ccip+"/"+ckey+"/resourceView"
    h = httplib2.Http('/home/ujcb52/web/manage/resourceview/.cache')
    response, content = h.request(url)
    result = json.loads(content.decode('utf-8'))

    for hostList in result['zoneId']:
        if 'zone_1' in hostList:
            hosts = hostList['zone_1']['nodes']
            context1_1 = helpcount2(hosts, 'zone_1')
            ip = hostList['zone_1']['zones']
            context1_2 = helpcount3(ip, 'zone_1')
            context1_1.update(context1_2)
            context1 = { 'Zone_1' : context1_1 }
        elif 'zone_2' in hostList:
            hosts = hostList['zone_2']['nodes']
            context2_1 = helpcount2(hosts, 'zone_2')
            ip = hostList['zone_2']['zones']
            context2_2 = helpcount3(ip, 'zone_2')
            context2_1.update(context2_2)
            context2 = { 'Zone_2' : context2_1 }

    context1.update(context2)
    context = { 'zone_list' : context1 }
    return render(request, 'resourceview/index.html', context)


# 공인IP 사용률 계산
def helpcount3(ip, zone=None):
    for i in ip:
        if zone == 'zone_1':
            if i['ipType'] == 'basic':
                basic_ipAvailable = i['ipAvailable']
                basic_ipTotal = i['ipTotal']
                basic_ipZone = i['ipZone']
                basic_ipUsage = i['ipUsage']
                basic_perc_Used = 100 - (100 * basic_ipAvailable // basic_ipTotal)
            elif i['ipType'] == 'vps':
                vps_ipAvailable = i['ipAvailable']
                vps_ipTotal = i['ipTotal']
                vps_ipZone = i['ipZone']
                vps_ipUsage = i['ipUsage']
                vps_perc_Used = 100 - (100 * vps_ipAvailable // vps_ipTotal)
            ip_std_perc = int(config['vmused_std_perc']['ip']) + 5
        elif zone == 'zone_2':
            if i['ipType'] == 'basic':
                basic_ipAvailable = i['ipAvailable']
                basic_ipTotal = i['ipTotal']
                basic_ipZone = i['ipZone']
                basic_ipUsage = i['ipUsage']
                basic_perc_Used = 100 - (100 * basic_ipAvailable // basic_ipTotal)
                ip_std_perc = int(config['vmused_std_perc']['ip'])
    cnt1 = 0
    if basic_perc_Used > ip_std_perc:
        basic_over_perc = basic_perc_Used - ip_std_perc
        for x in range(1,1000):
            result = 100 - (( 100 * ( basic_ipAvailable + x )) // ( basic_ipTotal + x ))
            if result <= ip_std_perc:
                break
        basic_ip_cnt = x
        cnt1 = 1
    cnt2 = 0
    if zone == 'zone_1':
        if vps_perc_Used > ip_std_perc:
            vps_over_perc = vps_perc_Used - ip_std_perc
            for x in range(1,1000):
                result = 100 - (( 100 * ( vps_ipAvailable + x )) // ( vps_ipTotal + x ))
                if result <= ip_std_perc:
                    break
            vps_ip_cnt = x
            cnt2 = 1

    if zone == 'zone_1':
        dict_result_1 = {'basic_ipAvailable' : basic_ipAvailable, 'basic_ipTotal' : basic_ipTotal, 'basic_ipZone' : basic_ipZone,
                'basic_ipUsage' : basic_ipUsage, 'basic_perc_Used' : basic_perc_Used,
                'vps_ipAvailable' : vps_ipAvailable, 'vps_ipTotal' : vps_ipTotal, 'vps_ipZone' : vps_ipZone,
                'vps_ipUsage' : vps_ipUsage, 'vps_perc_Used' : vps_perc_Used}
        if cnt1 == 1:
            dict_result_1.update({'ip_std_perc' : ip_std_perc, 'basic_over_perc' : basic_over_perc, 'basic_ip_cnt' : basic_ip_cnt})
        if cnt2 == 1: 
            dict_result_1.update({'vps_over_perc' : vps_over_perc, 'vps_ip_cnt' : vps_ip_cnt })
        return dict_result_1
    elif zone == 'zone_2':
        dict_result_2 = {'basic_ipAvailable' : basic_ipAvailable, 'basic_ipTotal' : basic_ipTotal, 'basic_ipZone' : basic_ipZone,
                        'basic_ipUsage' : basic_ipUsage, 'basic_perc_Used' : basic_perc_Used}
        if cnt1 == 1:
            dict_result_2.update({'ip_std_perc' : ip_std_perc, 'basic_over_perc' : basic_over_perc, 'basic_ip_cnt' : basic_ip_cnt })
        return dict_result_2

# helpcount 함수에서 NC 1대 기준으로 계산된 값을 합산한다.
# 전체 용량 대비 사용률을 구한다.
def helpcount2(hosts,zone=None):
    basic_tcnt_8 = 0
    basic_avcnt_8 = 0
    basic_tcnt_16 = 0
    basic_avcnt_16 = 0
    premium_tcnt_32 = 0
    premium_avcnt_32 = 0
    premium_tcnt_64 = 0
    premium_avcnt_64 = 0
    premium_tcnt_128 = 0
    premium_avcnt_128 = 0
    SSD_tcnt_8 = 0
    SSD_avcnt_8 = 0
    SSD_tcnt_16 = 0
    SSD_avcnt_16 = 0
    SSD_tcnt_32 = 0
    SSD_avcnt_32 = 0
    MSSQL_tcnt_8 = 0
    MSSQL_avcnt_8 = 0
    MSSQL_tcnt_16 = 0
    MSSQL_avcnt_16 = 0
    WAF_tcnt_4 = 0
    WAF_avcnt_4 = 0
    WAF_tcnt_8 = 0
    WAF_avcnt_8 = 0
    VPS_tcnt_2 = 0
    VPS_avcnt_2 = 0
    VPS_tcnt_4 = 0
    VPS_avcnt_4 = 0

    for host in hosts:
        if host['state'] == 'normal':
            if host['deployable'] == 1:
                if host['target'] == 'n':
                    if host['hostTypeId'] == 1:
                        # helpercount 함수에서 사용률 계산을 한다.
                        # 총 개수, 생성 가능 개수, 이에 따른 사용률 %를 계산.
                        result = helpercount(host)
                        basic_tcnt_8 += result['basic_t8']
                        basic_avcnt_8 += result['basic_av8']
                        basic_tcnt_16 += result['basic_t16']
                        basic_avcnt_16 += result['basic_av16']
                    elif host['hostTypeId'] == 2:
                        result = helpercount(host)
                        premium_tcnt_32 += result['premium_t32']
                        premium_avcnt_32 += result['premium_av32']
                        premium_tcnt_64 += result['premium_t64']
                        premium_avcnt_64 += result['premium_av64']
                        premium_tcnt_128 += result['premium_t128']
                        premium_avcnt_128 += result['premium_av128']
                    # HostType 5, 'SSD'
                    elif host['hostTypeId'] == 5:
                        result = helpercount(host)
                        # SSD 8G size
                        SSD_tcnt_8 += result['SSD_t8']
                        SSD_avcnt_8 += result['SSD_av8']
                        # SSD 16G size
                        SSD_tcnt_16 += result['SSD_t16']
                        SSD_avcnt_16 += result['SSD_av16']
                        # SSD 32G size
                        SSD_tcnt_32 += result['SSD_t32']
                        SSD_avcnt_32 += result['SSD_av32']
                    # HostType 9, 'MSSQL'
                    elif host['hostTypeId'] == 9:
                        result = helpercount(host)
                        # MSSQL 8G size
                        MSSQL_tcnt_8 += result['MSSQL_t8']
                        MSSQL_avcnt_8 += result['MSSQL_av8']
                        # MSSQL 16G size
                        MSSQL_tcnt_16 += result['MSSQL_t16']
                        MSSQL_avcnt_16 += result['MSSQL_av16']
                    # HostType 3, 'WAF'
                    elif host['hostTypeId'] == 3:
                        result = helpercount(host)
                        # WAF 4G size
                        WAF_tcnt_4 += result['WAF_t4']
                        WAF_avcnt_4 += result['WAF_av4']
                        # WAF 8G size
                        WAF_tcnt_8 += result['WAF_t8']
                        WAF_avcnt_8 += result['WAF_av8']
                    # HostType 7, 'VPS'
                    elif host['hostTypeId'] == 7:
                        result = helpercount(host)
                        # VPS 2G size
                        VPS_tcnt_2 += result['VPS_t2']
                        VPS_avcnt_2 += result['VPS_av2']
                        # VPS 4G size
                        VPS_tcnt_4 += result['VPS_t4']
                        VPS_avcnt_4 += result['VPS_av4']
            
    basic_perc_8 = 100 - (basic_avcnt_8 * 100 // basic_tcnt_8)
    basic_perc_16 = 100 - (basic_avcnt_16 * 100 // basic_tcnt_16)
    premium_perc_32 = 100 - (premium_avcnt_32 * 100 // premium_tcnt_32)
    premium_perc_64 = 100 - (premium_avcnt_64 * 100 // premium_tcnt_64)
    premium_perc_128 = 100 - (premium_avcnt_128 * 100 // premium_tcnt_128)
    SSD_perc_8 = 100 - (SSD_avcnt_8 * 100 // SSD_tcnt_8)
    SSD_perc_16 = 100 - (SSD_avcnt_16 * 100 // SSD_tcnt_16)
    SSD_perc_32 = 100 - (SSD_avcnt_32 * 100 // SSD_tcnt_32)
    MSSQL_perc_8 = 100 - (MSSQL_avcnt_8 * 100 // MSSQL_tcnt_8)
    MSSQL_perc_16 = 100 - (MSSQL_avcnt_16 * 100 // MSSQL_tcnt_16)
    WAF_perc_4 = 100 - (WAF_avcnt_4 * 100 // WAF_tcnt_4)
    WAF_perc_8 = 100 - (WAF_avcnt_8 * 100 // WAF_tcnt_8)
    if zone == 'zone_1':
        VPS_perc_2 = 100 - (VPS_avcnt_2 * 100 // VPS_tcnt_2)
        VPS_perc_4 = 100 - (VPS_avcnt_4 * 100 // VPS_tcnt_4)

#    print('')
#    print('#### Zone_1 ####')
#    print('basic 8G - Total : ', str(basic_tcnt_8), 'ea', ' ', 'Available : ', str(basic_avcnt_8), 'ea',
#          '( Used % :', str(basic_perc_8), '% )')
#    print('basic 16G - Total : ', str(basic_tcnt_16), 'ea', ' ', 'Available : ', str(basic_avcnt_16), 'ea',
#          '( Used % :',str(basic_perc_16), '% )')
#    print('')
#    print('premium 32G - Total : ', str(premium_tcnt_32), 'ea', ' ', 'Available : ', str(premium_avcnt_32), 'ea',
#          '( Used % :',str(premium_perc_32), '% )')
#    print('premium 64G - Total : ', str(premium_tcnt_64), 'ea', ' ', 'Available : ', str(premium_avcnt_64), 'ea',
#          '( Used % :',str(premium_perc_64), '% )')
#    print('premium 128G - Total : ', str(premium_tcnt_128), 'ea', ' ', 'Available : ', str(premium_avcnt_128), 'ea',
#          '( Used % :',str(premium_perc_128), '% )')
#    print('')
#    print('SSD 8G - Total : ', str(SSD_tcnt_8), 'ea', ' ', 'Available : ', str(SSD_avcnt_8), 'ea',
#          '( Used % :',str(SSD_perc_8), '% )')
#    print('SSD 16G - Total : ', str(SSD_tcnt_16), 'ea', ' ', 'Available : ', str(SSD_avcnt_16), 'ea',
#          '( Used % :',str(SSD_perc_16), '% )')
#    print('SSD 32G - Total : ', str(SSD_tcnt_32), 'ea', ' ', 'Available : ', str(SSD_avcnt_32), 'ea',
#          '( Used % :',str(SSD_perc_32), '% )')
#    print('')

    context = {'basic_tcnt_8' : basic_tcnt_8, 'basic_avcnt_8' : basic_avcnt_8, 'basic_perc_8' : basic_perc_8,
               'basic_tcnt_16' : basic_tcnt_16, 'basic_avcnt_16' : basic_avcnt_16, 'basic_perc_16' : basic_perc_16,
               'premium_tcnt_32' : premium_tcnt_32, 'premium_avcnt_32' : premium_avcnt_32, 'premium_perc_32' : premium_perc_32,
               'premium_tcnt_64' : premium_tcnt_64, 'premium_avcnt_64' : premium_avcnt_64, 'premium_perc_64' : premium_perc_64,
               'premium_tcnt_128' : premium_tcnt_128, 'premium_avcnt_128' : premium_avcnt_128, 'premium_perc_128' : premium_perc_128,
               'SSD_tcnt_8' : SSD_tcnt_8, 'SSD_avcnt_8' : SSD_avcnt_8, 'SSD_perc_8' : SSD_perc_8,
               'SSD_tcnt_16' : SSD_tcnt_16, 'SSD_avcnt_16' : SSD_avcnt_16, 'SSD_perc_16' : SSD_perc_16,
               'SSD_tcnt_32' : SSD_tcnt_32, 'SSD_avcnt_32' : SSD_avcnt_32, 'SSD_perc_32' : SSD_perc_32,
               'MSSQL_tcnt_8' : MSSQL_tcnt_8, 'MSSQL_avcnt_8' : MSSQL_avcnt_8, 'MSSQL_perc_8' : MSSQL_perc_8,
               'MSSQL_tcnt_16' : MSSQL_tcnt_16, 'MSSQL_avcnt_16' : MSSQL_avcnt_16, 'MSSQL_perc_16' : MSSQL_perc_16,
               'WAF_tcnt_4' : WAF_tcnt_4, 'WAF_avcnt_4' : WAF_avcnt_4, 'WAF_perc_4' : WAF_perc_4,
               'WAF_tcnt_8' : WAF_tcnt_8, 'WAF_avcnt_8' : WAF_avcnt_8, 'WAF_perc_8' : WAF_perc_8,
               }

    if zone == 'zone_1':
        context.update({'VPS_tcnt_2' : VPS_tcnt_2, 'VPS_avcnt_2' : VPS_avcnt_2, 'VPS_perc_2' : VPS_perc_2,
                        'VPS_tcnt_4' : VPS_tcnt_4, 'VPS_avcnt_4' : VPS_avcnt_4, 'VPS_perc_4' : VPS_perc_4})

#    return render(request, 'resourceview/index.html', context)


    # 134217728 (128G) - 134217728 (10G - reserve memory)
    basic_total_mem = 123731968
    # 285212672 (272G) - 8388608 (8G reserve memory)
    premium_total_mem = 285212672
    # 134217728 (128G) - 134217728 (10G - reserve memory)
    WAF_total_mem = 123731968
    # 117440512 (112G) - 16777216 (16G reserve memory)
    # SSD size count : 3081764864 (2939G) / 31457280 (30G) = 97.9
    # 97G memory를 total memory로 계산.
    SSD_total_mem = 101711872
    # 123731968 (176G) - 16777216 (16G reserve memory)
    # MSSQL size count : 4960813056 (4731G) / 251658240 (240G) = 19.7
    # 152G memory를 total memory로 계산.
    MSSQL_total_mem = 159383552
    # 134217728 (128G) - 8388608 (8G reserve memory)
    # VPS size count : VPS 최소사양 - 13107200 (12.5G)
    VPS_total_mem = 125829120 

    if zone == 'zone_1':
        basic_std_perc = int(config['vmused_std_perc']['basic']) + int(config['vmused_std_perc']['zone_1_weight'])
        premium_std_perc = int(config['vmused_std_perc']['premium']) + int(config['vmused_std_perc']['zone_1_weight'])
        WAF_std_perc = int(config['vmused_std_perc']['WAF']) + int(config['vmused_std_perc']['zone_1_weight'])
        SSD_std_perc = int(config['vmused_std_perc']['SSD']) + int(config['vmused_std_perc']['zone_1_weight'])
        MSSQL_std_perc = int(config['vmused_std_perc']['MSSQL']) + int(config['vmused_std_perc']['zone_1_weight'])
        VPS_std_perc = int(config['vmused_std_perc']['VPS'])
    elif zone == 'zone_2':
        basic_std_perc = int(config['vmused_std_perc']['basic']) + int(config['vmused_std_perc']['zone_2_weight'])
        premium_std_perc = int(config['vmused_std_perc']['premium']) + int(config['vmused_std_perc']['zone_2_weight'])
        WAF_std_perc = int(config['vmused_std_perc']['WAF']) + int(config['vmused_std_perc']['zone_2_weight'])
        SSD_std_perc = int(config['vmused_std_perc']['SSD']) + int(config['vmused_std_perc']['zone_2_weight'])
        MSSQL_std_perc = int(config['vmused_std_perc']['MSSQL']) + int(config['vmused_std_perc']['zone_2_weight'])

    if basic_perc_8 > basic_std_perc:
#        print('')
#        print('basic NC 8G 기준 사용률 :', str(basic_std_perc), '%')
#        print('basic NC 8G VM 생성 사용률 :', str(basic_perc_8), '% 입니다.', str(basic_perc_8 - basic_std_perc), '% 초과')
        basic_over_perc_8 = basic_perc_8 - basic_std_perc
        for x in range(1,100):
            result = 100 - (((basic_avcnt_8 + (basic_total_mem // 8388608 * x)) * 100) // (basic_tcnt_8 + (basic_total_mem // 8388608 * x)))
            if result <= basic_std_perc:
                break
#        print((basic_total_mem // 8388608 * x), '개 의 VM 용량을 추가해야 하며 NC Server는', x, "대 가 필요합니다.")
#        print('')
        basic_vm_cnt_8 = (basic_total_mem // 8388608 * x)
        basic_nc_cnt_8 = x
        basic_8_dict = { 'basic_std_perc' : basic_std_perc, 'basic_over_perc_8' : basic_over_perc_8,
                         'basic_vm_cnt_8' : basic_vm_cnt_8, 'basic_nc_cnt_8' : basic_nc_cnt_8 }
        context.update(basic_8_dict)

    if basic_perc_16 > basic_std_perc:
#        print('')
#        print('basic NC 16G 기준 사용률 :', str(basic_std_perc), '%')
#        print('basic NC 16G VM 생성 사용률 :', str(basic_perc_16), '% 입니다.', str(basic_perc_16 - basic_std_perc), '% 초과')
        basic_over_perc_16 = basic_perc_16 - basic_std_perc
        for x in range(1,100):
            result = 100 - (((basic_avcnt_16 + ( basic_total_mem // 16777216 * x)) * 100) // (basic_tcnt_16 + ( basic_total_mem // 16777216 * x)))
            if result <= basic_std_perc:
                break
#        print((basic_total_mem // 16777216 * x), '개 의 VM 용량을 추가해야 하며 NC Server는', x, "대 가 필요합니다.")
#        print('')
        basic_vm_cnt_16 = (basic_total_mem // 16777216 * x)
        basic_nc_cnt_16 = x
        basic_16_dict = { 'basic_std_perc' : basic_std_perc, 'basic_over_perc_16' : basic_over_perc_16,
                          'basic_vm_cnt_16' : basic_vm_cnt_16, 'basic_nc_cnt_16' : basic_nc_cnt_16 }
        context.update(basic_16_dict)

    if premium_perc_32 > premium_std_perc:
#        print('')
#        print('premium NC 32G 기준 사용률 :', str(premium_std_perc), '%')
#        print('premium NC 32G VM 생성 사용률 :', str(premium_perc_32), '% 입니다.', str(premium_perc_32 - premium_std_perc), '% 초과')
        premium_over_perc_32 = premium_perc_32 - premium_std_perc
        for x in range(1,100):
            result = 100 - (((premium_avcnt_32 + (premium_total_mem // 33554432 * x)) * 100) // (premium_tcnt_32 + (premium_total_mem // 33554432 * x)))
            if result <= premium_std_perc:
                break
#        print((premium_total_mem // 33554432 * x), '개 의 VM 용량을 추가해야 하며 NC Server는', x, "대 가 필요합니다.")
#        print('')
        premium_vm_cnt_32 = (premium_total_mem // 33554432 * x)
        premium_nc_cnt_32 = x
        premium_32_dict = { 'premium_std_perc' : premium_std_perc, 'premium_over_perc_32' : premium_over_perc_32,
                          'premium_vm_cnt_32' : premium_vm_cnt_32, 'premium_nc_cnt_32' : premium_nc_cnt_32 }
        context.update(premium_32_dict)

    if premium_perc_64 > premium_std_perc:
#        print('')
#        print('premium NC 64G 기준 사용률 :', str(premium_std_perc), '%')
#        print('premium NC 64G VM 생성 사용률 :', str(premium_perc_64), '% 입니다.', str(premium_perc_64 - premium_std_perc), '% 초과')
        premium_over_perc_64 = premium_perc_64 - premium_std_perc
        for x in range(1,100):
            result = 100 - (((premium_avcnt_64 + (premium_total_mem // 67108864 * x)) * 100) // (premium_tcnt_64 + (premium_total_mem // 67108864 * x)))
            if result <= premium_std_perc:
                break
#        print((premium_total_mem // 67108864 * x), '개 의 VM 용량을 추가해야 하며 NC Server는', x, "대 가 필요합니다.")
#        print('')
        premium_vm_cnt_64 = (premium_total_mem // 67108864 * x)
        premium_nc_cnt_64 = x
        premium_64_dict = { 'premium_std_perc' : premium_std_perc, 'premium_over_perc_64' : premium_over_perc_64,
                          'premium_vm_cnt_64' : premium_vm_cnt_64, 'premium_nc_cnt_64' : premium_nc_cnt_64 }
        context.update(premium_64_dict)

    if premium_perc_128 > premium_std_perc:
#        print('')
#        print('premium NC 128G 기준 사용률 :', str(premium_std_perc), '%')
#        print('premium NC 128G VM 생성 사용률 :', str(premium_perc_128), '% 입니다.', str(premium_perc_128 - premium_std_perc), '% 초과')
        premium_over_perc_128 = premium_perc_128 - premium_std_perc
        for x in range(1,100):
            result = 100 - (((premium_avcnt_128 + (premium_total_mem // 134217728 * x)) * 100) // (premium_tcnt_128 + (premium_total_mem // 134217728 * x)))
            if result <= premium_std_perc:
                break
#        print((premium_total_mem // 134217728 * x), '개 의 VM 용량을 추가해야 하며 NC Server는', x, "대 가 필요합니다.")
#        print('')
        premium_vm_cnt_128 = (premium_total_mem // 134217728 * x)
        premium_nc_cnt_128 = x
        premium_128_dict = { 'premium_std_perc' : premium_std_perc, 'premium_over_perc_128' : premium_over_perc_128,
                          'premium_vm_cnt_128' : premium_vm_cnt_128, 'premium_nc_cnt_128' : premium_nc_cnt_128 }
        context.update(premium_128_dict)

    if WAF_perc_4 > WAF_std_perc:
#        print('')
#        print('WAF NC 4G 기준 사용률 :', str(WAF_std_perc), '%')
#        print('WAF NC 4G VM 생성 사용률 :', str(WAF_perc_4), '% 입니다.', str(WAF_perc_4 - WAF_std_perc), '% 초과')
        WAF_over_perc_4 = WAF_perc_4 - WAF_std_perc
        for x in range(1,100):
            result = 100 - (((WAF_avcnt_4 + (WAF_total_mem // 4194304 * x)) * 100) // ( WAF_tcnt_4 + (WAF_total_mem // 4194304 * x)))
            if result <= WAF_std_perc:
                break
#        print((WAF_total_mem // 4194304 * x), '개 의 VM 용량을 추가해야 하며 NC Server는', x, "대 가 필요합니다.")
#        print('')
        WAF_vm_cnt_4 = (WAF_total_mem // 4194304 * x)
        WAF_nc_cnt_4 = x
        WAF_4_dict = { 'WAF_std_perc' : WAF_std_perc, 'WAF_over_perc_4' : WAF_over_perc_4,
                       'WAF_vm_cnt_4' : WAF_vm_cnt_4, 'WAF_nc_cnt_4' : WAF_nc_cnt_4 }
        context.update(WAF_4_dict)

    if WAF_perc_8 > WAF_std_perc:
#        print('')
#        print('WAF NC 8G 기준 사용률 :', str(WAF_std_perc), '%')
#        print('WAF NC 8G VM 생성 사용률 :', str(WAF_perc_8), '% 입니다.', str(WAF_perc_8 - WAF_std_perc), '% 초과')
        WAF_over_perc_8 = WAF_perc_8 - WAF_std_perc
        for x in range(1,100):
            result = 100 - (((WAF_avcnt_8 + (WAF_total_mem // 8388608 * x)) * 100) // ( WAF_tcnt_8 + (WAF_total_mem // 8388608 * x)))
            if result <= WAF_std_perc:
                break
#        print((WAF_total_mem // 8388608 * x), '개 의 VM 용량을 추가해야 하며 NC Server는', x, "대 가 필요합니다.")
#        print('')
        WAF_vm_cnt_8 = (WAF_total_mem // 8388608 * x)
        WAF_nc_cnt_8 = x
        WAF_8_dict = { 'WAF_std_perc' : WAF_std_perc, 'WAF_over_perc_8' : WAF_over_perc_8,
                       'WAF_vm_cnt_8' : WAF_vm_cnt_8, 'WAF_nc_cnt_8' : WAF_nc_cnt_8 }
        context.update(WAF_8_dict)

    if SSD_perc_8 > SSD_std_perc:
#        print('')
#        print('SSD NC 8G 기준 사용률 :', str(SSD_std_perc), '%')
#        print('SSD NC 8G VM 생성 사용률 :', str(SSD_perc_8), '% 입니다.', str(SSD_perc_8 - SSD_std_perc), '% 초과')
        SSD_over_perc_8 = SSD_perc_8 - SSD_std_perc
        for x in range(1,100):
            result = 100 - (((SSD_avcnt_8 + (SSD_total_mem // 8388608 * x)) * 100) // ( SSD_tcnt_8 + (SSD_total_mem // 8388608 * x)))
            if result <= SSD_std_perc:
                break
#        print((SSD_total_mem // 8388608 * x), '개 의 VM 용량을 추가해야 하며 NC Server는', x, "대 가 필요합니다.")
#        print('')
        SSD_vm_cnt_8 = (SSD_total_mem // 8388608 * x)
        SSD_nc_cnt_8 = x
        SSD_8_dict = { 'SSD_std_perc' : SSD_std_perc, 'SSD_over_perc_8' : SSD_over_perc_8,
                       'SSD_vm_cnt_8' : SSD_vm_cnt_8, 'SSD_nc_cnt_8' : SSD_nc_cnt_8 }
        context.update(SSD_8_dict)

    if SSD_perc_16 > SSD_std_perc:
#        print('')
#        print('SSD NC 16G 기준 사용률 :', str(SSD_std_perc), '%')
#        print('SSD NC 16G VM 생성 사용률 :', str(SSD_perc_16), '% 입니다.', str(SSD_perc_16 - SSD_std_perc), '% 초과')
        SSD_over_perc_16 = SSD_perc_16 - SSD_std_perc
        for x in range(1,100):
            result = 100 - (((SSD_avcnt_16 + ( SSD_total_mem // 16777216 * x)) * 100) // ( SSD_tcnt_16 + ( SSD_total_mem // 16777216 * x)))
            if result <= SSD_std_perc:
                break
#        print((SSD_total_mem // 16777216 * x), '개 의 VM 용량을 추가해야 하며 NC Server는', x, "대 가 필요합니다.")
#        print('')
        SSD_vm_cnt_16 = (SSD_total_mem // 16777216 * x)
        SSD_nc_cnt_16 = x
        SSD_16_dict = { 'SSD_std_perc' : SSD_std_perc, 'SSD_over_perc_16' : SSD_over_perc_16,
                        'SSD_vm_cnt_16' : SSD_vm_cnt_16, 'SSD_nc_cnt_16' : SSD_nc_cnt_16 }
        context.update(SSD_16_dict)

    if SSD_perc_32 > SSD_std_perc:
#        print('')
#        print('SSD NC 32G 기준 사용률 :', str(SSD_std_perc), '%')
#        print('SSD NC 32G VM 생성 사용률 :', str(SSD_perc_32), '% 입니다.', str(SSD_perc_32 - SSD_std_perc), '% 초과')
        SSD_over_perc_32 = SSD_perc_32 - SSD_std_perc
        for x in range(1,100):
            result = 100 - (((SSD_avcnt_32 + (SSD_total_mem // 33554432 * x)) * 100) // (SSD_tcnt_32 + (SSD_total_mem // 33554432 * x)))
            if result <= SSD_std_perc:
                break
#        print((SSD_total_mem // 33554432 * x), '개 의 VM 용량을 추가해야 하며 NC Server는', x, "대 가 필요합니다.")
#        print('')
        SSD_vm_cnt_32 = (SSD_total_mem // 33554432 * x)
        SSD_nc_cnt_32 = x
        SSD_32_dict = { 'SSD_std_perc' : SSD_std_perc, 'SSD_over_perc_32' : SSD_over_perc_32,
                        'SSD_vm_cnt_32' : SSD_vm_cnt_32, 'SSD_nc_cnt_32' : SSD_nc_cnt_32 }
        context.update(SSD_32_dict)

    if MSSQL_perc_8 > MSSQL_std_perc:
#        print('')
#        print('MSSQL NC 8G 기준 사용률 :', str(MSSQL_std_perc), '%')
#        print('MSSQL NC 8G VM 생성 사용률 :', str(MSSQL_perc_8), '% 입니다.', str(MSSQL_perc_8 - MSSQL_std_perc), '% 초과')
        MSSQL_over_perc_8 = MSSQL_perc_8 - MSSQL_std_perc
        for x in range(1,100):
            result = 100 - (((MSSQL_avcnt_8 + (MSSQL_total_mem // 8388608 * x)) * 100) // ( MSSQL_tcnt_8 + (MSSQL_total_mem // 8388608 * x)))
            if result <= MSSQL_std_perc:
                break
#        print((MSSQL_total_mem // 8388608 * x), '개 의 VM 용량을 추가해야 하며 NC Server는', x, "대 가 필요합니다.")
#        print('')
        MSSQL_vm_cnt_8 = (MSSQL_total_mem // 8388608 * x)
        MSSQL_nc_cnt_8 = x
        MSSQL_8_dict = { 'MSSQL_std_perc' : MSSQL_std_perc, 'MSSQL_over_perc_8' : MSSQL_over_perc_8,
                       'MSSQL_vm_cnt_8' : MSSQL_vm_cnt_8, 'MSSQL_nc_cnt_8' : MSSQL_nc_cnt_8 }
        context.update(MSSQL_8_dict)

    if MSSQL_perc_16 > MSSQL_std_perc:
#        print('')
#        print('MSSQL NC 16G 기준 사용률 :', str(MSSQL_std_perc), '%')
#        print('MSSQL NC 16G VM 생성 사용률 :', str(MSSQL_perc_16), '% 입니다.', str(MSSQL_perc_16 - MSSQL_std_perc), '% 초과')
        MSSQL_over_perc_16 = MSSQL_perc_16 - MSSQL_std_perc
        for x in range(1,100):
            result = 100 - (((MSSQL_avcnt_16 + ( MSSQL_total_mem // 16777216 * x)) * 100) // ( MSSQL_tcnt_16 + ( MSSQL_total_mem // 16777216 * x)))
            if result <= MSSQL_std_perc:
                break
#        print((MSSQL_total_mem // 16777216 * x), '개 의 VM 용량을 추가해야 하며 NC Server는', x, "대 가 필요합니다.")
#        print('')
        MSSQL_vm_cnt_16 = (MSSQL_total_mem // 16777216 * x)
        MSSQL_nc_cnt_16 = x
        MSSQL_16_dict = { 'MSSQL_std_perc' : MSSQL_std_perc, 'MSSQL_over_perc_16' : MSSQL_over_perc_16,
                        'MSSQL_vm_cnt_16' : MSSQL_vm_cnt_16, 'MSSQL_nc_cnt_16' : MSSQL_nc_cnt_16 }
        context.update(MSSQL_16_dict)

    if zone == 'zone_1':
        if VPS_perc_2 > VPS_std_perc:
    #        print('')
    #        print('VPS NC 8G 기준 사용률 :', str(VPS_std_perc), '%')
    #        print('VPS NC 8G VM 생성 사용률 :', str(VPS_perc_2), '% 입니다.', str(VPS_perc_2 - VPS_std_perc), '% 초과')
            VPS_over_perc_2 = VPS_perc_2 - VPS_std_perc
            for x in range(1,100):
                result = 100 - (((VPS_avcnt_2 + (VPS_total_mem // 2097152 * x)) * 100) // ( VPS_tcnt_2 + (VPS_total_mem // 2097152 * x)))
                if result <= VPS_std_perc:
                    break
    #        print((VPS_total_mem // 2097152 * x), '개 의 VM 용량을 추가해야 하며 NC Server는', x, "대 가 필요합니다.")
    #        print('')
            VPS_vm_cnt_2 = (VPS_total_mem // 2097152 * x)
            VPS_nc_cnt_2 = x 
            VPS_2_dict = { 'VPS_std_perc' : VPS_std_perc, 'VPS_over_perc_2' : VPS_over_perc_2,
                           'VPS_vm_cnt_2' : VPS_vm_cnt_2, 'VPS_nc_cnt_2' : VPS_nc_cnt_2 }
            context.update(VPS_2_dict)
    
        if VPS_perc_4 > VPS_std_perc:
    #        print('')
    #        print('VPS NC 4G 기준 사용률 :', str(VPS_std_perc), '%')
    #        print('VPS NC 4G VM 생성 사용률 :', str(VPS_perc_4), '% 입니다.', str(VPS_perc_4 - VPS_std_perc), '% 초과')
            VPS_over_perc_4 = VPS_perc_4 - VPS_std_perc
            for x in range(1,100):
                result = 100 - (((VPS_avcnt_4 + (VPS_total_mem // 4194304 * x)) * 100) // ( VPS_tcnt_4 + (VPS_total_mem // 4194304 * x)))
                if result <= VPS_std_perc:
                    break
    #        print((VPS_total_mem // 4194304 * x), '개 의 VM 용량을 추가해야 하며 NC Server는', x, "대 가 필요합니다.")
    #        print('')
            VPS_vm_cnt_4 = (VPS_total_mem // 4194304 * x)
            VPS_nc_cnt_4 = x
            VPS_4_dict = { 'VPS_std_perc' : VPS_std_perc, 'VPS_over_perc_4' : VPS_over_perc_4,
                           'VPS_vm_cnt_4' : VPS_vm_cnt_4, 'VPS_nc_cnt_4' : VPS_nc_cnt_4 }
            context.update(VPS_4_dict)

    return context


# NC 에서 가져온 Total Memory, Avail Memory 를 VM의 Memory Size (8G, 16G etc) 로 나눠 개수를 계산한다.
# SSD는 Disk Size 도 계산식에 포함된다. ( MEM, SSD 나눈값 중 가장 작은 수치를 생성 가능 수치로 계산.
def helpercount(host):
    basic_t8 = 0
    basic_av8 = 0
    basic_t16 = 0
    basic_av16 = 0
    premium_t32 = 0
    premium_av32 = 0
    premium_t64 = 0
    premium_av64 = 0
    premium_t128 = 0
    premium_av128 = 0
    WAF_t4 = 0 
    WAF_av4 = 0 
    WAF_t8 = 0 
    WAF_av8 = 0 
    SSD_t8 = 0
    SSD_av8 = 0
    SSD_t16 = 0
    SSD_av16 = 0
    SSD_t32 = 0
    SSD_av32 = 0
    MSSQL_t8 = 0 
    MSSQL_av8 = 0 
    MSSQL_t16 = 0 
    MSSQL_av16 = 0 
    VPS_t2 = 0 
    VPS_av2 = 0 
    VPS_t4 = 0 
    VPS_av4 = 0 

    # HostType 1, 'basic'
    if host['hostTypeId'] == 1:
        basic_t8 = host['totalMemory'] // 8388608
        basic_av8 = host['avMem'] // 8388608
        basic_t16 = host['totalMemory'] // 16777216
        basic_av16 = host['avMem'] // 16777216
#        print(json.dumps(hostList['zone_1'], indent=4))
        return {'basic_t8' : basic_t8, 'basic_av8' : basic_av8, 'basic_t16' : basic_t16, 'basic_av16' : basic_av16}
    # HostType 2, 'premium'
    elif host['hostTypeId'] == 2:
        premium_t32 = host['totalMemory'] // 33554432
        premium_av32 = host['avMem'] // 33554432
        premium_t64 = host['totalMemory'] // 67108864
        premium_av64 = host['avMem'] // 67108864
        premium_t128 = host['totalMemory'] // 134217728
        premium_av128 = host['avMem'] // 134217728
        return {'premium_t32' : premium_t32, 'premium_av32' : premium_av32, 'premium_t64' : premium_t64, 'premium_av64' : premium_av64,
                'premium_t128' : premium_t128, 'premium_av128' : premium_av128}
    # HostType 3, 'WAF'
    elif host['hostTypeId'] == 3:
        WAF_t4 = host['totalMemory'] // 4194304
        WAF_av4 = host['avMem'] // 4194304
        WAF_t8 = host['totalMemory'] // 8388608
        WAF_av8 = host['avMem'] // 8388608
        return {'WAF_t4' : WAF_t4, 'WAF_av4' : WAF_av4, 'WAF_t8' : WAF_t8, 'WAF_av8' : WAF_av8}
    # HostType 5, 'SSD'
    elif host['hostTypeId'] == 5:
        # SSD 8G size
        t8_1 = host['totalMemory'] // 8388608
        t8_2 = host['totalSize'] // 251658240
        av8_1 = host['avMem'] // 8388608
        av8_2 = host['availableSize'] // 251658240
        # SSD 16G size
        t16_1 = host['totalMemory'] // 16777216
        t16_2 = host['totalSize'] // 503316480
        av16_1 = host['avMem'] // 16777216
        av16_2 = host['availableSize'] // 503316480
        # SSD 32G size
        t32_1 = host['totalMemory'] // 33554432
        t32_2 = host['totalSize'] // 1006632960
        av32_1 = host['avMem'] // 33554432
        av32_2 = host['availableSize'] // 1006632960
        # SSD 8G size
        if t8_1 >= t8_2:
            SSD_t8 = t8_2
        else:
            SSD_t8 = t8_1
        if av8_1 >= av8_2:
            SSD_av8 = av8_2
        else:
            SSD_av8 = av8_1
        # SSD 16G size
        if t16_1 >= t16_2:
            SSD_t16 = t16_2
        else:
            SSD_t16 = t16_1
        if av16_1 >= av16_2:
            SSD_av16 = av16_2
        else:
            SSD_av16 = av16_1
        # SSD 32G size
        if t32_1 >= t32_2:
            SSD_t32 = t32_2
        else:
            SSD_t32 = t32_1
        if av32_1 >= av32_2:
            SSD_av32 = av32_2
        else:
            SSD_av32 = av32_1
        return {'SSD_t8' : SSD_t8, 'SSD_av8' : SSD_av8, 'SSD_t16' : SSD_t16, 'SSD_av16' : SSD_av16, 'SSD_t32' : SSD_t32, 'SSD_av32' : SSD_av32}
    # HostType 9, 'MSSQL'
    elif host['hostTypeId'] == 9:
        # MSSQL 8G size
        t8_1 = host['totalMemory'] // 8388608
        t8_2 = host['totalSize'] // 251658240
        av8_1 = host['avMem'] // 8388608
        av8_2 = host['availableSize'] // 251658240
        # MSSQL 16G size
        t16_1 = host['totalMemory'] // 16777216
        t16_2 = host['totalSize'] // 503316480
        av16_1 = host['avMem'] // 16777216
        av16_2 = host['availableSize'] // 503316480
        # MSSQL 8G size
        if t8_1 >= t8_2:
            MSSQL_t8 = t8_2
        else:
            MSSQL_t8 = t8_1
        if av8_1 >= av8_2:
            MSSQL_av8 = av8_2
        else:
            MSSQL_av8 = av8_1
        # MSSQL 16G size
        if t16_1 >= t16_2:
            MSSQL_t16 = t16_2
        else:
            MSSQL_t16 = t16_1
        if av16_1 >= av16_2:
            MSSQL_av16 = av16_2
        else:
            MSSQL_av16 = av16_1
        return {'MSSQL_t8' : MSSQL_t8, 'MSSQL_av8' : MSSQL_av8, 'MSSQL_t16' : MSSQL_t16, 'MSSQL_av16' : MSSQL_av16}
    # HostType 7, 'VPS'
    elif host['hostTypeId'] == 7:
        # VPS 2G size
        t2_1 = host['totalMemory'] // 2097152
        t2_2 = host['totalSize'] // 52428800
        av2_1 = host['avMem'] // 2097152
        av2_2 = host['availableSize'] // 52428800
        # VPS 4G size
        t4_1 = host['totalMemory'] // 4194304
        t4_2 = host['totalSize'] // 104857600
        av4_1 = host['avMem'] // 4194304
        av4_2 = host['availableSize'] // 104857600
        # VPS 2G size
        if t2_1 >= t2_2:
            VPS_t2 = t2_2
        else:
            VPS_t2 = t2_1
        if av2_1 >= av2_2:
            VPS_av2 = av2_2
        else:
            VPS_av2 = av2_1
        # VPS 4G size
        if t4_1 >= t4_2:
            VPS_t4 = t4_2
        else:
            VPS_t4 = t4_1
        if av4_1 >= av4_2:
            VPS_av4 = av4_2
        else:
            VPS_av4 = av4_1
        return {'VPS_t2' : VPS_t2, 'VPS_av2' : VPS_av2, 'VPS_t4' : VPS_t4, 'VPS_av4' : VPS_av4}
