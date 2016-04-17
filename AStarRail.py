import sys, getopt, requests, json
import MetroInterface as MetroAPI
import MetroConstants as Constants
from MetroData import Line, Station
from time import sleep

lineInfos = {}
stationInfos = {}
metroGraph = {}

def parseApiKey(argv):
    try:
        opts,_ = getopt.getopt(argv, "hk:")
    except getopt.GetoptError:
        print ("AStarRail -k <API key>")
        exit()

    # List comprehension yields a list of one element (the tuple with ("-k", <key>))
    apiKey = [v for k, v in enumerate(opts) if v[0] == "-k"][0][1]
    return apiKey

def buildMetroGraph(destCode):
    lineInfos = MetroAPI.getLineInfos(apiKey)

    for line in lineInfos:
        print(lineInfos[line])

    stationInfos = MetroAPI.getStationInfos(apiKey)

    for key in stationInfos:
        print("Key: " + key + ", Station: " + str(stationInfos[key]))

    for line in lineInfos:
        lineInfos[line].mph = MetroAPI.getLineAvgSpeed(apiKey, line, lineInfos[line].startStationCode, lineInfos[line].endStationCode)
        print("Speed (" + line +") " + str(lineInfos[line].mph))

    stationDistances = MetroAPI.getDistancesToGoal(apiKey, destCode)
    for station in stationDistances:
        stationInfos[station].distance = stationDistances[station]
        print("Distance (" + station + "): " + str(stationInfos[station].distance))

    sleep(1)
    for line in lineInfos:
        orderedList = MetroAPI.getOrderedStationList(apiKey, line, lineInfos[line].startStationCode, lineInfos[line].endStationCode)
        lineInfos[line].stations = orderedList
        print("Ordered Line (" + line + ") " + str(orderedList))
        for i in range(0, len(orderedList)):
            assert orderedList[i] in stationInfos
            station = stationInfos[orderedList[i]]

            if station.name not in metroGraph:
                metroGraph[station.name] = []
                if i != len(orderedList) - 1:
                    metroGraph[station.name].append([stationInfos[orderedList[i+1]]])
                if i != 0:
                    metroGraph[station.name].append([stationInfos[orderedList[i-1]]])
            else:
                neighborsList = metroGraph[station.name]

                if i != 0:
                    beforeStation = stationInfos[orderedList[i-1]]
                    if beforeStation not in neighborsList:
                        neighborsList.append(beforeStation)

                if i != len(orderedList) - 1:
                    afterStation = stationInfos[orderedList[i+1]]
                    if afterStation not in neighborsList:
                        neighborsList.append(afterStation)

    for key in metroGraph:
        print ("Station: " + key + ", Neighbors: " + str(metroGraph[key]))

    


assert sys.argv[1:]
apiKey = parseApiKey(sys.argv[1:])
"""
destCode = input("Enter destination station code: ")
assert destCode
"""

buildMetroGraph("C07") # Pentagon
