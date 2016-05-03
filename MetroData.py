class Line:
    """
    Represents a Metro line - name, line code / abbreviation, starting & ending stations.
    
    For more information see the Lines API under Rail Station Information:
    https://developer.wmata.com/docs/services/

    Args:
        displayName (str): Full name of line color.
        lineCode (str): Two-letter abbreviation for the line.
        startStationCode (str): Station code of one end of the line.
        endStationCOde (str): Station code for the other end of the lin.
    """

    def __init__(self, displayName, lineCode, startStationCode, endStationCode):
        self.displayName = displayName
        self.lineCode = lineCode
        self.startStationCode = startStationCode
        self.endStationCode = endStationCode

    def __str__(self):
        return "Display Name: " + self.displayName + \
        " Line Code: " + self.lineCode + \
        " Start Station: " + self.startStationCode + \
        " End Station: " + self.endStationCode

class Station:
    """
    Represents a Metro station: name, code, lines, and alternate station codes.
    
    For more information see the Station API under Rail Station Information:
    https://developer.wmata.com/docs/services/

    Args:
        name (str): Full name of the station.
        code (str): Primary station code.
        lineCode1 (str): Two-letter line code for a line served by this station.
        lineCode2 (str): Same as previous, may be None.
        lineCode3 (str): Same as previous, may be None.
        lineCode4 (str): Same as previous, may be None.
        stationTogether1: Alternate station code (for multiple platforms), may be None.
        stationTogether2: Same as previous, may be None.
    """

    def __init__(self, name, code, lineCode1, lineCode2, lineCode3, lineCode4, stationTogether1, stationTogether2):
        self.name = name

        self.lineList = [lineCode1]
        for i in [lineCode2, lineCode3, lineCode4]:
            if i:
                self.lineList.append(i)

        self.codeList = [code]
        for i in [stationTogether1, stationTogether2]:
            if i:
                self.codeList.append(i)

        self.distance = None

    def __str__(self):
        return self.name + " | " + str(self.codeList) + " | " + str(self.lineList)

    def __repr__(self):
        return str(self)

    def addStation(self, code):
        if code not in self.codeList:
            self.codeList.append(code)

    def addLine(self, line):
        if line not in self.lineList:
            self.lineList.append(line)
