import sys, getopt, requests, json
import MetroConstants as Constants
from MetroInterface import MetroInterface
from MetroData import Line, Station
from time import sleep

_DEBUG = True

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

    if not lineInfos:
        lineInfos = MetroAPI.getLineInfos()

        if _DEBUG:
            for line in lineInfos:
                print(lineInfos[line])

    if not stationInfos:
        stationInfos = MetroAPI.getStationInfos()

        if _DEBUG:
            for key in stationInfos:
                print("Key: " + key + ", Station: " + str(stationInfos[key]))

        for line in lineInfos:
            lineInfos[line].mph = MetroAPI.getLineAvgSpeed(line, lineInfos[line].startStationCode, lineInfos[line].endStationCode)
            
            if _DEBUG: print("Speed (" + line +") " + str(lineInfos[line].mph))

    stationDistances = MetroAPI.getDistancesToGoal(destCode)
    for station in stationDistances:
        stationInfos[station].distance = stationDistances[station]
        if _DEBUG: print("Distance (" + station + "): " + str(stationInfos[station].distance))

    sleep(1)
    for line in lineInfos:
        orderedList = MetroAPI.getOrderedStationList(line, lineInfos[line].startStationCode, lineInfos[line].endStationCode)
        lineInfos[line].stations = orderedList

        if _DEBUG: print("Ordered Line (" + line + ") " + str(orderedList))

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

    if _DEBUG:
        for key in metroGraph:
            print ("Station: " + key + ", Neighbors: " + str(metroGraph[key]))

def costToReachStation(startStation, endStation):
    minDist = 100
    minLine = ""

    sharedLines = set(startStation.lineList).intersection(set(endStation.lineList))

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
        if dist < minDist:
            minDist = dist
            minLine = line
    if _DEBUG: print("Min Dist between " + startStation.name + " and " + endStation.name + ": " + str(minDist) + " (" + minLine + ")")
    return minDist

def calculateFn(startStation, endStation):
#    if "Gallery" in endStation.name:
#        return 100
    fn = costToReachStation(startStation, endStation) + endStation.distance
    return fn

def checkShouldTakeDirectLine(queryStation, lineCode):
    stationList = lineInfos[lineCode].stations
    queryIndex = -1
    for code in queryStation.codeList:
        if code in stationList:
            queryIndex = stationList.index(code)
    if queryIndex == -1:
        return False

    if queryIndex == 0:
        return queryStation.distance >= stationInfos[stationList[queryIndex+1]].distance
    elif queryIndex == len(stationList)-1:
        return queryStation.distance >= stationInfos[stationList[queryIndex-1]].distance
    else:
        return queryStation.distance > stationInfos[stationList[queryIndex-1]].distance \
                or queryStation.distance > stationInfos[stationList[queryIndex+1]].distance
    pass


def findShortestPath(startCode, destCode):
    buildMetroGraph(destCode)

    currentStation = stationInfos[startCode]
    availableLines = currentStation.lineList[:]
    fringe = []
    
    for line in availableLines:
        if _DEBUG: print(lineInfos[line].stations)
        fringe += [ x for x in [stationInfos[y] for y in lineInfos[line].stations] \
                if x not in fringe and not set(x.lineList).issubset(set(availableLines))] 
        
    if _DEBUG: print("Initial fringe: " + str(fringe))
    for station in fringe:
        station.fn = 0 + calculateFn(currentStation, station)
        station.parent = currentStation
        if _DEBUG: print("F(" + station.name + "): " + str(station.fn))

    # While not empty
#    while not len(fringe):
    for i in range(0,5):
        if _DEBUG: print("Available lines: " + str(availableLines))

        for line in availableLines:
            if destCode in lineInfos[line].stations:
                if _DEBUG: print("On the " + line + " line")
                if not checkShouldTakeDirectLine(currentStation, line):
                    if _DEBUG: 
                        print("But it should not be taken...")
                else:
                    return currentStation
#        closestStation = min(fringe, key=lambda station: \
#                costToReachStation(currentStation, station) + station.distance)
        closestStation = min(fringe, key=lambda station: station.fn)
        if _DEBUG: print("Current closest station: " + str(closestStation))

        newLines = set(closestStation.lineList).difference(set(availableLines))
        availableLines += newLines
#        costToReachStation(currentStation, closestStation)

        costSoFar = closestStation.fn - closestStation.distance
        if _DEBUG: print("Cost so far: " + str(costSoFar))

        for line in newLines:
            if _DEBUG: print("New line to consider: " + line)
            
            newNodes = [ x for x in [stationInfos[y] for y in lineInfos[line].stations] \
                    if x not in fringe and not set(x.lineList).issubset(set(availableLines))] 

            for station in newNodes:
                station.fn = costSoFar + calculateFn(closestStation, station)
                if _DEBUG: print("F(" + station.name + "): " + str(station.fn))
                station.parent = closestStation
            fringe += newNodes

        currentStation = closestStation
        fringe.remove(closestStation)
        if _DEBUG: print("Update fringe: " + str(fringe))

    

assert sys.argv[1:]
apiKey = parseApiKey(sys.argv[1:])
startCode = input("Enter starting station code (or exit): ")
assert startCode

if "exit" in startCode:
    exit()

destCode = input("Enter destination station code: ")
assert destCode

while True:
    MetroAPI = MetroInterface(apiKey)

    if " " in startCode or " " in destCode:
        print("Using defaults: Foggy Bottom (CO4) -> Columbia Heights (E04)")
        startCode = "C04"
        destCode = "E04"
    finalStop = findShortestPath(startCode, destCode) # Foggy Bottom to Columbia Heights

    pathStack = [stationInfos[destCode].name]
    while not stationInfos[startCode].name in finalStop.name:
        pathStack.append(finalStop.name)
        finalStop = finalStop.parent
    pathStack.append(stationInfos[startCode].name)
    pathStack.reverse()

    print("---------------------------------------------------")
    print("Path:")
    for station in pathStack:
        print(station)
    print("---------------------------------------------------")
    
    startCode = input("Enter starting station code (or exit): ")
    assert startCode

    if "exit" in startCode:
        exit()

    destCode = input("Enter destination station code: ")
    assert destCode
