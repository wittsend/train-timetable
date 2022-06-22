from enum import IntFlag
# from rttapi.api import RttApi
from rttapi_extend import RttApi
from mwlogger import Post
import sys
import os
import time
import datetime
import json
import ansicolour
#from datetime import date

class QueryTypes(IntFlag):
    DEPARTURES  = 0x1
    ARRIVALS    = 0x2
    DEP_ARR     = 0x3
    SERVICE     = 0x4

TrainLocations = {
    None        :   "",
    "AT_PLAT"   :   "At platform",
    "APPR_STAT" :   "Apr. station",
    "APPR_PLAT" :   "Arriving",
    "DEP_PREP"  :   "Prep. to dep.",
    "DEP_READY" :   "Ready to dep.",
    "Departed"  :   "Departed"
}


# Prints the cmd line arguments and quits
def printCommandLineHelp():   
    print("")
    quit()


def getCredentials(cred_file_path):
    usr=''
    key=''
    cf = open(cred_file_path, 'r')
    cred_data = json.load(cf)
    cf.close()
    return cred_data['username'], cred_data['key']

def parseTimeString(timeStr: str):
    global log
    output = ''

    cln = timeStr.find(':')
    if(cln != -1):
        try:
            hour = int(timeStr[:cln])
            min = int(timeStr[cln+1:])
            if(hour>23 or hour<0 or min>59 or min<0):
                raise Exception('Invalid time')
            output = '{0}{1}'.format(str(hour).zfill(2), str(min).zfill(2))
        except:
            output = ''
            log.error('Time string is invalid. "{}"'.format(timeStr))    

    return output

def parseCmdLine():

    global log

    # Inputs
    arg_usrnm = ''
    arg_api_key = ''
    arg_cred_file = ''
    arg_dep_st = ''
    arg_dep_time_id = ''
    arg_arr_st = ''
    arg_arr_time_id = ''
    arg_service_id = ''
    arg_log_verb = 1
    query_type = 0

    lastArg = ''
    first = True
    for arg in sys.argv:
        if first:
            first = False
            continue

        if lastArg == '':
            lastArg = arg
            continue

        # username argument
        if lastArg == '-u':
            log.debug(f'User name specified on command line: {arg}')
            arg_usrnm = arg.strip()

        # API key argument
        elif lastArg == '-k':
            log.debug(f'API key specified on command line: {arg}')
            arg_api_key = arg.strip()

        # credentials file argument
        elif lastArg == '-c':
            arg_cred_file = arg.strip()

        # departing station argument
        elif lastArg == '-d':
            log.debug(f'Departing station specified on command line: {arg}')
            arg_dep_st = arg.strip()

        # arriving station arument
        elif lastArg == '-a':
            arg_arr_st = arg.strip()

        # departing time argument
        elif lastArg == '-td':
            arg_dep_time_id = parseTimeString(arg.strip())

        # arriving time argument
        elif lastArg == '-ta':
            arg_arr_time_id = parseTimeString(arg.strip())

        # service uid argument
        elif lastArg == '-s':
            arg_service_id = arg.strip()

        elif lastArg == '-v':
            arg_log_verb = int(arg)
            log.setVerbosity(arg_log_verb)

        else:
            pass

        lastArg = ''
        

    # Run the logic to determine that the correct args have been supplied

    # If user and key has been supplied, then use these, otherwise, look for credentials file
    if not (arg_usrnm != '' and arg_api_key != ''):
        log.info('No credentials supplied on the command line.')
        if arg_cred_file == '':
            # Look for credentials in script folder
            arg_cred_file = os.path.join(sys.path[0], 'credentials.json')
        log.info(f'Looking for credentials in {arg_cred_file}')
        try: 
            arg_usrnm, arg_api_key = getCredentials(arg_cred_file)
        except:
           print(f'Unable to load credentials from file "{arg_cred_file}". Cannot continue.') 
           quit()

    if arg_usrnm == '' or arg_api_key == '':
        print('No API credentials have been supplied!')
        printCommandLineHelp()
    else:
        log.info(f'API credentials; user:{arg_usrnm}, key:{arg_api_key}')

    # If no service ID
    # Must have a departing station, or arrival station (not both)
    if arg_service_id == '':
        if arg_arr_st != '':
            log.info("Station arrival query")
            query_type |= QueryTypes.ARRIVALS
        if arg_dep_st != '':
            log.info("Station departure query")
            query_type |= QueryTypes.DEPARTURES
        if not query_type & (QueryTypes.DEP_ARR):
            log.warning("No arrival or departure option specified. Don't know what to do")
            print("Must have arrival or departure options when no service ID specified")
            printCommandLineHelp()
    else:
        query_type = QueryTypes.SERVICE

    return arg_usrnm, arg_api_key, arg_service_id, arg_dep_st, arg_dep_time_id, \
        arg_arr_st, arg_arr_time_id, query_type, arg_log_verb




def findByTrainID(tid:str):
    return

def cvtTimeStrToMin(tStr : str) -> int:
    result = 0
    if len(tStr) != 4: 
        raise Exception(f'Time string should be 4 characters long not {len(tStr)}')
    result = int(tStr[0:2])*60 + int(tStr[2:4])
    return result

def diffTimeStr(tStrA : str, tStrB : str) -> int:
    if tStrA == None or tStrB == None: return 0
    return cvtTimeStrToMin(tStrA)-cvtTimeStrToMin(tStrB)

def createTTGString(time_str : str) -> str:
    timeNow = time.localtime(int(time.time()))
    timeNowStr = f'{timeNow.tm_hour:0>2}{timeNow.tm_min:0>2}'
    if time_str == '': return '-'
    ttg = diffTimeStr(time_str, timeNowStr)
    if(ttg >= 60):
        return f'{round(ttg/60.00,1)}h'
    elif ttg<0:
        return 'Dep.'
    else:
        return f'{ttg}m'

def createLatenessString(late : int, realtime : str) -> str:
    if late > 0:
        ls = f'{late}m late ({realtime})'
        #ls = ansicolour.set_str_colour(ls , 0, ansicolour.sgr.FG_WHITE, ansicolour.sgr.BG_RED,)
        return ls
    elif late < 0:
        return f'{-late}m early ({realtime})'
    else:
        return f'On time'



def generate_arr_or_dep_line(serv_id, loc, query_type : QueryTypes) -> str:
    result = ""
    station_name_width = 18
    lateness_width = 15
    pf_width = 10
    ttg_width = 5
    origin = loc.origin[0].description
    dest = loc.destination[0].description
    accepted_display_as = ''
    cancel_code = loc.cancel_reason_code

    if query_type & QueryTypes.DEP_ARR == QueryTypes.DEPARTURES:
        realtime = loc.realtime_departure
        booked_time = loc.gbtt_booked_departure
        accepted_display_as = 'ORIGIN CALL'
        locStr = f'to {dest}'
    elif query_type & QueryTypes.DEP_ARR == QueryTypes.ARRIVALS:
        realtime = loc.realtime_arrival
        booked_time = loc.gbtt_booked_arrival
        accepted_display_as = 'DESTINATION CALL'
        locStr = f'from {origin}'
    else:
        raise Exception(f'Invalid value for query_type {query_type}')

    if(loc.realtime_activated):
        if loc.display_as in accepted_display_as:
            platform = f'Plat. {loc.platform}'
            late = diffTimeStr(realtime, booked_time)
            if TrainLocations[loc.service_location] != '':
                lateness = TrainLocations[loc.service_location]
                ttg_str = ''
            else:
                ttg_str = createTTGString(realtime)
                lateness = createLatenessString(late, realtime)

            
        else:
            if 'CANCELLED' in loc.display_as:
                lateness = "     Cancelled"
                platform = '  ---'
                ttg_str = ''
            else:
                return ''
                
        #line = '{}: {}  {} {} {} {} --> {} {}'
        line = '{}: {} {}  {} {} {} {}'

        result = line.format(\
            serv_id, \
            booked_time, \
            locStr.ljust(station_name_width)[0:station_name_width],\
            lateness.ljust(lateness_width)[0:lateness_width], \
            ttg_str.ljust(ttg_width)[0:ttg_width], \
            platform.ljust(pf_width), \
            #origin.ljust(station_name_width)[0:station_name_width], \
            #dest.ljust(station_name_width)[0:station_name_width],\
            cancel_code,\
            )
    else:
        #result = f'Service {location.} not activated.'
        pass
    return result

def generate_arr_or_dep_list(services, query_type : QueryTypes):
    result=[]
    for service in services:
        service_line = generate_arr_or_dep_line(service.service_uid, service.location_detail, query_type) 
        if(service_line != ''): result.append(service_line)
        if(service.location_detail.cancel_reason_long_text != None):
            result.append(f'  >>> {service.location_detail.cancel_reason_long_text} <<<')
    return result

def generate_service_stop_line(serv_id, loc, query_type):
    result = ""
    station_name_width = 18
    lateness_width = 15
    pf_width = 10
    ttg_width = 5
    origin = loc.origin[0].description
    dest = loc.destination[0].description
    accepted_display_as = ''
    cancel_code = ''

    # Line is assigned here so that colour can be applied to it before the values are formatted in.
    #line = '{}: {}  {} {} {} {} --> {} {}'
    line = '{}: {} {}  {} {} {} {}'

    if query_type & QueryTypes.SERVICE != 0:
        realtime = loc.realtime_departure
        booked_time = loc.gbtt_booked_departure
        accepted_display_as = 'STARTS ORIGIN CALL DESTINATION'
        if loc.display_as == 'CALL':
            locStr = f'- {loc.description}'
        else:
            locStr = f'{loc.description}'
    elif query_type & QueryTypes.DEP_ARR == QueryTypes.DEPARTURES:
        realtime = loc.realtime_departure
        booked_time = loc.gbtt_booked_departure
        accepted_display_as = 'ORIGIN CALL'
        locStr = f'to {dest}'
    elif query_type & QueryTypes.DEP_ARR == QueryTypes.ARRIVALS:
        realtime = loc.realtime_arrival
        booked_time = loc.gbtt_booked_arrival
        accepted_display_as = 'DESTINATION CALL'
        locStr = f'from {origin}'
    else:
        raise Exception(f'Invalid value for query_type {query_type}')

    if(loc.realtime_activated):
        if loc.display_as in accepted_display_as:
            platform = f'Plat. {loc.platform}'
            if loc.platform_changed:
                platform = ansicolour.set_str_style(platform, [ansicolour.sgr.BLINK_SLW])
            late = diffTimeStr(realtime, booked_time)
            ttg_str = createTTGString(realtime)
            if ttg_str == 'Dep.':
                cancel_code = ''
                line = ansicolour.set_str_style(line, [ansicolour.sgr.FG_BLACK, ansicolour.sgr.BG_CYAN])
            if TrainLocations[loc.service_location] != '':
                lateness = TrainLocations[loc.service_location]
                ttg_str = ''
                line = ansicolour.set_str_style(line, [ansicolour.sgr.BOLD, ansicolour.sgr.FG_BLACK, ansicolour.sgr.BG_GREEN])
            else:
                lateness = createLatenessString(late, realtime)

            
        else:
            if 'CANCELLED' in loc.display_as:
                lateness = "     Cancelled"
                platform = '  ---'
                ttg_str = ''
                ansicolour.set_str_style(line, [ansicolour.sgr.BOLD, ansicolour.sgr.FG_WHITE, ansicolour.sgr.BG_RED])
            else:
                return ''
                


        result = line.format(\
            serv_id.ljust(6)[0:6], \
            booked_time, \
            locStr.ljust(station_name_width)[0:station_name_width],\
            lateness.ljust(lateness_width)[0:lateness_width], \
            ttg_str.ljust(ttg_width)[0:ttg_width], \
            platform.ljust(pf_width), \
            #origin.ljust(station_name_width)[0:station_name_width], \
            #dest.ljust(station_name_width)[0:station_name_width],\
            cancel_code,\
            )
    else:
        #result = f'Service {location.} not activated.'
        pass
    return result

def generate_service_stop_list(service, query_type):
    output = []
    for stop in service.locations:
        output.append(generate_service_stop_line(stop.display_as, stop, query_type))
    return output

def print_table(title:str, lineList):
    header_row = ''
    lines_output = ''
    footer_row = ''
    title = f'[ {title} ]'
    
    try:
        max_len = os.get_terminal_size().columns
        log.debug(f'Got terminal width of {max_len} columns')
    except:
        max_len = 100
        log.debug(f'Could not determine terminal width. Defaulting to {max_len} columns')

    for line in lineList:
        lines_output += ((line).expandtabs(4))[0:max_len-1] + os.linesep

    title_st = int((max_len-len(title))/2)
    title_end = title_st + len(title)
    for i in range(0,title_st):
        header_row += '='

    header_row += title

    for i in range (title_end, max_len):
        header_row += '='

    for i in range(0, max_len):
        footer_row += '-'

    print(f'{header_row}{os.linesep}{lines_output}{footer_row}')

def get_arr_or_dep_data(td, station, query_type):
    global log
    output = None
    log.info(f'Attempting to retrieve data for {station}...')
    try: 
        if query_type & QueryTypes.DEP_ARR == QueryTypes.DEPARTURES:
            output = td.search_station_departures(station)
        elif query_type & QueryTypes.DEP_ARR == QueryTypes.ARRIVALS:
            output = td.search_station_arrivals(station)
        else:
            raise Exception('Invalid query type')
    except:
        err = sys.exc_info()
        log.error(f'Failed to retrieve data for station {station}:')
        log.error(err[1])
        print('Invalid service or no connection.')
        quit()
    return output

def get_service_data_by_station(td, dep_station, arr_station):
    global log
    output = None
    log.info(f'Attempting to retrieve data for services departing {dep_station} and arriving at {arr_station}...')
    try: 
        output = td.search_service_by_stations(dep_station, arr_station)
    except:
        err = sys.exc_info()
        log.error(f'Failed to retrieve data for services from {dep_station} to {arr_station}:')
        log.error(err[1])
        print('Invalid service or no connection.')
        quit()
    return output

def get_service_data_by_uid(td, service_id, query_type):
    global log
    output = None
    log.info(f'Attempting to retrieve data for services ID {service_id}...')
    try: 
        output = td.fetch_service_info_datetime(service_id, datetime.datetime.now())
    except:
        err = sys.exc_info()
        log.error(f'Failed to retrieve data for service ID {service_id}:')
        log.error(err[1])
        print('Invalid service or no connection.')
        quit()
    return output

####### [Main] #####################################################################################

log = Post('trainmon','0', 1)

user_id, api_key, service_id, dep_station, dep_time,  arr_station, arr_time, query_type, \
    log_verb = parseCmdLine()

# Objects to store RttAPI info
dep=None
arr=None
serv=None

log.info('Connecting to RTT API...')
try:
    td = RttApi(user_id, api_key)
except:
    err = sys.exc_info()
    log.error('There was and error retrieving information about the given service:')
    log.error(err[1])
    quit()



if query_type & QueryTypes.SERVICE != 0:
    serv = get_service_data_by_uid(td, service_id, query_type)
    print_table(f'Service info for {service_id}', generate_service_stop_list(serv, query_type))

elif query_type == QueryTypes.DEPARTURES:
    dep = get_arr_or_dep_data(td, dep_station, QueryTypes.DEPARTURES)
    print_table(f'Departures from {dep.location.name}', generate_arr_or_dep_list(dep.services, QueryTypes.DEPARTURES))

elif query_type == QueryTypes.ARRIVALS:
    arr = get_arr_or_dep_data(td, arr_station, QueryTypes.ARRIVALS)
    print_table(f'Arrivals at {arr.location.name}', generate_arr_or_dep_list(arr.services, QueryTypes.ARRIVALS))

else:
    dep = get_service_data_by_station(td, dep_station, arr_station)
    print_table(f'Trains from {dep.location.name} to {dep.filter.name}', generate_arr_or_dep_list(dep.services, QueryTypes.DEPARTURES))




