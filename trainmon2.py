from enum import IntFlag
from mwlogger import Post
import sys
import os
import time
import json
from datetime import date

#Logging verbosity
log_verb = 1

class QueryTypes(IntFlag):
    DEPARTURES  = 0x1
    ARRIVALS    = 0x2
    DEP_ARR     = 0x3
    STOPS       = 0x4


# Prints the cmd line arguments and quits
def printCommandLineHelp():   
    print("")
    quit()


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
        log.info('State not handled yet')
        exit()            


    return arg_usrnm, arg_api_key, arg_service_id, arg_dep_st, arg_dep_time_id, \
        arg_arr_st, arg_arr_time_id, query_type, arg_log_verb



def getCredentials(cred_file_path):
    usr=''
    key=''
    cf = open(cred_file_path, 'r')
    cred_data = json.load(cf)
    cf.close()
    return cred_data['username'], cred_data['key']

####### [Main] #####################################################################################

log = Post('trainmon','main', log_verb)

user_id, api_key, service_id, dep_station, dep_time,  arr_station, arr_time, query_type, \
    log_verb = parseCmdLine()

