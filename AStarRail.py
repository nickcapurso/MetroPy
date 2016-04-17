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
    global lineInfos, stationInfos, metroGraph
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

def costToReachStation(startStation, endStation):
    minDist = 100
    minLine = ""

    sharedLines = set(startStation.lineList).intersection(set(endStation.lineList))
    #print("Shared lines between " + startStation.name + " and " + endStation.name +": " + str(sharedLines))

    for line in sharedLines:
        stationCodeList = lineInfos[line].stations
        stationList = [x for x in [stationInfos[y] for y in stationCodeList]]

        startIndex = stationList.index(startStation)
        endIndex = stationList.index(endStation)

        if startIndex > endIndex:
            tmp = startIndex
            startIndex = endIndex
            endIndex = tmp

        dist = 0

        for i in range(startIndex, endIndex):
            dist += abs(stationList[i].distance - stationList[i+1].distance)
        #print("CTR: " + endStation.name + " from " + startStation.name + " via " + line + " = " + str(dist))
        if dist < minDist:
            minDist = dist
            minLine = line
    print("Min Dist between " + startStation.name + " and " + endStation.name + ": " + str(minDist) + " (" + minLine + ")")
    return minDist

def calculateFn(startStation, endStation):
    fn = costToReachStation(startStation, endStation) + endStation.distance
    return fn


def findShortestPath(startCode, destCode):
    buildMetroGraph(destCode)

    currentStation = stationInfos[startCode]
    availableLines = currentStation.lineList[:]
    fringe = []
    
    for line in availableLines:
        print(lineInfos[line].stations)
        fringe += [ x for x in [stationInfos[y] for y in lineInfos[line].stations] \
                if x not in fringe and not set(x.lineList).issubset(set(availableLines))] 
        
    print("Initial fringe: " + str(fringe))

    for station in fringe:
        station.fn = 0 + calculateFn(currentStation, station)
        print("F(" + station.name + "): " + str(station.fn))

    # While not empty
#    while not len(fringe):
    for i in range(0,5):
        print("Available lines: " + str(availableLines))
        for line in availableLines:
            if destCode in lineInfos[line].stations:
                print("On the " + line + " line")
                return
#        closestStation = min(fringe, key=lambda station: \
#                costToReachStation(currentStation, station) + station.distance)
        closestStation = min(fringe, key=lambda station: station.fn)
        print("Current closest station: " + str(closestStation))

        newLines = set(closestStation.lineList).difference(set(availableLines))
        availableLines += newLines
#        costToReachStation(currentStation, closestStation)

        costSoFar = closestStation.fn - closestStation.distance
        print("Cost so far: " + str(costSoFar))

        newNodes = []
        for line in newLines:
            print("New line to consider: " + line)
            
            newNodes += [ x for x in [stationInfos[y] for y in lineInfos[line].stations] \
                    if x not in fringe and not set(x.lineList).issubset(set(availableLines))] 

            for station in newNodes:
                station.fn = costSoFar + calculateFn(closestStation, station)
                print("F(" + station.name + "): " + str(station.fn))
            fringe += newNodes

        currentStation = closestStation
        fringe.remove(closestStation)
        print("Update fringe: " + str(fringe))



assert sys.argv[1:]
apiKey = parseApiKey(sys.argv[1:])
"""
destCode = input("Enter destination station code: ")
assert destCode
"""

findShortestPath("C04", "E04") # Foggy Bottom to Columbia Heights
#buildMetroGraph("C07") # Columbia Heights
