#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
library for WittyPi 3 mini
Version 3.11
"""

name = "wittypi"
__version__ = '0.0.5'
# pip3 install smbus2



import datetime as dt
import calendar
import time
import pytz
local_tz = pytz.timezone('Europe/Stockholm')
utc_tz = pytz.timezone('UTC')

from smbus2 import SMBus

def dec2hex(datalist):
    res = []
    for v in datalist:
        hexInt = 10*(v//16) + (v%16)
        res.append(hexInt)
    return res



RTC_ADDRESS = 0x68
I2C_MC_ADDRESS = 0x69
I2C_VOLTAGE_IN_I=1
I2C_VOLTAGE_IN_D=2

I2C_VOLTAGE_OUT_I=3
I2C_VOLTAGE_OUT_D=4
I2C_CURRENT_OUT_I=5
I2C_CURRENT_OUT_D=6
I2C_POWER_MODE=7
I2C_LV_SHUTDOWN=8
I2C_CONF_ADDRESS=9
I2C_CONF_DEFAULT_ON=10
I2C_CONF_PULSE_INTERVAL=11
I2C_CONF_LOW_VOLTAGE=12
I2C_CONF_BLINK_LED=13
I2C_CONF_POWER_CUT_DELAY=14
I2C_CONF_RECOVERY_VOLTAGE=15
I2C_CONF_DUMMY_LOAD=16
I2C_CONF_ADJ_VIN=17
I2C_CONF_ADJ_VOUT=18
I2C_CONF_ADJ_IOUT=19
HALT_PIN=4    # halt by GPIO-4 (BCM naming)
SYSUP_PIN=17




def get_rtc_timestamp(): 
    out=[]
    with SMBus(1) as bus:
        data = [0,1, 2, 3, 4, 5, 6]
        for ele in data:
            b = bus.read_byte_data(RTC_ADDRESS, ele)
            out.append(b)
    res = dec2hex(out)
    UTCtime = dt.datetime(res[6]+2000,res[5],res[4],res[2],res[1],res[0])
    UTCtime = pytz.utc.localize(UTCtime).astimezone(utc_tz)
    localtime = UTCtime.astimezone(local_tz)
    timestamp = int(time.mktime(UTCtime.timetuple()))
    return UTCtime,localtime,timestamp



def get_input_voltage():
    with SMBus(1) as bus:
        i = bus.read_byte_data(I2C_MC_ADDRESS, I2C_VOLTAGE_IN_I)
        d = bus.read_byte_data(I2C_MC_ADDRESS, I2C_VOLTAGE_IN_D)
    res = i + float(d)/100.
    return res


def get_startup_time(): # [?? 07:00:00], ignore: [?? ??:??:00] and [?? ??:??:??]
    out=[]
    with SMBus(1) as bus:
        for ele in [7,8,9,10]:
            b = bus.read_byte_data(RTC_ADDRESS, ele)
            out.append(b)
    res = dec2hex(out) # sec, min, hour, day
    return calcTime(res)

def add_one_month(orig_date):
    # advance year and month by one month
    new_year = orig_date.year
    new_month = orig_date.month + 1
    # note: in datetime.date, months go from 1 to 12
    if new_month > 12:
        new_year += 1
        new_month -= 12
    last_day_of_month = calendar.monthrange(new_year, new_month)[1]
    new_day = min(orig_date.day, last_day_of_month)
    return orig_date.replace(year=new_year, month=new_month, day=new_day)


def calcTime(res):
    """calculate startup/shutdown time from wittypi output"""
    nowUTC = dt.datetime.now(utc_tz)
    nowLOCAL = dt.datetime.now(local_tz)
    #  sec, min, hour, day
    if (res[-1] == 0): # [0, 0, 0] if day = 0 -> no time or date defined
        startup_time_utc = dt.datetime(nowUTC.year+1,nowUTC.month,nowUTC.day,nowUTC.hour,nowUTC.minute,0) #.astimezone(utc_tz) # add 1 year
        startup_time_utc = utc_tz.localize(startup_time_utc)
    else:
        if (res[-1] == 80) and (res[-2] != 80): # day not defined, start every day
            startup_time_utc = dt.datetime(nowUTC.year,nowUTC.month,nowUTC.day,res[-2],res[-3],0) #.astimezone(utc_tz)
            startup_time_utc = utc_tz.localize(startup_time_utc)
            if startup_time_utc < nowUTC: startup_time_utc += dt.timedelta(days=1)
        if (res[-1] != 80) and (res[-2] != 80): # day defined, start every month
            startup_time_utc = dt.datetime(nowUTC.year,nowUTC.month,res[-1],res[-2],res[-3],0) #.astimezone(utc_tz)
            startup_time_utc = utc_tz.localize(startup_time_utc)
            if startup_time_utc < nowUTC: startup_time_utc = add_one_month(startup_time_utc)
        if (res[-1] == 80) and (res[-2] == 80): # day and hour not defined, start every hour
            startup_time_utc = dt.datetime(nowUTC.year,nowUTC.month,nowUTC.day,nowUTC.hour,res[-3],0) #.astimezone(utc_tz)
            startup_time_utc = utc_tz.localize(startup_time_utc)
            if startup_time_utc < nowUTC: startup_time_utc += dt.timedelta(hours=1)
    startup_time_local =  startup_time_utc.astimezone(local_tz)
    strtime = [] # [0, 20, 80]
    for ele in res:
        if ele == 80: strtime.append('??')
        else: strtime.append(str(ele))
    if len(strtime) == 4: str_time = strtime[-1] + ' ' + strtime[-2] + ':' + strtime[-3] + ':' + strtime[-4]
    else: str_time = strtime[-1] + ' ' + strtime[-2] + ':' + strtime[-3] + ':00' 
    timedelta = startup_time_local - nowLOCAL
    return startup_time_utc,startup_time_local,str_time,timedelta


def calcTimeOld(res):
    """calculate startup/shutdown time from wittypi output"""
    nowUTC = dt.datetime.now(utc_tz)
    nowLOCAL = dt.datetime.now(local_tz)
    #  sec, min, hour, day
    if (res[-1] == 0): # [0, 0, 0] if day = 0 -> no time or date defined
        startup_time_local = dt.datetime(nowLOCAL.year+1,nowLOCAL.month,nowLOCAL.day,nowLOCAL.hour,nowLOCAL.minute,0).astimezone(local_tz) # add 1 year
    else:
        if (res[-1] == 80) and (res[-2] != 80): # day not defined, start every day
            startup_time_local = dt.datetime(nowLOCAL.year,nowLOCAL.month,nowLOCAL.day,res[-2],res[-3],0).astimezone(local_tz)
            if startup_time_local < nowLOCAL: startup_time_local += dt.timedelta(days=1)
        if (res[-1] != 80) and (res[-2] != 80): # day defined, start every month
            startup_time_local = dt.datetime(nowLOCAL.year,nowLOCAL.month,res[-1],res[-2],res[-3],0).astimezone(local_tz)
            if startup_time_local < nowLOCAL: startup_time_local = add_one_month(startup_time_local)
        if (res[-1] == 80) and (res[-2] == 80): # day and hour not defined, start every hour
            startup_time_local = dt.datetime(nowLOCAL.year,nowLOCAL.month,nowLOCAL.day,nowLOCAL.hour,res[-3],0).astimezone(local_tz)
            if startup_time_local < nowLOCAL: startup_time_local += dt.timedelta(hours=1)
    #startup_time_local =  startup_time_utc.astimezone(local_tz)
    startup_time_utc =  startup_time_local.astimezone(utc_tz)
    strtime = [] # [0, 20, 80]
    for ele in res:
        if ele == 80: strtime.append('??')
        else: strtime.append(str(ele))
    if len(strtime) == 4: str_time = strtime[-1] + ' ' + strtime[-2] + ':' + strtime[-3] + ':' + strtime[-4]
    else: str_time = strtime[-1] + ' ' + strtime[-2] + ':' + strtime[-3] + ':00' 
    timedelta = startup_time_local - nowLOCAL
    return startup_time_utc,startup_time_local,str_time,timedelta




def get_shutdown_time(): # [?? 07:00:00], ignore: [?? ??:??:00] and [?? ??:??:??]
    out=[]
    with SMBus(1) as bus:
        for ele in [11,12,13]:
            b = bus.read_byte_data(RTC_ADDRESS, ele)
            out.append(b)
    res = dec2hex(out) # sec, min, hour, day
    return calcTime(res)

def stringtime2timetuple(stringtime='?? 20:00'):
    day = stringtime.split(' ')[0]
    if day == '??': day = 80 #128
    else: day = int(day)
    hour = stringtime.split(' ')[1].split(':')[0]
    if hour == '??': hour = 80 #128
    else: hour = int(hour)
    minute = int(stringtime.split(' ')[1].split(':')[1])
    #second = int(stringtime.split(' ')[1].split(':')[2])
    #print(day,hour,minute,second)
    return (day,hour,minute)

def set_shutdown_time(stringtime='?? 20:00'):
    try:
        day,hour,minute = stringtime2timetuple(stringtime=stringtime)
        with SMBus(1) as bus:
            bus.write_byte_data(RTC_ADDRESS, 14,7) # write_byte_data(i2c_addr, register, value, force=None)
            bus.write_byte_data(RTC_ADDRESS, 11,int(float(minute)*1.6)) 
            bus.write_byte_data(RTC_ADDRESS, 12,int(float(hour)*1.6)) 
            bus.write_byte_data(RTC_ADDRESS, 13,int(float(day)*1.6)) 
        return True
    except Exception as e:
        print(e)
        return False


def set_startup_time(stringtime='?? 20:00'):
    try:
        day,hour,minute = stringtime2timetuple(stringtime=stringtime)
        with SMBus(1) as bus:
            bus.write_byte_data(RTC_ADDRESS, 14,7) # write_byte_data(i2c_addr, register, value, force=None)
            #bus.write_byte_data(RTC_ADDRESS, 7,int(float(seconds)*1.6)) 
            bus.write_byte_data(RTC_ADDRESS, 8,int(float(minute)*1.6)) 
            bus.write_byte_data(RTC_ADDRESS, 9,int(float(hour)*1.6)) 
            bus.write_byte_data(RTC_ADDRESS, 10,int(float(day)*1.6)) 
        return True
    except Exception as e:
        print(e)
        return False


def clear_shutdown_time():
    with SMBus(1) as bus:
        bus.write_byte_data(RTC_ADDRESS, 11,0) # write_byte_data(i2c_addr, register, value, force=None)
        bus.write_byte_data(RTC_ADDRESS, 12,0) # write_byte_data(i2c_addr, register, value, force=None)
        bus.write_byte_data(RTC_ADDRESS, 13,0) # write_byte_data(i2c_addr, register, value, force=None)


def get_power_mode():
    with SMBus(1) as bus:
        b = bus.read_byte_data(I2C_MC_ADDRESS, I2C_POWER_MODE)
    return b # int 0 or 1

def get_output_voltage():
    with SMBus(1) as bus:
        i = bus.read_byte_data(I2C_MC_ADDRESS, I2C_VOLTAGE_OUT_I)
        d = bus.read_byte_data(I2C_MC_ADDRESS, I2C_VOLTAGE_OUT_D)
    return float(i) + float(d)/100.


def get_output_current():
    with SMBus(1) as bus:
        i = bus.read_byte_data(I2C_MC_ADDRESS, I2C_CURRENT_OUT_I)
        d = bus.read_byte_data(I2C_MC_ADDRESS, I2C_CURRENT_OUT_D)
    return float(i) + float(d)/100.



def get_low_voltage_threshold():
    with SMBus(1) as bus:
        i = bus.read_byte_data(I2C_MC_ADDRESS, I2C_CONF_LOW_VOLTAGE)
    if i == 255: thresh = 'disabled'
    else: thresh = float(i)/10.
    return thresh


def get_recovery_voltage_threshold():
    with SMBus(1) as bus:
        i = bus.read_byte_data(I2C_MC_ADDRESS, I2C_CONF_RECOVERY_VOLTAGE)
    if i == 255: thresh = 'disabled'
    else: thresh = float(i)/10.
    return thresh

def set_low_voltage_threshold(volt='11.5'): 
    if len(volt) == 4:
        volt = int(float(volt) * 10.)
        if not (50 < volt < 254): volt = 255 # clear threshold if threshold is not between 5V and 25.4V
        else: print(' setting threshold to ',volt)
        try:
            with SMBus(1) as bus:
                bus.write_byte_data(I2C_MC_ADDRESS, I2C_CONF_LOW_VOLTAGE,volt) 
            return True
        except Exception as e:
            print(e)
            return False
    else:
        print('wrong input for voltage threshold',volt)
        return False


def set_recovery_voltage_threshold(volt='12.8'): 
    if len(volt) == 4:
        volt = int(float(volt) * 10.)
        if not (50 < volt < 254): volt = 255 # clear threshold if threshold is not between 5V and 25.4V
        else: print(' setting threshold to ',volt)
        try:
            with SMBus(1) as bus:
                bus.write_byte_data(I2C_MC_ADDRESS, I2C_CONF_RECOVERY_VOLTAGE,volt) 
            return True
        except Exception as e:
            print(e)
            return False
    else:
        print('wrong input for voltage threshold',volt)
        return False

def get_temperature():
    with SMBus(1) as bus:
        ctrl = bus.read_byte_data(RTC_ADDRESS, 14)
        ctrl2 = 7|0x20 #39 bitwise or
        bus.write_byte_data(RTC_ADDRESS, 14,ctrl2) 
        time.sleep(0.2)
        t1 = bus.read_byte_data(RTC_ADDRESS, 0x11)
        t2 = bus.read_byte_data(RTC_ADDRESS, 0x12)
        c = ''
        sign = t1&0x80
        if sign < 0: c+='-'
        else: c += str(t1&0x7F)
        c+='.'
        c += str(((t2&0xC0)>>6)*25 )
    return float(c)


def getAll():
    wittypi = {}
    UTCtime,localtime,timestamp = get_rtc_timestamp()
    wittypi['DateTime'] = localtime.strftime("%Y-%m-%d_%H-%M-%S")
    wittypi['timestamp'] = timestamp
    wittypi['input_voltage'] = get_input_voltage()
    wittypi['output_voltage'] = get_output_voltage()
    wittypi['temperature'] = get_temperature()
    wittypi['outputcurrent'] = get_output_current()
    return wittypi
    


