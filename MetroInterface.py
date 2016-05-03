import requests, json
import MetroConstants as Constants
from MetroData import Line,Station
from time import sleep

class MetroInterface:
    """
    Abstracts the process of hitting the API and parsing JSON responses.

    For more info, see the Rail Station Information API at:
    https://developer.wmata.com/docs/services/

    Args:
        apiKey (str): WMATA API key.
    """
    def __init__(self, apiKey):
        self.apiKey = apiKey

    def getLineInfos(self):
        """
        Queries the Lines API for the list of Metro lines.

        Returns:
            List of MetroData.Line for each line parsed.
        """
        jsonResp = json.loads(requests.get(Constants.URL_LINES_LIST + "?api_key=" +self.apiKey).text)
        lineInfos = {}
        for i in jsonResp[Constants.LINES_TOP]:
            displayName = i[Constants.LINES_DISPLAY_NAME]
            lineCode = i[Constants.LINES_LINE_CODE]
            startCode = i[Constants.LINES_START_CODE]
            endCode = i[Constants.LINES_END_CODE]
            lineInfos[lineCode] = Line(displayName, lineCode, startCode, endCode)
        return lineInfos

    def getStationInfos(self):
        """
        Queries the Stations API for each station on the Metro.

        Returns:
            A dictionary which can be indexed by station name or code (keys) and yields MetroData.Station objects (value).
        """
        jsonResp = json.loads(requests.get(Constants.URL_STATION_LIST + "?api_key=" +self.apiKey).text)
        stationInfos = {}
        for i in jsonResp[Constants.STATION_LIST_TOP]:
            name = i[Constants.STATION_LIST_NAME]
            code = i[Constants.STATION_LIST_CODE]
            lc1 = i[Constants.STATION_LIST_LC1]
            lc2 = i[Constants.STATION_LIST_LC2]
            lc3 = i[Constants.STATION_LIST_LC3]
            lc4 = i[Constants.STATION_LIST_LC4]
            st1 = i[Constants.STATION_LIST_ST1]
            st2 = i[Constants.STATION_LIST_ST2]

            if name not in stationInfos:
                station = Station(name, code, lc1, lc2, lc3, lc4, st1, st2)
                # Want the station information to be indexed by name or station code
                stationInfos[name] = station
                stationInfos[code] = station

                for st in [st1, st2]:
                    if st:
                        stationInfos[st] = station
            else:
                # Add any new lines / codes to the existing Station object
                station = stationInfos[name]
                for newLine in [lc1, lc2, lc3, lc4]:
                    if newLine:
                        station.addLine(newLine)
                for newCode in [st1, st2, code]:
                    if newCode:
                        station.addStation(newCode)
                        if newCode not in stationInfos:
                            stationInfos[newCode] = station
        return stationInfos


    def getLineAvgSpeed(self, lineCode, startCode, endCode):
        """
        Determines the approximate speed of trains on a given line, between two stations.

        Querying with the absolute start and end stations of the line yields the approximate
        speed across the whole line.

        Args:
            lineCode (str): Two-letter abbreviation for a line.
            startCode (str): Start station code of the line.
            endCode (str): End station code of the line.

        Returns:
            Approximate speed in MPH (float)
        """
        jsonResp = json.loads(requests.get(Constants.URL_STATION_STATION_INFO+ "?FromStationCode=" + startCode + "&ToStationCode=" + endCode + "&api_key=" +self.apiKey).text)
       
        info = jsonResp[Constants.STATION_STATION_TOP][0]
        totalMiles = info[Constants.STATION_STATION_MILES]
        time = info[Constants.STATION_STATION_TIME]
        return totalMiles * 60 / time


    def getOrderedStationList(self, lineCode, startCode, endCode):
        """
        Determines the stations, in order, for a given line.

        Args:
            lineCode (str): Two-letter abbreviation for a line.
            startCode (str): Start station code of the line.
            endCode (str): End station code of the line.

        Returns:
            List of station codes (str) sorted in order of sequence along the line.
        """
        jsonResp = json.loads(requests.get(Constants.URL_STATION_PATH + "?FromStationCode=" + startCode + "&ToStationCode=" + endCode + "&api_key=" +self.apiKey).text)

        orderedStations = []
        for i in jsonResp[Constants.STATION_PATH_TOP]:
            orderedStations.append(i[Constants.STATION_PATH_CODE])

        return orderedStations


    def getDistancesToGoal(self, destCode):
        """
        Queries the approximate distance (by track) of every station to the supplied destination station.

        Args:
            destCode (str): Destination station code.

        Returns:
            A dictionary of station codes to approximate distances (in miles).
        """
        jsonResp = json.loads(requests.get(Constants.URL_STATION_STATION_INFO + "?ToStationCode=" + destCode + "&api_key=" +self.apiKey).text)
        stationDists = {}

        for i in jsonResp[Constants.STATION_STATION_TOP]:
            sourceStation = i[Constants.STATION_STATION_SOURCE]
            stationDists[sourceStation] = i[Constants.STATION_STATION_MILES]
        stationDists[destCode] = 0
        return stationDists

