import os
import re

"""Fan control on Gigabyte systems (R282-Z93 or G292-Z43)

    - this help:
            axs byname gigabyte_fan_control , help

    - reading fan speed (in RPM) on default GIGABYTE_R282-Z93 or GIGABYTE_G292-Z43:
            axs byname gigabyte_fan_control , get get_fan

    - setting fan speed (in own units, 1..250) :
            axs byname gigabyte_fan_control , get set_fan --fan_value=15

    - mapping between --fan_value and speed_RPM :

            ---------------------------
            fan_value   |   speed_RPM
            ---------------------------
               0        |    3000
              15        |    3600
              20        |    3900
              25        |    4200
              30        |    4500
              40        |    4950
              50        |    5550
              75        |    6750
             100        |    8100
             125        |    9450
             150        |   10800
             200        |   13350
             250        |   15900
            ---------------------------
"""

def set_fan(fan_value, system_name, supported_systems=[]):
    if not fan_value:
        return
    cmd  = "sudo ipmitool raw 0x2e 0x10 0x0a 0x3c 0 64 1 " + str(fan_value) + " 0xFF"
    if system_name in supported_systems:
        print(cmd)
        return os.system(cmd)
    else:
        print(f'The {system_name} does not support fan setting. system_name has to be in {system_name_list}.')
        return 0

def get_fan(system_name, fan_sensor, supported_systems=[]):
    if system_name in supported_systems:
        cmd  = "sudo ipmitool sensor get " + fan_sensor
        print(cmd)
        cmd += " | grep 'Sensor Reading'"
        res = os.popen(cmd).read()
        r = re.match("(\s+)Sensor Reading(\s+):(\s+)(\d+)", res).group(4)
        return r
    else:
        print(f'The {system_name} does not support fan getting. system_name has to be in {system_name_list}.')
        return 0