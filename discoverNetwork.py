import os
import re
import queue
import socket
import jinja2
import pymssql
import pymysql
import netmiko
import paramiko
import traceback
from threading import Thread
from sqlFunctions import *
from time import sleep
from datetime import datetime

def getFQDNAndIPAddress(hostname, domainsList=None):
    if not domainsList:
        domainsList = ['sub1.domain.com.', 'sub2.domain.com.']
        try:
            ipv4Address = socket.getaddrinfo(hostname,0,0,0,0)[0][4][0]
            return hostname
        except:
            pass
    hostname = hostname.split('.')[0]
    region = domainsList.pop(0)
    fqdn = hostname + region
    try:
        ipv4Address = socket.getaddrinfo(fqdn,0,0,0,0)[0][4][0]
        return fqdn.upper()
    except:
        if len(domainsList):
            return getFQDNAndIPAddress(hostname, domainsList)
        return False


def getDevicesSQL(queue,site_code):
    queryStr = '''  SELECT DISTINCT hostname FROM [Central].[central].[network_device_inventory]
                    WHERE vendor LIKE 'Cisco IOS%' AND inactive_indicator = 0
                    '''
    if site_code:
        queryStr += f"AND hostname LIKE '%{site_code}%'"
    rows = runQueryGetRows(queryStr, os.environ['SERVICE_ACCOUNT_USERNAME'], 'sql.domain.com', 'Central', password, True)
    nonDuplicatedHostnames = []
    for row in rows:
        if '-wireless' in row['hostname'].lower():
            pass
        elif '-security' in row['hostname'].lower():
            pass
        elif '-firewall' in row['hostname'].lower():
            pass
        elif '-ips' in row['hostname'].lower():
            pass
        else:
            item = getFQDNAndIPAddress(row['hostname'].upper().split('.')[0])
        if not item in nonDuplicatedHostnames:
            nonDuplicatedHostnames.append(item)
    for row in nonDuplicatedHostnames:
        queue.put(row)
    return

def getDevicesForm(queue,form):
    nonDuplicatedHostnames = []
    for row in form['devices'].splitlines():
        if '-wireless' in row.lower():
            pass
        elif '-security' in row.lower():
            pass
        else:
            item = getFQDNAndIPAddress(row.upper().split('.')[0])
        if not item in nonDuplicatedHostnames:
            nonDuplicatedHostnames.append(item)
    for row in nonDuplicatedHostnames:
        queue.put(row)
    return

def ios(device,username,password,outputList,ouiOutputList,intOutputList):
    try:
        try:
            connection = netmiko.ConnectHandler(ip=device, device_type='cisco_ios',username=username,password=password,global_delay_factor=10)
        except netmiko.ssh_exception.NetMikoAuthenticationException or paramiko.ssh_exception.AuthenticationException:
            sleep(1)
            print(f'!\nFirst Authentication Attempt Failed for {device}\n!\n!')
            connection = netmiko.ConnectHandler(ip=device, device_type='cisco_ios',username=username,password=password,global_delay_factor=10)

        ipadd = socket.getaddrinfo(device,0,0,0,0)[-1][-1][0]

        pid_sn = connection.send_command_timing('show inv | begin PID').strip().splitlines()[0].split()
        try:
            if pid_sn[1].strip() == ',':
                pid_sn[1] = connection.send_command_timing('show inv | include '+pid_sn[-1]).strip().splitlines()[1].split()[1]
            if ('ASR1' in pid_sn[1].strip()) or ('ISR4' in pid_sn[1].strip()):
                return
        except IndexError:
            # Print Full Exception
            print(f'{device} PID failed discovery.')
            print(traceback.format_exc())
            print(pid_sn)

        image = connection.send_command_timing('show version | in image').strip().split(':')[-1].split('/')[-1].replace('"','')
        if len(image) < 5 or not '.bin' in image:
            image = connection.send_command_timing('show bootvar | in =').strip().split(';')[0].split(':')[-1].split(',')[0].replace('/','')
            if 'invalid' in image.lower():
                image = connection.send_command_timing('show boot | in =').strip().split(':')[-1].split(',')[0]
            if 'packages.conf' in image or 'BOOT variable' in image:
                image = ''


        supervisor = 'None'
        vtp_mode = 'NULL'
        user_vlan    = 'NULL'
        general_vlan = 'NULL'
        voice_1_vlan = 'NULL'
        voice_2_vlan  = 'NULL'
        voice_3_vlan   = 'NULL'
        voice_4_vlan   = 'NULL'
        lwap_vlan   = 'NULL'
        sec_vlan = 'NULL'


        status = 'Unknown'
        vtp_mode = 'Unknown'
        output = connection.send_command_timing('show inv | in SUP|WS-X4013|WS-X4515|WS-X4516|S720-10G|S2T-10G')
        if 'PID:' in output:
            for line in output.strip().splitlines():
                if 'PID:' in line:
                    supervisor = line.strip().split()[1].strip()
                    break
        output = connection.send_command_timing('show vtp status | in Operating Mode').strip().split()[-1].strip()
        if output and not 'marker' in output:
            vtp_mode = output
        vlans = connection.send_command_timing('show vlan brief | include active').strip().splitlines()
        try:
            for vlan in vlans:
                if 'user_vlan' == vlan.split()[1].strip():
                    user_vlan = vlan.split()[0].strip()
                elif 'general_vlan' == vlan.split()[1].strip():
                    general_vlan = vlan.split()[0].strip()
                elif 'voice_1_vlan' == vlan.split()[1].strip():
                    voice_1_vlan = vlan.split()[0].strip()
                elif 'voice_2_vlan' == vlan.split()[1].strip():
                    voice_2_vlan = vlan.split()[0].strip()
                elif 'voice_3_vlan' == vlan.split()[1].strip():
                    voice_3_vlan = vlan.split()[0].strip()
                elif 'voice_4_vlan' == vlan.split()[1].strip():
                    voice_4_vlan = vlan.split()[0].strip()
                elif 'lwap_vlan' == vlan.split()[1].strip():
                    lwap_vlan = vlan.split()[0].strip()
                elif 'sec_vlan' == vlan.split()[1].strip():
                    sec_vlan = vlan.split()[0].strip()
        except:
            pass

        lldpNeighbors = connection.send_command_timing('sh lldp neighbors detail | in Local Intf|System Name').strip().splitlines()
        lldpNeighborsDictionary = {}
        interface = ''
        for lines in lldpNeighbors:
            if 'Local Intf:' in lines:
                interface = lines.split(':')[-1].strip()
            elif 'System Name:' in lines:
                lldpNeighborsDictionary.update({interface:lines.split(':')[-1].strip()})

        trunks = connection.send_command_timing('show int trunk | include trunking').strip().splitlines()
        trunkInts = []
        for lines in trunks:
            trunkInts.append(lines.split()[0].strip())
            trunkInts.append(lines.split()[0].strip().replace('Po','Port-channel').replace('Gi','GigabitEthernet').replace('Fa','FastEthernet').replace('Te','TenGigabitEthernet'))

        ints = connection.send_command_timing('show int status | in /').strip().splitlines()
        int_count = len(ints)
        dot1x_ints = connection.send_command_timing('show dot1x all | in Info').strip().splitlines()
        dot1x_int_count = len(dot1x_ints)

        int_dict = {}

        for line in ints:
            interface = line.split()[0]
            int_dict[interface] = {}
            if 'trunk' in line:
                int_dict[interface]['type'] = 'Trunk'
            else:
                int_dict[interface]['type'] = 'Access'
            int_dict[interface]['description'] = 'NULL'
            int_dict[interface]['dot1x'] = 'Non-Dot1x'
            int_dict[interface]['mac'] = 'NULL'

        for line in dot1x_ints:
            interface = line.split()[-1].replace('GigabitEthernet','Gi').replace('FastEthernet','Fa').replace('TenGigabitEthernet','Te')
            try:
                int_dict[interface]['dot1x'] = 'Dot1x'
            except KeyError:
                int_dict[interface] = {}
                int_dict[interface]['description'] = 'NULL'
                int_dict[interface]['dot1x'] = 'Dot1x'
                int_dict[interface]['type'] = 'Access'
                int_dict[interface]['mac'] = 'NULL'
        # Extract All interesting configurations from running config
        output = connection.send_command_timing('show run')
        hostname = re.search('hostname\s*(\S*)',output).group(1)
        domain = re.search('ip domain.name\s*(\S*)',output)
        if domain:
            hostname += '.'+domain.group(1)
        interface = None
        for line in output.strip().splitlines():
            if line.lower().startswith('aaa authentication dot1x default group '):
                try:
                    status = line.strip().split()[-1].strip()
                except:
                    status = ''
            elif line.lower().startswith('interface '):
                interface = line.split()[-1].replace('GigabitEthernet','Gi').replace('FastEthernet','Fa').replace('TenGigabitEthernet','Te')
            elif line.strip() == '!':
                if interface is not None:
                    try:
                        int_dict[interface]['description'] = interfaceDescription
                    except:
                        pass
                interface = None
                interfaceDescription = 'NULL'
            elif interface is not None:
                if line.startswith(' description'):
                    if 'Dot1xNR' in line:
                        interfaceDescription = 'Dot1xNR'
                    else:
                        interfaceDescription = line.replace(' description ','').replace("'","")

        output = connection.send_command_timing('show mac add | exclude '+(' |'.join(trunkInts))).strip().splitlines()
        for lines in output:
            if ('Gi' in lines or 'Fa' in lines or 'Te' in lines) and len(lines.split()) > 3:
                if not 'ffff' in lines and not lines.split()[-1] == 'Switch':
                    words = lines.strip().strip('*').strip().replace('TenGigabitEthernet','Te').replace('GigabitEthernet','Gi').replace('FastEthernet','Fa').strip().split()
                    if not words[-1] in trunkInts and not ',' in words[-1] and not '/' in words[0]:
                        try:
                            oui = ouiDB[words[1].replace('.','')[0:6].upper()]
                        except:
                            oui = 'Unknown'
                        try:
                            ouiOutputList.put((hostname.upper(),words[-1],words[0],words[1],oui,lldpNeighborsDictionary[words[-1]][:99]))
                        except:
                            ouiOutputList.put((hostname.upper(),words[-1],words[0],words[1],oui,'NULL'))
                        # Add MAC to int_dict
                        try:
                            int_dict[words[-1]]['mac'] = words[1]
                        except:
                            pass

        # Add output to output queue
        ### (hostname, status, int_count, dot1x_int_count, mgmt_ip, pid, supervisor, image, user_vlan, general_vlan, voice_1_vlan, voice_3_vlan, voice_2_vlan, voice_4_vlan, lwap_vlan, sec_vlan, vtp_mode)
        outputList.put((hostname.upper(), status, int_count, dot1x_int_count,ipadd,pid_sn[1].upper(),supervisor,image, user_vlan, general_vlan, voice_1_vlan, voice_3_vlan, voice_2_vlan, voice_4_vlan, lwap_vlan, sec_vlan, vtp_mode))

        # Add int_dict to output queue
        for item in int_dict:
            intOutputList.put((hostname.upper(),item,int_dict[item]['description'],int_dict[item]['type'],int_dict[item]['dot1x'],int_dict[item]['mac']))
        if connection:
            connection.disconnect()
        connection = None
    except Exception as e:
        print(f'{device} identified as IOS but was unable to run discovery: {str(e)}')
        # Print Full Exception
        print(traceback.format_exc())
    return

def threadedFunction(username,password,devices,outputList,ouiOutputList,intOutputList):
    while not devices.empty():
        device = devices.get_nowait()
        if device:
            try:
                ios(device,username,password,outputList,ouiOutputList,intOutputList)
            except:
                print(f'{device} has failed discovery via Netmiko.')
                # Print Full Exception
                print(traceback.format_exc())
    outputList.put(None)
    return
def intSQL(intOutputList,site_code=None,form=None):
    connection = pymysql.connect(host=os.environ['MYSQL_HOST2'],
                                 user=os.environ['MYSQL_USER2'],
                                 password=os.environ['MYSQL_PASSWORD2'],
                                 db=os.environ['MYSQL_DATABASE2'],
                                 charset='utf8mb4',
                                 autocommit=True,
                                 cursorclass=pymysql.cursors.DictCursor)
    with connection.cursor() as cursor:
        if not site_code and not form:
            cursor.execute('DELETE FROM int_discovered')
        elif site_code:
            cursor.execute(f"DELETE FROM int_discovered WHERE hostname LIKE '%{site_code}%'")

        finishedOutput = 'Running'
        while finishedOutput != 'Finished':
            result = intOutputList.get()
            if result == 'Finished':
                break
            try:
                cursor.execute("INSERT INTO int_discovered (hostname, interface, description, type, dot1x, mac) VALUES ('%s', '%s', '%s', '%s', '%s', '%s')" % result)
            except Exception as e:
                print('Exception occurred while attempting to write to SQL {str(e)}')
                print(result)

def ouiSQL(ouiOutputList,site_code=None,form=None):
    connection = pymysql.connect(host=os.environ['MYSQL_HOST2'],
                                 user=os.environ['MYSQL_USER2'],
                                 password=os.environ['MYSQL_PASSWORD2'],
                                 db=os.environ['MYSQL_DATABASE2'],
                                 charset='utf8mb4',
                                 autocommit=True,
                                 cursorclass=pymysql.cursors.DictCursor)
    with connection.cursor() as cursor:
        if not site_code and not form:
            cursor.execute('DELETE FROM oui_discovered')
        elif site_code:
            cursor.execute(f"DELETE FROM oui_discovered WHERE hostname LIKE '%{site_code}%'")

        finishedOutput = 'Running'
        while finishedOutput != 'Finished':
            result = ouiOutputList.get()
            if result == 'Finished':
                break
            try:
                cursor.execute("INSERT INTO oui_discovered (hostname, interface, vlan, mac, oui, lldp_neighbor) VALUES ('%s', '%s', '%s', '%s', '%s', '%s')" % result)
            except Exception as e:
                print(f'Exception occurred while attempting to write to SQL {str(e)}')
                print(result)

def runDiscovery(site_code = None, form=None):
    ### set up logging and variables needed to pass through to threads
    NUM_THREADS = 300
    starttime = f'Starting threads.... {str(datetime.now())}'
    deviceList = queue.Queue()
    outputList = queue.Queue()
    ouiOutputList = queue.Queue()
    intOutputList = queue.Queue()
    


    ### fill device queue with device information
    if form:
        getDevicesForm(deviceList, form)
    else:
        getDevicesSQL(deviceList, site_code)
    print(f'Using {NUM_THREADS} threads to discover {deviceList.qsize()} devices')
    outputList.put(('NONE', 'total_switches', deviceList.qsize(), 0,'NONE','NONE','NONE','NONE', 0,0, 0, 0, 0, 0, 0, 0, 'NONE'))


    ### start threads
    for i in range(NUM_THREADS):
        print(f'Starting thread {i}...')
        Thread(target=threadedFunction, args=(username,password,deviceList,outputList,ouiOutputList,intOutputList)).start()
    Thread(target=ouiSQL, args=[ouiOutputList,site_code,form]).start()
    Thread(target=intSQL, args=[intOutputList,site_code,form]).start()

    numDone = 0
    connection = pymysql.connect(host=os.environ['MYSQL_HOST2'],
                                 user=os.environ['MYSQL_USER2'],
                                 password=os.environ['MYSQL_PASSWORD2'],
                                 db=os.environ['MYSQL_DATABASE2'],
                                 charset='utf8mb4',
                                 autocommit=True,
                                 cursorclass=pymysql.cursors.DictCursor)
    with connection.cursor() as cursor:
        if not site_code:
            cursor.execute('DELETE FROM ise_info')
        else:
            cursor.execute(f"DELETE FROM ise_info WHERE hostname LIKE '%{site_code}%'")

        print(f'SQL num thread {str(NUM_THREADS)})
        while numDone < NUM_THREADS:
            result = outputList.get()
            if result is None:
                numDone += 1
                print(f'SQL numDone {str(numDone)}')
            else:
                # record in DB looks like (device_guid, hostname, management_ip_address, serial_number, vendor, hardware_pid, sw_image_name, date, inactive_indicator)
                try:
                    cursor.execute("INSERT INTO ise_info (hostname, status, int_count, dot1x_int_count, mgmt_ip, pid, supervisor, image, user_vlan, general_vlan, voice_1_vlan, voice_3_vlan, voice_2_vlan, voice_4_vlan, lwap_vlan, sec_vlan, vtp_mode) VALUES ('%s', '%s', %s, %s, '%s', '%s', '%s', '%s', %s, %s, %s, %s, %s, %s, %s, %s, '%s')" % result)
                except Exception as e:
                    print(f'Exception occurred while attempting to write to SQL {str(e)})
                    print(str(result))
        intOutputList.put('Finished')
        ouiOutputList.put('Finished')
    print('!!!!! Completed Network Discovery !!!!!')
    # Generate HTML Files for Status tables
    Thread(target=BuildStatusTables).start()
    return

password = os.environ['SERVICE_ACCOUNT_PASSWORD']
username = os.environ['SERVICE_ACCOUNT_USERNAME'].split('\\')[-1]
ouiDB = {}
with open('templates/oui.csv','r') as ouiFile:
    for lines in ouiFile.read().replace("'",' ').strip().splitlines():
        lines = lines.split(',')
        ouiDB.update({lines[0]:lines[1]})
