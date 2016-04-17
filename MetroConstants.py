URL_LINES_LIST = "https://api.wmata.com/Rail.svc/json/jLines"
URL_STATION_LIST = "https://api.wmata.com/Rail.svc/json/jStations" # ?LineCode=<code>
URL_STATION_STATION_INFO = "https://api.wmata.com/Rail.svc/json/jSrcStationToDstStationInfo" # ?ToStationCode=<code>
URL_STATION_PATH = "https://api.wmata.com/Rail.svc/json/jPath" # ?FromStationCode=<code1> &ToStationCode=<code2>

LINES_TOP = "Lines"
LINES_DISPLAY_NAME = "DisplayName"
LINES_START_CODE = "StartStationCode"
LINES_END_CODE = "EndStationCode"
LINES_LINE_CODE = "LineCode"

STATION_LIST_TOP = "Stations"
STATION_LIST_NAME = "Name"
STATION_LIST_CODE = "Code"
STATION_LIST_LC1 = "LineCode1"
STATION_LIST_LC2 = "LineCode2"
STATION_LIST_LC3 = "LineCode3"
STATION_LIST_LC4 = "LineCode4"
STATION_LIST_ST1 = "StationTogether1"
STATION_LIST_ST2 = "StationTogether2"

STATION_STATION_TOP = "StationToStationInfos"
STATION_STATION_MILES = "CompositeMiles"
STATION_STATION_TIME = "RailTime"
STATION_STATION_SOURCE = "SourceStation"

STATION_PATH_TOP = "Path"
STATION_PATH_CODE = "StationCode"
