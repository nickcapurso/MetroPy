class Line:
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
