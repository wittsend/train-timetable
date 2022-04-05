import rttapi.api as api
import rttapi.parser as parser
from rttapi.model import SearchResult, Service

class _Api(api._Api):
    
    def fetch_service_info_stations(self, credentials: tuple, station_code_dep: str, station_code_arr: str) -> dict:
        """
        Requests the list of upcoming departures from a given station.

        :param credentials: A username/password pair used for the HTTPBasicAuth challenge
        :param station_code: Either the three-letter CRS station code (CRS, e.g. 'CLJ') or the longer TIPLOC code (e.g. 'CLPHMJC')

        :return: A rttapi.model.SearchResult object mirroring the JSON reply
        """
        url = "{base}/json/search/{station1}/to/{station2}".format(base=self.__urlBase, station1=station_code_dep, station2=station_code_arr)
        return api._request_basic_auth(credentials, url)

# Extend the RttApi Api class with additional functionality
class RttApi(api.RttApi):

    def __init__(self, username: str, password: str):
        """
        Constructor for the RttApi object.

        :param username: The RealtimeTrains API username to authenticate with
        :param password: The password matching the RealtimeTrains API username
        """
        api.RttApi.__init__(self, username, password)
        self.__api = _Api()

    def search_service_info_stations(self, station_code_orig: str, station_code_dest: str) -> SearchResult:
        """
        Requests the list of upcoming departures from a given station, filtering by destination.

        :param station_code: Either the three-letter CRS station code (CRS, e.g. 'CLJ') or the longer TIPLOC code (e.g. 'CLPHMJC')

        :return: A rttapi.model.SearchResult object mirroring the JSON reply
        """
        json = self.__api.fetch_service_info_stations(self.credentials, station_code_orig, station_code_dest)
        return parser.parse_search(json)

