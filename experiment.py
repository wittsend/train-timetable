from rttapi.api import RttApi
import PySimpleGUI as sg
from rttapi.model import LocationContainer, SearchResult

####################################################################################################
def generate_service_list(services):
    result=[]
    for service in services :
        if(service.location_detail.realtime_activated):
            result.append("{}: {} from {} to {}".format(\
                service.running_identity, \
                    service.location_detail.realtime_departure, \
                        service.location_detail.destination[0].description, \
                            service.location_detail.origin[0].description))
    return result

def get_all_destinations(services):
    result=[]

    for service in services:
        for dest in service.location_detail.destination:
            result.append(dest)

    return result


# Parses the command line arguments and returns the results.
def parseCmdLineOld():
    """---------------
    Command line args
    - List all services departing a given station
    trainmon  <api_username> <api_key> <departing_station>
    - Show departure and arrival times for the given train by departure time
    trainmon  <api_username> <api_key> <departing_station> <departing_time> <arriving_station>
    - Show departure and arrival times for the given train by service UID
    trainmon  <api_username> <api_key> <departing_station> <service_id>  <arriving_station>
    ---------------"""
    global log

    # Inputs
    arg_usrnm = None
    arg_api_key = None
    arg_dep_st = None
    arg_time_id = None
    arg_arr_st = None
    
    try: arg_usrnm = sys.argv[1] 
    except:
        print('Missing API username.')
        printCommandLineHelp() 
    try: arg_api_key = sys.argv[2]
    except:
        print('Missing API key.')
        printCommandLineHelp()
    try: arg_dep_st = sys.argv[3]
    except:
        print('Missing departing station')
        printCommandLineHelp()
    try: arg_time_id = sys.argv[4]
    except: pass
    try: arg_arr_st = arg_api_key
    except: pass

    # Outputs
    dep_time   = ''
    serv_uid    = ""
    dep_st      = ""
    arr_st      = ""
    usrnm       = ''
    apikey      = ''
    dep_only    = False

    
    if len(sys.argv) >= 6:
        dep_st = arg_dep_st
        usrnm = arg_usrnm
        apikey = arg_api_key
        arr_st = arg_arr_st
        log.info('Arriving station: {}'.format(arr_st))
        
        #Fourth arg is either the time or service ID. Time contains a colon to separate hours from mins
        cln = arg_time_id.find(':')
        if(cln != -1):
            try:
                hour = int(arg_time_id[:cln])
                min = int(arg_time_id[cln+1:])
                if(hour>23 or hour<0 or min>59 or min<0):
                    raise Exception('Invalid time')
                dep_time = '{0}{1}'.format(str(hour).zfill(2), str(min).zfill(2))
            except:
                print("Invalid time specified.")
                printCommandLineHelp()
            
            log.info(f"Using time for service: {dep_time}")
        else:
            serv_uid = arg_time_id
            log.info(f"Time not specified, assuming service ID for first arg ({serv_uid})")

    elif len(sys.argv) >= 4:
        # Just show the departures for the given station
        dep_only = True
        dep_st = arg_dep_st
        usrnm = arg_usrnm
        apikey = arg_api_key
        log.info(f'Departing station: {dep_st}')
        log.info(f'Username: {usrnm}')
        log.info(f'API key: {apikey}')
    
    else:
        print('Incorrect number of arguments')
        printCommandLineHelp()

    return serv_uid, dep_time, dep_st, arr_st, usrnm, apikey, dep_only


####################################################################################################


td = RttApi("rttapi_wittsend86","373cfeaf44e3157ba9ce016a48770399265220ce")


# Form layout
lyt_frm_main = [
    [sg.Text(text='From: ', key='lbl_selected_station_lbl'), sg.Input(default_text='LDS', key='txt_selected_station',  size=(15,1)), sg.Button(button_text='Search', key='cmd_search')],
    [sg.Text(text='To: ', key='lbl_dest'), sg.InputCombo(key='cmb_to_station', values=[], size=(25,1))],
    [sg.Listbox(values=[], size=(50,50), key='lstbox_trains')],
]

frm_main = sg.Window('Train timetable', lyt_frm_main)
frm_main.Read(timeout=50)

dep = td.search_station_departures(frm_main['txt_selected_station'].get())

arr = td.search_station_arrivals(frm_main['txt_selected_station'].get())

#dep.services[0]

try:
    while True:
        
        frm_main['txt_selected_station'](dep.location.name)
        frm_main['lstbox_trains'](generate_service_list(arr.services))

        event, value = frm_main.Read(timeout=10000)
        if event==sg.WIN_CLOSED:
            quit()

        if event=='cmd_search':
            dep = td.search_station_departures(frm_main['txt_selected_station'].get())
            arr = td.search_station_arrivals(frm_main['txt_selected_station'].get())
            #print([dest.description for dest in get_all_destinations(dep.services)])
            if(dep.filter != None):
                print(dep.filter.name)
            else:
                print('No filter data')
        

except KeyboardInterrupt:
    print('Execution interrupted by user')
    quit()