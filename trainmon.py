from enum import IntFlag
from rttapi.api import RttApi
from mwlogger import Post
import sys
import os
import time
import json
from datetime import date

class QueryTypes(IntFlag):
    DEPARTURES  = 0x1
    ARRIVALS    = 0x2
    DEP_ARR     = 0x3
    STOPS       = 0x4

TrainLocations = {
    None        :   "",
    "AT_PLAT"   :   "At platform",
    "APPR_STAT" :   "Appr. station",
    "APPR_PLAT" :   "Arriving",
    "DEP_PREP"  :   "Preparing to dep.",
    "DEP_READY" :   "Ready to depart"
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
            arg_usrnm = arg

        # API key argument
        elif lastArg == '-k':
            log.debug(f'API key specified on command line: {arg}')
            arg_api_key = arg

        # credentials file argument
        elif lastArg == '-c':
            arg_cred_file = arg

        # departing station argument
        elif lastArg == '-d':
            log.debug(f'Departing station specified on command line: {arg}')
            arg_dep_st = arg

        # arriving station arument
        elif lastArg == '-a':
            arg_arr_st = arg

        # departing time argument
        elif lastArg == '-td':
            arg_dep_time_id = parseTimeString(arg)

        # arriving time argument
        elif lastArg == '-ta':
            arg_arr_time_id = parseTimeString(arg)

        # service uid argument
        elif lastArg == '-s':
            arg_service_id = arg

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
        log.info('State not handled yet')
        exit()            


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
    else:
        return f'{ttg}m'

def createLatenessString(late : int, realtime : str) -> str:
    if late > 0:
        return f'{late}m late ({realtime})'
    elif late < 0:
        return f'{-late}m early ({realtime})'
    else:
        return f'On time'


def generate_arr_or_dep_line(serv_id, location, query_type : QueryTypes) -> str:
    result = ""
    station_name_width = 18
    lateness_width = 15
    pf_width = 10
    ttg_width = 5
    origin = location.origin[0].description
    dest = location.destination[0].description
    accepted_display_as = ''

    if query_type & QueryTypes.DEP_ARR == QueryTypes.DEPARTURES:
        realtime = location.realtime_departure
        booked_time = location.gbtt_booked_departure
        accepted_display_as = 'ORIGIN CALL'
    elif query_type & QueryTypes.DEP_ARR == QueryTypes.ARRIVALS:
        realtime = location.realtime_arrival
        booked_time = location.gbtt_booked_arrival
        accepted_display_as = 'DESTINATION CALL'
    else:
        raise Exception(f'Invalid value for query_type {query_type}')

    if(location.realtime_activated):
        if location.display_as in accepted_display_as:
            platform = f'Plat. {location.platform}'
            late = diffTimeStr(realtime, booked_time)
            ttg_str = createTTGString(realtime)

            if late > 0:
                lateness = f'{late}m late ({realtime})'
            elif late < 0:
                lateness = f'{-late}m early ({realtime})'
            else:
                lateness = f'On time'
        else:
            if 'CANCELLED' in location.display_as:
                lateness = "     Cancelled"
                platform = '  ---'
                ttg_str = ''
            else:
                return ''
                
        line = '{}: {}  {} {} {} {} --> {} {}'

        result = line.format(\
            serv_id, \
            booked_time, \
            lateness.ljust(lateness_width)[0:lateness_width], \
            ttg_str.ljust(ttg_width)[0:ttg_width], \
            platform.ljust(pf_width), \
            origin.ljust(station_name_width)[0:station_name_width], \
            dest.ljust(station_name_width)[0:station_name_width], \
            TrainLocations[location.service_location]
            )
    else:
        #result = f'Service {location.} not activated.'
        pass
    return result

def generate_arr_or_dep_list(services, query_type : QueryTypes):
    result=[]
    for service in services:
        service_line = generate_arr_or_dep_line(service.train_identity, service.location_detail, query_type) 
        if(service_line != ''): result.append(service_line)
        if(service.location_detail.cancel_reason_long_text != None):
            result.append(f'  >>> {service.location_detail.cancel_reason_long_text} <<<')
    return result

def generate_arr_and_dep_line(s_pair):
    station_name_width = 14
    lateness_width = 15
    pf_width = 10
    ttg_width = 5

    # If no destination station in the service pair
    if(s_pair[0] == None):
        booked_dep_time = s_pair[1].location_detail.origin[0].public_time
        real_dep_time = s_pair[1].location_detail.origin[0].public_time
        orig_name = s_pair[1].location_detail.origin[0].description
        display_as = s_pair[1].location_detail.display_as
        dep_ttg_str = createTTGString(real_dep_time)
        if '-' in dep_ttg_str.lower():
            dep_platform = 'Departed'
        else:
            dep_platform = '?'
    else:
        booked_dep_time = s_pair[0].location_detail.gbtt_booked_departure
        real_dep_time = s_pair[0].location_detail.realtime_departure
        orig_name = s_pair[0].location_detail.origin[0].description
        display_as = s_pair[0].location_detail.display_as
        dep_ttg_str = createTTGString(real_dep_time)
        dep_platform = s_pair[0].location_detail.platform

    train_id = s_pair[1].train_identity
    booked_arr_time = s_pair[1].location_detail.gbtt_booked_arrival
    real_arr_time = s_pair[1].location_detail.realtime_arrival
    arr_platform = s_pair[1].location_detail.platform
    dest_name = s_pair[1].location_detail.destination[0].description
    call_name = s_pair[1].location_detail.description

    if((s_pair[0] != None and s_pair[0].location_detail.realtime_activated) or s_pair[1].location_detail.realtime_activated):
        if dep_platform != 'Departed': dep_platform = f'Plat. {dep_platform}'
        arr_platform = f'Plat. {arr_platform}'
        
        dep_late = diffTimeStr(real_dep_time, booked_dep_time)
        dep_lateness = createLatenessString(dep_late, real_dep_time)
        
        arr_late = diffTimeStr(real_arr_time, booked_arr_time) 
        arr_lateness = createLatenessString(arr_late, real_arr_time)
        
        
        arr_ttg_str = createTTGString(real_arr_time)

        if 'CANCELLED' in display_as:
            arr_lateness = "     Cancelled"
            dep_lateness = "     Cancelled"
            dep_platform = '  ---'
            arr_platform = '  ---'
            dep_ttg_str = ''
            arr_ttg_str = ''
    else:
        return ''

    line = "{}: {} {} --> {} {} {} arr {} {} {} {}"
    result = line.format(\
        train_id,\
        booked_dep_time,\
        orig_name.ljust(station_name_width)[0:station_name_width],\
        dest_name.ljust(station_name_width)[0:station_name_width],\
        dep_platform.ljust(pf_width)[0:pf_width],\
        dep_lateness.ljust(lateness_width)[0:lateness_width],\
        booked_arr_time,\
        arr_lateness.ljust(lateness_width)[0:lateness_width],\
        arr_platform.ljust(pf_width)[0:pf_width],\
        call_name.ljust(station_name_width)[0:station_name_width])
    return result

def generate_arr_and_dep_list(d_services, a_services):
    result=[]

    s_pairs = []
    dest_stations = []
    train_ids = []

    # Find the matching services between the departures and arrivals and pair them up
    for d_service in d_services:
        for a_service in a_services:
            if(d_service.train_identity == a_service.train_identity\
                and (d_service, a_service) not in s_pairs):
                train_ids.append(d_service.train_identity)
                s_pairs.append((d_service, a_service))

    # Save the arrival and departure station name pairs and use these as a pattern to determin the
    # remaing arrival stations (that don't have pairs) to keep
    for s_pair in s_pairs:
        dest_name = s_pair[0].location_detail.destination[0].description
        if dest_name not in dest_stations:
            dest_stations.append(dest_name)

    # Go through the unmatched arrival entries, and filter out the entries that are going in the 
    # direction we want to go in
    for a_service in a_services:
        if(a_service.train_identity not in train_ids):
            dest_name = a_service.location_detail.destination[0].description
            if dest_name in dest_stations:
                s_pairs.insert(0,(None, a_service))


    # Sort s_pairs by arrival station time (not final dest or origin)
    sort_list = []
    for s_pair in s_pairs:
        sort_list.append((s_pair[1].location_detail.gbtt_booked_arrival, s_pair[1].train_identity))
        sort_list.sort()
    sorted_s_pairs = []
    for sort_item in sort_list:
        for s_pair in s_pairs:
            if s_pair[1].train_identity == sort_item[1]:
                sorted_s_pairs.append(s_pair)
                break

    # Create a list of service strings to pass to the print table function
    for s_pair in sorted_s_pairs:
        service_line = generate_arr_and_dep_line(s_pair) 
        if(service_line != ''): result.append(service_line)
        # if(s_pair[0].location_detail.cancel_reason_long_text != None):
        #     result.append(f'  >>> {s_pair[0].location_detail.cancel_reason_long_text} <<<')
        if(s_pair[1].location_detail.cancel_reason_long_text != None):
            result.append(f'  >>> {s_pair[1].location_detail.cancel_reason_long_text} <<<')

    return result


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

####### [Main] #####################################################################################

log = Post('trainmon','0', 1)

user_id, api_key, service_id, dep_station, dep_time,  arr_station, arr_time, query_type, \
    log_verb = parseCmdLine()

# Objects to store RttAPI info
dep=None
arr=None

log.info('Connecting to RTT API...')
try:
    td = RttApi(user_id, api_key)
except:
    err = sys.exc_info()
    log.error('There was and error retrieving information about the given service:')
    log.error(err[1])
    quit()

if query_type == QueryTypes.DEPARTURES:
    dep = get_arr_or_dep_data(td, dep_station, QueryTypes.DEPARTURES)
    print_table(f'Departures from {dep.location.name}', generate_arr_or_dep_list(dep.services, QueryTypes.DEPARTURES))

elif query_type == QueryTypes.ARRIVALS:
    arr = get_arr_or_dep_data(td, arr_station, QueryTypes.ARRIVALS)
    print_table(f'Arrivals at {arr.location.name}', generate_arr_or_dep_list(arr.services, QueryTypes.ARRIVALS))

else:
    dep = get_arr_or_dep_data(td, dep_station, QueryTypes.DEPARTURES)
    arr = get_arr_or_dep_data(td, arr_station, QueryTypes.ARRIVALS)
    print_table(f'Trains from {dep.location.name} to {arr.location.name}', generate_arr_and_dep_list(dep.services, arr.services))

# else:
#     # Show departure and arrival time for the given service
#     if service_id != '':
#         log.info(f'Identifying train by service ID ({service_id})...')
#         try: serv = td.fetch_service_info_datetime(service_id, date.today())
#         except:
#             err = sys.exc_info()
#             log.error(f'Failed to retrieve data for service {service_id}:')
#             log.error(err[1])
#             print('Invalid service or no connection.')
#             quit()

#         # Find the locations specified. Departure first:
        
#         log.debug('CRS\tTIPLOC\tDescr\tIs call')
#         for loc in serv.locations:
#             log.debug(f'{loc.crs}\t{loc.tiploc}\t{loc.description}\t{loc.is_call_public_simple}')

#         servDepLoc = [loc for loc in serv.locations \
#             if (loc.crs.lower().find(dep_station.lower()) != -1  or \
#                 loc.description.lower() == dep_station.lower() or \
#                     loc.tiploc.lower() == dep_station.lower())]

#         for loc in servDepLoc:
#             print(generate_service_line(serv.service_uid ,loc))

#         if len(servDepLoc) == 0:
#             print(f'Service {service_id} does not call at {dep_station}')
#             print('Valid stops:')
#             for stop in servDepLoc:
#                 print(f'{stop.crs} {stop.tiploc} "{stop.description}"')

#         log.info(f'Finished retrieving data for service ID ({service_id})...')
#     else:
#         log.info(f'Identifying train by departure time ({dep_time})...')



