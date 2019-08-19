import os
import sys
import jinja2
import pymysql
import pymssql
sys.path.append('templates')

createPrePostTableQuery = '''
CREATE TABLE IF NOT EXISTS ise_pre_post (
        crq_number VARCHAR(20) NOT NULL,
        pre_post VARCHAR(5) NOT NULL,
        hostname VARCHAR(50) NOT NULL,
        interface VARCHAR(50) NOT NULL,
        mac VARCHAR(20) NOT NULL,
        ip VARCHAR(20) NULL,
        vlan VARCHAR(50) NOT NULL,
        method VARCHAR(50) NOT NULL,
        domain VARCHAR(50) NOT NULL,
        status VARCHAR(10) NOT NULL);
'''
createAuthSessTableQuery = '''
CREATE TABLE IF NOT EXISTS ise_post_auth_sessions (
        hostname VARCHAR(50) NOT NULL,
        interface VARCHAR(50) NOT NULL,
        ip VARCHAR(20) NULL,
        vlan VARCHAR(5) NOT NULL,
        username VARCHAR(100) NOT NULL,
        acl VARCHAR(100) NOT NULL);
'''
createOUITableQuery = '''
CREATE TABLE IF NOT EXISTS oui_discovered (
        hostname varchar(50) NOT NULL,
        interface varchar(50) NOT NULL,
        vlan varchar(50) NOT NULL,
        mac varchar(50) NOT NULL,
        oui varchar(100) NOT NULL,
        lldp_neighbor varchar(200) NULL);
'''
createINTTableQuery = '''
CREATE TABLE IF NOT EXISTS int_discovered (
        hostname varchar(50) NOT NULL,
        interface varchar(50) NOT NULL,
        description varchar(200) NULL,
        type varchar(50) NOT NULL,
        dot1x varchar(50) NOT NULL,
        mac varchar(50) NULL);
'''
createISETableQuery = '''
CREATE TABLE IF NOT EXISTS ise_info (
        hostname varchar(50) NOT NULL,
        status varchar(50) NOT NULL,
        int_count int(10)  NULL,
        dot1x_int_count int(10)  NULL,
        mgmt_ip varchar(50) NOT NULL,
        pid varchar(50) NOT NULL,
        supervisor varchar(50)  NULL,
        image varchar(200)  NULL,
        vtp_mode varchar(50) NOT NULL,
        user_vlan int(10)  NULL,
        general_vlan int(10)  NULL,
        voice_1_vlan int(10)  NULL,
        voice_2_vlan int(10)  NULL,
        voice_3_vlan int(10)  NULL,
        voice_4_vlan int(10)  NULL,
        lwap_vlan int(10)  NULL,
        sec_vlan int(10)  NULL);
'''

def runQueryGetRows(queryString, username=os.environ['MYSQL_USER2'], server=os.environ['MYSQL_HOST2'], database=os.environ['MYSQL_DATABASE2'], password=os.environ['MYSQL_PASSWORD2'], resultsAsDict=True):
    with pymssql.connect(server, username, password, database) as conn:
        with conn.cursor(as_dict=resultsAsDict) as cursor:
            cursor.execute(queryString)
            return cursor.fetchall()

def runQueryGetRowsv2(queryString):
    mySQLConnection = pymysql.connect(host=os.environ['MYSQL_HOST2'],
                                      user=os.environ['MYSQL_USER2'],
                                      password=os.environ['MYSQL_PASSWORD2'],
                                      db=os.environ['MYSQL_DATABASE2'],
                                      charset='utf8mb4',
                                      cursorclass=pymysql.cursors.DictCursor)
    with mySQLConnection.cursor() as cursor:
        cursor.execute(queryString)
        return cursor.fetchall()

def executeQuery(queryString):
    print(queryString)
    mySQLConnection = pymysql.connect(host=os.environ['MYSQL_HOST2'],
                                      user=os.environ['MYSQL_USER2'],
                                      password=os.environ['MYSQL_PASSWORD2'],
                                      db=os.environ['MYSQL_DATABASE2'],
                                      charset='utf8mb4',
                                      autocommit=True,
                                      cursorclass=pymysql.cursors.DictCursor)
    with mySQLConnection.cursor() as cursor:
        cursor.execute(queryString)
    return

def create_base_tables():
    executeQuery(createPrePostTableQuery)
    executeQuery(createAuthSessTableQuery)
    executeQuery(createOUITableQuery)
    executeQuery(createINTTableQuery)
    executeQuery(createISETableQuery)

def getBody(country_code='',site_code=''):
    mySQLConnection = pymysql.connect(host=os.environ['MYSQL_HOST2'],
                                      user=os.environ['MYSQL_USER2'],
                                      password=os.environ['MYSQL_PASSWORD2'],
                                      db=os.environ['MYSQL_DATABASE2'],
                                      charset='utf8mb4',
                                      cursorclass=pymysql.cursors.DictCursor)
    html = ''
    with mySQLConnection.cursor() as cursor:
        cursor.execute('SELECT column_name from information_schema.columns where table_name="ise_info"')
        column_name = []
        query = cursor.fetchall()
        for items in query:
            if items['column_name'] != 'switch_id':
                column_name.append(items['column_name'])
        cursor.execute(f'SELECT * FROM ise_info WHERE hostname LIKE "%{site_code}%" ORDER BY hostname')
        switchInfo = cursor.fetchall()
        html = jinja2.Environment(trim_blocks=True, lstrip_blocks=True).from_string(jinjaTable).render(
                switchInfo=switchInfo,
                column_name=column_name,
                title='Site Switch List',
                filtertype='Filter by Switch Name')
    return html

def getOUITableSite(site_code, queryString = ''):
    mySQLConnection = pymysql.connect(host=os.environ['MYSQL_HOST2'],
                                      user=os.environ['MYSQL_USER2'],
                                      password=os.environ['MYSQL_PASSWORD2'],
                                      db=os.environ['MYSQL_DATABASE2'],
                                      charset='utf8mb4',
                                      cursorclass=pymysql.cursors.DictCursor)
    html = ''
    with mySQLConnection.cursor() as cursor:
        cursor.execute('SELECT column_name from information_schema.columns where table_name="oui_discovered"')
        column_name = []
        query = cursor.fetchall()
        for items in query:
            if items['column_name'] != 'switch_id':
                column_name.append(items['column_name'])
        if queryString:
            cursor.execute(queryString)
        else:
            cursor.execute(f'SELECT * FROM oui_discovered WHERE hostname LIKE "%{site_code}%" ORDER BY hostname')
        switchInfo = cursor.fetchall()
        html = jinja2.Environment(trim_blocks=True, lstrip_blocks=True).from_string(jinjaTable).render(
                switchInfo=switchInfo,
                column_name=column_name,
                title='Endpoint List',
                filtertype='Filter by Switch Name')
    return html



def getOUITable(hostname, queryString = ''):
    mySQLConnection = pymysql.connect(host=os.environ['MYSQL_HOST2'],
                                      user=os.environ['MYSQL_USER2'],
                                      password=os.environ['MYSQL_PASSWORD2'],
                                      db=os.environ['MYSQL_DATABASE2'],
                                      charset='utf8mb4',
                                      cursorclass=pymysql.cursors.DictCursor)
    html = ''
    with mySQLConnection.cursor() as cursor:
        cursor.execute('SELECT column_name from information_schema.columns where table_name="oui_discovered"')
        column_name = []
        query = cursor.fetchall()
        for items in query:
            if items['column_name'] != 'switch_id':
                column_name.append(items['column_name'])
        if queryString:
            cursor.execute(queryString)
        else:
            cursor.execute(f'SELECT * FROM oui_discovered WHERE hostname = "{hostname}"')
        switchInfo = cursor.fetchall()
        html = jinja2.Environment(trim_blocks=True, lstrip_blocks=True).from_string(jinjaTable).render(
                switchInfo=switchInfo,
                column_name=column_name,
                title='Endpoint List',
                filtertype='Filter by Switch Name')
    return html

def getOUIList():
    listOfOUI = []
    output = runQueryGetRowsv2('SELECT DISTINCT oui FROM oui_discovered  ORDER BY oui')
    for entry in output:
        listOfOUI.append(entry['oui'])
    return listOfOUI

def getResultsFromOUI(ouiDictionary):
    tempList = []
    for key,value in ouiDictionary.items():
        if key != 'siteCode':
            tempList.append(value)
    if ouiDictionary['siteCode'] == '':
        queryString = 'SELECT * FROM oui_discovered WHERE (oui = "'+'" OR oui = "'.join(tempList)+'") ORDER BY hostname'
    else:
        queryString = 'SELECT * FROM oui_discovered WHERE hostname LIKE "'+ouiDictionary['siteCode']+'%" AND (oui = "'+'" OR oui = "'.join(tempList)+'") ORDER BY hostname'
    return getOUITable('',queryString=queryString)

def getResultsFromMAC(macDictionary):
    tempList = []
    for key,value in macDictionary.items():
        if key != 'siteCode':
            tempList.append(value)
    queryString = 'SELECT * FROM oui_discovered WHERE (mac = "'+'" OR mac = "'.join(tempList)+' ") ORDER BY hostname'
    return getOUITable('',queryString=queryString)

def BuildStatusTables():
    html = ''
    mySQLConnection = pymysql.connect(host=os.environ['MYSQL_HOST2'],
                                      user=os.environ['MYSQL_USER2'],
                                      password=os.environ['MYSQL_PASSWORD2'],
                                      db=os.environ['MYSQL_DATABASE2'],
                                      charset='utf8mb4',
                                      cursorclass=pymysql.cursors.DictCursor)
    with mySQLConnection.cursor() as cursor:
        cursor.execute('SELECT column_name from information_schema.columns where table_name="ise_info"')
        column_name = []
        query = cursor.fetchall()
        for items in query:
            if items['column_name'] != 'switch_id':
                column_name.append(items['column_name'])
        cursor.execute("SELECT * FROM ise_info WHERE status LIKE 'NAC_%' ORDER BY hostname")
        switchInfo = cursor.fetchall()
        html = jinja2.Environment(trim_blocks=True, lstrip_blocks=True).from_string(jinjaTable).render(
                switchInfo=switchInfo,
                column_name=column_name,
                title='ISE Switches',
                filtertype='Filter by Switch Name')
        with open('templates/ISE_Status.html','w') as F:
            F.write(html)
    print('Done Writing ISE Table HTML')

    with mySQLConnection.cursor() as cursor:
        cursor.execute('SELECT column_name from information_schema.columns where table_name="ise_info"')
        column_name = []
        query = cursor.fetchall()
        for items in query:
            if items['column_name'] != 'switch_id':
                column_name.append(items['column_name'])
        cursor.execute("SELECT * FROM ise_info WHERE (status NOT LIKE  'NAC_%' AND status NOT LIKE  'total_switches')  ORDER BY hostname")
        switchInfo = cursor.fetchall()
        html = jinja2.Environment(trim_blocks=True, lstrip_blocks=True).from_string(jinjaTable).render(
                switchInfo=switchInfo,
                column_name=column_name,
                title='ACS Switches',
                filtertype='Filter by Switch Name')
        with open('templates/ACS_Status.html','w') as F:
            F.write(html)
    print('Done Writing ACS Table HTML')

def GetStatusTables(json):
    html = ''
    site_code = json['site_code']
    mySQLConnection = pymysql.connect(host=os.environ['MYSQL_HOST2'],
                                      user=os.environ['MYSQL_USER2'],
                                      password=os.environ['MYSQL_PASSWORD2'],
                                      db=os.environ['MYSQL_DATABASE2'],
                                      charset='utf8mb4',
                                      cursorclass=pymysql.cursors.DictCursor)
    if json['label'] == 'Dot1x':
        with mySQLConnection.cursor() as cursor:
            cursor.execute('SELECT column_name from information_schema.columns where table_name="int_discovered"')
            column_name = []
            query = cursor.fetchall()
            for items in query:
                if items['column_name'] != 'switch_id':
                    column_name.append(items['column_name'])
            cursor.execute("SELECT * FROM int_discovered WHERE dot1x LIKE 'Dot1x' AND hostname LIKE '"+ site_code +"%'")
            switchInfo = cursor.fetchall()
            html = jinja2.Environment(trim_blocks=True, lstrip_blocks=True).from_string(jinjaTable).render(
                    switchInfo=switchInfo,
                    column_name=column_name,
                    title='802.1x Switchports',
                    filtertype='Filter by Switch Name')
            return html
    elif json['label'] == 'NonDot1x':
        with mySQLConnection.cursor() as cursor:
            cursor.execute('SELECT column_name from information_schema.columns where table_name="int_discovered"')
            column_name = []
            query = cursor.fetchall()
            for items in query:
                if items['column_name'] != 'switch_id':
                    column_name.append(items['column_name'])
            cursor.execute("SELECT * FROM int_discovered WHERE dot1x LIKE 'Non-Dot1x' AND hostname LIKE '"+ site_code +"%'")
            switchInfo = cursor.fetchall()
            html = jinja2.Environment(trim_blocks=True, lstrip_blocks=True).from_string(jinjaTable).render(
                    switchInfo=switchInfo,
                    column_name=column_name,
                    title='Non-802.1x Switchports',
                    filtertype='Filter by Switch Name')
            return html
    elif json['label'] == 'Dot1xEndpoints':
        with mySQLConnection.cursor() as cursor:
            cursor.execute('SELECT column_name from information_schema.columns where table_name="int_discovered"')
            column_name = []
            query = cursor.fetchall()
            for items in query:
                if items['column_name'] != 'switch_id':
                    column_name.append(items['column_name'])
            cursor.execute("SELECT * FROM int_discovered WHERE dot1x LIKE 'Dot1x' AND mac NOT LIKE 'NULL' AND hostname LIKE '"+ site_code +"%'")
            switchInfo = cursor.fetchall()
            html = jinja2.Environment(trim_blocks=True, lstrip_blocks=True).from_string(jinjaTable).render(
                    switchInfo=switchInfo,
                    column_name=column_name,
                    title='802.1x Endpoints',
                    filtertype='Filter by Switch Name')
            return html
    elif json['label'] == 'NonDot1xEndpoints':
        with mySQLConnection.cursor() as cursor:
            cursor.execute('SELECT column_name from information_schema.columns where table_name="int_discovered"')
            column_name = []
            query = cursor.fetchall()
            for items in query:
                if items['column_name'] != 'switch_id':
                    column_name.append(items['column_name'])
            cursor.execute("SELECT * FROM int_discovered WHERE dot1x LIKE 'Non-Dot1x' AND mac NOT LIKE 'NULL' AND hostname LIKE '"+ site_code +"%'")
            switchInfo = cursor.fetchall()
            html = jinja2.Environment(trim_blocks=True, lstrip_blocks=True).from_string(jinjaTable).render(
                    switchInfo=switchInfo,
                    column_name=column_name,
                    title='Non-802.1x Endpoints',
                    filtertype='Filter by Switch Name')
            return html
    return html

def getNumResult(queryType):
    if queryType == 'num_passing':
        queryString = "SELECT COUNT(*) FROM ise_info WHERE status LIKE 'NAC_%'"
        result = runQueryGetRowsv2(queryString)[0]['COUNT(*)']
    elif queryType == 'num_failing':
        queryString = "SELECT COUNT(*) FROM ise_info WHERE status NOT LIKE 'NAC_%'  "
        result = runQueryGetRowsv2(queryString)[0]['COUNT(*)']
    elif queryType == 'num_int':
        queryString = "SELECT COUNT(*) FROM int_discovered"
        result = runQueryGetRowsv2(queryString)[0]['COUNT(*)']
    elif queryType == 'num_trunks':
        queryString = "SELECT COUNT(*) FROM int_discovered WHERE type LIKE 'Trunk'"
        result = runQueryGetRowsv2(queryString)[0]['COUNT(*)']
    elif queryType == 'num_dot1x':
        queryString = "SELECT COUNT(*) FROM int_discovered WHERE dot1x LIKE 'Dot1x'"
        result = runQueryGetRowsv2(queryString)[0]['COUNT(*)']
    elif queryType == 'num_non_dot1x':
        queryString = "SELECT COUNT(*) FROM int_discovered WHERE dot1x LIKE 'Non-Dot1x'"
        result = runQueryGetRowsv2(queryString)[0]['COUNT(*)']
    elif queryType == 'num_int_iAi':
        queryString = "SELECT COUNT(*) FROM int_discovered WHERE type NOT LIKE 'Trunk' AND dot1x LIKE 'Non-Dot1x' AND description LIKE 'iAi%'"
        result = runQueryGetRowsv2(queryString)[0]['COUNT(*)']
    elif queryType == 'num_int_iLi':
        queryString = "SELECT COUNT(*) FROM int_discovered WHERE type NOT LIKE 'Trunk' AND dot1x LIKE 'Non-Dot1x' AND description LIKE 'iLi%'"
        result = runQueryGetRowsv2(queryString)[0]['COUNT(*)']
    elif queryType == 'num_int_iPi':
        queryString = "SELECT COUNT(*) FROM int_discovered WHERE type NOT LIKE 'Trunk' AND dot1x LIKE 'Non-Dot1x' AND description LIKE 'iPi%'"
        result = runQueryGetRowsv2(queryString)[0]['COUNT(*)']
    elif queryType == 'num_int_Dot1xNR':
        queryString = "SELECT COUNT(*) FROM int_discovered WHERE type NOT LIKE 'Trunk' AND dot1x LIKE 'Non-Dot1x' AND description LIKE 'Dot1xNR'"
        result = runQueryGetRowsv2(queryString)[0]['COUNT(*)']
    elif queryType == 'num_int_iL4Si':
        queryString = "SELECT COUNT(*) FROM int_discovered WHERE type NOT LIKE 'Trunk' AND dot1x LIKE 'Non-Dot1x' AND description LIKE '@L4S@%'"
        result = runQueryGetRowsv2(queryString)[0]['COUNT(*)']
    elif queryType == 'num_int_iUi':
        queryString = "SELECT COUNT(*) FROM int_discovered WHERE type NOT LIKE 'Trunk' AND dot1x LIKE 'Non-Dot1x' AND description LIKE '@U@%'"
        result = runQueryGetRowsv2(queryString)[0]['COUNT(*)']
    elif queryType == 'num_int_null':
        queryString = "SELECT COUNT(*) FROM int_discovered WHERE type NOT LIKE 'Trunk' AND dot1x LIKE 'Non-Dot1x' AND description LIKE 'NULL'"
        result = runQueryGetRowsv2(queryString)[0]['COUNT(*)']
    elif queryType == 'num_endpoints':
        queryString = "SELECT COUNT(DISTINCT mac) FROM int_discovered"
        result = runQueryGetRowsv2(queryString)[0]['COUNT(DISTINCT mac)']
    elif queryType == 'num_dot1x_endpoints':
        queryString = "SELECT COUNT(DISTINCT mac) FROM int_discovered WHERE dot1x LIKE 'Dot1x' AND mac NOT LIKE 'NULL'"
        result = runQueryGetRowsv2(queryString)[0]['COUNT(DISTINCT mac)']
    elif queryType == 'num_non_dot1x_endpoints':
        queryString = "SELECT COUNT(DISTINCT mac) FROM int_discovered WHERE dot1x LIKE 'Non-Dot1x' AND mac NOT LIKE 'NULL'"
        result = runQueryGetRowsv2(queryString)[0]['COUNT(DISTINCT mac)']
    elif queryType == 'total_switches':
        queryString = "SELECT int_count FROM ise_info WHERE status LIKE 'total_switches'"
        result = runQueryGetRowsv2(queryString)[0]['int_count']

    return result

def getSwitchTypeAhead(query='SELECT DISTINCT hostname FROM oui_discovered ORDER BY hostname;',Type='hostname'):
    mySQLConnection = pymysql.connect(host=os.environ['MYSQL_HOST2'],
                                      user=os.environ['MYSQL_USER2'],
                                      password=os.environ['MYSQL_PASSWORD2'],
                                      db=os.environ['MYSQL_DATABASE2'],
                                      charset='utf8mb4',
                                      cursorclass=pymysql.cursors.DictCursor)
    html = ''
    with mySQLConnection.cursor() as cursor:
        cursor.execute(query)
        hostnames = []
        query = cursor.fetchall()
        if Type == 'hostname':
            for items in query:
                hostname = items['hostname']
                if hostname not in hostnames:
                    hostnames.append(hostname)
        elif Type == 'site_code':
            for items in query:
                hostname = items['hostname'][:5]
                if hostname not in hostnames:
                    hostnames.append(hostname)
        html = jinja2.Environment(trim_blocks=True, lstrip_blocks=True).from_string(jinjaTypeAhead).render(hostnames=hostnames)
    return html

def getPostHostNameTypeAhead():
    return getSwitchTypeAhead(query='SELECT DISTINCT hostname FROM ise_pre_post WHERE pre_post="post" ORDER BY hostname;').replace(
            'TypeAheadBody','TypeAheadBodyPost').replace('SwitchNameSearchPage','SwitchNameSearchPagePost').replace(
            'SwitchNameSearchPageMenu','SwitchNameSearchPageMenuPost')

def getPostSiteCodeTypeAhead():
    return getSwitchTypeAhead(query='SELECT DISTINCT hostname FROM ise_info WHERE status NOT LIKE "total_switches" ORDER BY hostname;',Type='site_code').replace(
            'TypeAheadBody','TypeAheadBodySite').replace('SwitchNameSearchPage','SiteCodeSearchPagePost').replace(
            'SwitchNameSearchPageMenu','SiteCodeSearchPageMenuPost').replace(
            '"Type Hostname FQDN"','"Type 5 Character Site Code"').replace(
            '>Hostname<','>Site Code<').replace(
            'value=""','value="" pattern="([0-9a-fA-F]{5})"')

jinjaTypeAhead = '''
<div id="TypeAheadBody" class="c-field js-typeahead">
    <label for="" class="c-field__label">Hostname</label>
    <div class="c-field__body">
        <input type="" id="SwitchNameSearchPage" class="c-input js-typeahead SearchField" placeholder="Type Hostname FQDN" value="" onFocus="typeaheadFocus('SwitchNameSearchPageMenu')" onFocusOut="typeaheadLoseFocus('SwitchNameSearchPageMenu')" onKeyUp="typeaheadUpdate('SwitchNameSearchPageMenu', this)" />
        <div id="SwitchNameSearchPageMenu" class="c-field__menu js-typeahead-menu" style="z-index: 15;">
            <ul class="c-typeahead-list">
{% for suggestion in hostnames %}
                <li class="c-typeahead-list__item" onmousedown="typeaheadClick('SwitchNameSearchPage', '{{ suggestion }}')">
                    <span class="c-typeahead__suggestion">{{ suggestion }}</span>
                </li>
{% endfor %}
            </ul>
        </div>
    </div>
</div>'''

jinjaTable = open('templates/JinjaTable.html','r').read()
