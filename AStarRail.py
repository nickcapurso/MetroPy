"""
Main algorithm. Prompts for two station codes and uses the A* algorithm
to determine a path between them.
"""
import sys, getopt, requests, json
import MetroConstants as Constants
from MetroInterface import MetroInterface
from MetroData import Line, Station
from time import sleep

# Toggles print statements
_DEBUG = False

lineInfos = {}
stationInfos = {}

# Graph to be represented as a dictionary where the key (station name / code) maps to
# an adjacency list for that station.
metroGraph = {}

def parseApiKey(argv):
    """Returns the API key passed in via the command line."""
    try:
        opts,_ = getopt.getopt(argv, "hk:")
    except getopt.GetoptError:
        print ("AStarRail -k <API key>")
        exit()

    # List comprehension yields a list of one element (the tuple with ("-k", <key>))
    apiKey = [v for k, v in enumerate(opts) if v[0] == "-k"][0][1]
    return apiKey

def buildMetroGraph(destCode):
    """
    Builds a graph (represented with a dictionary) based on the D.C. Metro. 

    Approximate distance information to the desired destination is placed in each "node" and the 
    train speed for each line is also calculated.

    Args:
        destCode (str): Desired destination station code.
    """
    global lineInfos, stationInfos, metroGraph

    # Retrieve Metro lines
    if not lineInfos:
        lineInfos = MetroAPI.getLineInfos()

        if _DEBUG:
            for line in lineInfos:
                print(lineInfos[line])

    # Retrieve Metro stations
    if not stationInfos:
        stationInfos = MetroAPI.getStationInfos()

        if _DEBUG:
            for key in stationInfos:
                print("Key: " + key + ", Station: " + str(stationInfos[key]))

        # For each line, calculate the approximate speed of the trains
        for line in lineInfos:
            lineInfos[line].mph = MetroAPI.getLineAvgSpeed(line, lineInfos[line].startStationCode, lineInfos[line].endStationCode)
            
            if _DEBUG: print("Speed (" + line +") " + str(lineInfos[line].mph))

    # Retrieve station distances to the destination / goal
    stationDistances = MetroAPI.getDistancesToGoal(destCode)
    for station in stationDistances:
        # Include into each Station object
        stationInfos[station].distance = stationDistances[station]
        if _DEBUG: print("Distance (" + station + "): " + str(stationInfos[station].distance))

    # Account for 10 requests / sec. restriction
    sleep(1)

    # For each line, determine the ordered station list, then the neighbors of each station (edges between nodes)
    for line in lineInfos:
        # Retrieve ordered station list and include it in the Line objects.
        orderedList = MetroAPI.getOrderedStationList(line, lineInfos[line].startStationCode, lineInfos[line].endStationCode)
        lineInfos[line].stations = orderedList

        if _DEBUG: print("Ordered Line (" + line + ") " + str(orderedList))

        # For each station on the current line, set the "neighbors" in the graph to be the adjacent stations
        for i in range(0, len(orderedList)):
            assert orderedList[i] in stationInfos
            station = stationInfos[orderedList[i]]

            if station.name not in metroGraph:
                metroGraph[station.name] = []
                if i != len(orderedList) - 1:
                    metroGraph[station.name].append(stationInfos[orderedList[i+1]])
                if i != 0:
                    metroGraph[station.name].append(stationInfos[orderedList[i-1]])
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
    """
    Calculates the g(n) in the A* algorithm.

    Args:
        startStation (MetroData.Station)
        endStation (MetroData.Station)

    Returns:
        The cost (in distance) to reach the end station from the start station.
    """
    minDist = 100
    minLine = ""

    # Want to use set intersection to determine lines in common between the two stations
    sharedLines = set(startStation.lineList).intersection(set(endStation.lineList))

    # Determine the shortest (distance) line to take from the start to the end station
    for line in sharedLines:
        stationCodeList = lineInfos[line].stations

        # For each station code, grab the corresponding MetroData.Station object from stationInfos
        stationList = [x for x in [stationInfos[y] for y in stationCodeList]]

        startIndex = stationList.index(startStation)
        endIndex = stationList.index(endStation)

        # If moving in the opposite direction, swap start and end index (doesn't affect distance).
        if startIndex > endIndex:
            tmp = startIndex
            startIndex = endIndex
            endIndex = tmp

        dist = 0

        # Sum of the differences of distances to destination station
        for i in range(startIndex, endIndex):
            dist += abs(stationList[i].distance - stationList[i+1].distance)
        if dist < minDist:
            minDist = dist
            minLine = line
    if _DEBUG: print("Min Dist between " + startStation.name + " and " + endStation.name + ": " + str(minDist) + " (" + minLine + ")")
    return minDist

def calculateFn(startStation, endStation):
    """
    Calculates f(n) for A*, f(n) = g(n) + h(n).

    g(n) = cost so far (distance)
    h(n) = approximate distance from the nth station to goal. Can later factor in delay times * mph.

    For experimentation, can manually "close" lines or stations by manuall adjusting f(n) values.

    Args:
        startStation (MetroData.Station)
        endStation (MetroData.Station)

    Returns:
        f(endStation)
    """
    fn = costToReachStation(startStation, endStation) + endStation.distance
#    if "Metro Center" in endStation.name:
#        fn = fn - endStation.distance + (20/60) * lineInfos["RD"].mph
#    if "Gallery" in endStation.name or "Plaza" in endStation.name or "Totten" in endStation.name:
#        return 100
    return fn

def checkShouldTakeDirectLine(queryStation, lineCode):
    """
    Determines if the "best" past from a station to the goal is taking the direct line (no transfers).

    This is not true in certain cases -- ex. Federal Center SW and Van Dorn St. share the Blue Line,
    but taking it is not the best path.

    Args:
        queryStation (MetroData.Station) - station in question with a direct line to the destination.
        lineCode (str) - Two-letter abbreviation for the line to check.

    Returns:
        True if taking the <lineCode> line from <queryStation> is the best option, false otherwise.
    """
    stationList = lineInfos[lineCode].stations
    queryIndex = -1

    # The passed station code may not be the one that corresponds to the <lineCode> line.
    # Ex. Metro Center has two codes (for the two platforms), but only one corresponds to the Red Line.
    for code in queryStation.codeList:
        if code in stationList:
            queryIndex = stationList.index(code)
    if queryIndex == -1:
        return False

    # Since station "distances" are distances relative to the end goal, for the direct line path
    # to be best, stations along that path must have a non-increasing distance.
    if queryIndex == 0:
        return queryStation.distance >= stationInfos[stationList[queryIndex+1]].distance
    elif queryIndex == len(stationList)-1:
        return queryStation.distance >= stationInfos[stationList[queryIndex-1]].distance
    else:
        return queryStation.distance > stationInfos[stationList[queryIndex-1]].distance \
                or queryStation.distance > stationInfos[stationList[queryIndex+1]].distance

def findShortestPath(startCode, destCode):
    """
    The core of the algorithm, finds the best path between two stations using the A* algorithm.

    Args:
        startCode (str): Starting station code.
        endCode (str): Destination station code

    Returns:
        The last node to transfer at. Nodes have a "parent" field which can be followed to get the
        full path.
    """

    buildMetroGraph(destCode)

    startStation = stationInfos[startCode]
    destStation = stationInfos[destCode]
    currentStation = stationInfos[startCode]

    # The initial list of available lines
    availableLines = currentStation.lineList[:]
    fringe = []
    
    # Build the initial fringe.
    for line in availableLines:
        if _DEBUG: print(lineInfos[line].stations)

        # Expansion = all nodes reachable by the current station.
        fringe += [ x for x in [stationInfos[y] for y in lineInfos[line].stations] \
                if x not in fringe and x is not startStation and x is not destStation] 
        
    if _DEBUG: print("Initial fringe: " + str(fringe))

    # Set f(n) for each node in the fringe
    for station in fringe:
        station.fn = 0 + calculateFn(currentStation, station)
        station.parent = currentStation
        if _DEBUG: print("F(" + station.name + "): " + str(station.fn))

    # Can be turned into a while loop, currently doing tests to see how many steps the algorithm takes.
    for i in range(0,80):
        if _DEBUG: print("Available lines: " + str(availableLines))

        # Determine if the destination station is directly reachable by one of the available lines
        for line in availableLines:
            if any(code in lineInfos[line].stations for code in destStation.codeList):
                if _DEBUG: print("On the " + line + " line")
                if not checkShouldTakeDirectLine(currentStation, line):
                    if _DEBUG: 
                        print("But it should not be taken...")
                else:
                    return currentStation

        # Determine the next node to expand, based on f(n)
        closestStation = min(fringe, key=lambda station: station.fn)
        if _DEBUG: print("Current closest station: " + str(closestStation))

        # Determine if the next node adds any new lines we can consider
        newLines = set(closestStation.lineList).difference(set(availableLines))
        availableLines += newLines

        # Update the cost so far. The cost to the closest station, g(n)  = f(n) - h(n)
        costSoFar = closestStation.fn - closestStation.distance
        if _DEBUG: print("Cost so far: " + str(costSoFar))

        for line in newLines:
            if _DEBUG: print("New line to consider: " + line)
            
            # Expand the node. Add any newly reachable stations.
            newNodes = [ x for x in [stationInfos[y] for y in lineInfos[line].stations] \
                if x not in fringe and x is not startStation and x is not destStation] 
            #newNodes = [ x for x in [stationInfos[y] for y in lineInfos[line].stations] \
            #        if x not in fringe and not set(x.lineList).issubset(set(availableLines))] 

            # Calculate f(n) for newly reachable stations and add them to the fringe
            for station in newNodes:
                station.fn = costSoFar + calculateFn(closestStation, station)
                if _DEBUG: print("F(" + station.name + "): " + str(station.fn))
                station.parent = closestStation
            fringe += newNodes

        # Update the current station
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
    finalStop = findShortestPath(startCode, destCode) # Foggy Bottom to Columbia Heights is the default

    # The object returned from findShortestPath is the final station to transfer at.
    # It has a "parent" field which can be followed backwards to determine the full path.
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
