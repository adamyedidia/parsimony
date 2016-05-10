import string
import sys

from state import *

def getStateName(line):
    colonLoc = string.find(line, ":")
    
    stateName = line[:colonLoc]

    return stateName    

if __name__ == "__main__":
    sttm = SingleTapeTuringMachine(sys.argv[-1], ["_", "1", "H", "E"])
    args = sys.argv[1:-1]

    quiet = ("-q" in args)

    numSteps = float("Inf") # default value
    if ("-s" in args):
        numSteps = args[args.index("-s") + 1]

    output = None
    if ("-f" in args):
        output = open(args[args.index("-f") + 1], "w")

    sttm.run(quiet, numSteps, output)


def parseMachine(path, alphabet):
    with open(path, "r") as inp:
        tmLines = inp.readlines()

    stateDictionary = {"ACCEPT": SimpleState("ACCEPT", alphabet),
        "REJECT": SimpleState("REJECT", alphabet),
        "ERROR": SimpleState("ERROR", alphabet),
        "HALT": SimpleState("HALT", alphabet),
        "OUT": SimpleState("OUT", alphabet)}

    listOfRealStates = []

    # initialize state dictionary
    for line in tmLines[1:]:
        if line != "\n": # not a blank line
            lineSplit = string.split(line)

            if lineSplit[0] == "START":
                stateName = getStateName(line[6:])
                startState = State(stateName, None, alphabet)
                stateDictionary[stateName] = startState
                listOfRealStates.append(stateDictionary[stateName])
                startState.makeStartState()

            elif not lineSplit[0] in alphabet:
                stateName = getStateName(line)
                stateDictionary[stateName] = State(stateName, None, alphabet)
                listOfRealStates.append(stateDictionary[stateName])

    currentStateBeingModified = None

    # fill in state dictionary
    for line in tmLines[1:]:
        if line != "\n":
            lineSplit = string.split(line)

            if lineSplit[0] == "START":
                stateName = getStateName(line[6:])
                currentStateBeingModified = stateDictionary[stateName]

            elif not lineSplit[0] in alphabet:
                stateName = getStateName(line)
                currentStateBeingModified = stateDictionary[stateName]

            else:
                symbol = lineSplit[0]
                stateName = lineSplit[2][:-1]
                headMove = lineSplit[3][:-1]
                write = lineSplit[4]

                currentStateBeingModified.setNextState(symbol,
                    stateDictionary[stateName])
                currentStateBeingModified.setHeadMove(symbol, headMove)
                currentStateBeingModified.setWrite(symbol, write)

    return startState, stateDictionary

def stateDictionariesToLists(stateDictionary, alphabet, startState):
    simulationStates = {}
    for state in stateDictionary.itervalues():
        if state.isSimpleState():
            newState = state
        else:
            newState = SimulationState()
        simulationStates[state] = newState
    for state in stateDictionary.itervalues():
        if not state.isSimpleState():
            simulationStates[state]._initFromState(state, simulationStates)
    return simulationStates[startState]

class SingleTapeTuringMachine:
    def __init__(self, path, alphabet=["_", "1", "H", "E"]):        
        self.state = None
        self.tape = Tape(None, alphabet[0])

        startState, stateDictionary = parseMachine(
                path, alphabet)
        startState = stateDictionariesToLists(
                stateDictionary, alphabet, startState)
        self.startState = startState

    def run(self, quiet=False, numSteps=float("Inf"), output=None):
        
        self.state = self.startState

        stepCounter = 0
        halted = False
        numSteps = float(numSteps)

        while stepCounter < numSteps:
            if not quiet:
                self.printTape(-2, 340, output)
            
            stepCounter += 1

            if self.state.isSimpleState():
                if self.state.stateName == "ERROR":
                    print "Turing machine threw error!"
                    halted = True
                    break

                if self.state.stateName == "ACCEPT":
                    print "Turing machine accepted after", stepCounter, "steps."
                    print len(self.tape.tapeDict), "squares of memory were used."
                    halted = True
                    break

                if self.state.stateName == "REJECT":
                    print "Turing machine rejected after", stepCounter, "steps."
                    print len(self.tape.tapeDict), "squares of memory were used."
                    halted = True
                    break

                if self.state.stateName == "HALT":
                    print "Turing machine halted after", stepCounter, "steps."
                    print len(self.tape.tapeDict), "squares of memory were used."
                    halted = True
                    break

                if self.state.stateName == "OUT":
                    print "Turing machine execution incomplete: reached out state."
                    print "Perhaps this Turing machine wants to be melded with another machine."

            symbol = self.tape.readSymbol()
            headmove = self.state.getHeadMove(symbol)

            self.tape.writeSymbol(self.state.getWrite(symbol))
            self.tape.moveHead(headmove)
            self.state = self.state.getNextState(symbol)

        if not halted:
            print "Turing machine ran for", numSteps, "steps without halting."
    
    def printTape(self, start, end, output):
        if output == None:
        
            print self.state.stateName

            self.tape.printTape(start, end)
#           print "--------------------------------------"
        else:
            output.write(self.state.stateName + "\n")

            self.tape.printTape(start, end, output)
#           output.write("--------------------------------------\n")    


class SimulationState(object):
    def __init__(self):
        self.nextState = [None] * 256
        self.headMove = [""] * 256
        self.write = [""] * 256

    def _initFromState(self, realState, simulationStates):
        self.stateName = realState.stateName
        self.description = realState.description
        self.alphabet = realState.alphabet
        self.isStartState = realState.isStartState
        for symbol in self.alphabet:
            self.headMove[ord(symbol)] = realState.headMoveDict[symbol]
            self.write[ord(symbol)] = realState.writeDict[symbol]
            self.nextState[ord(symbol)] = simulationStates[
                    realState.nextStateDict[symbol]]

    def getNextState(self, symbol):
        return self.nextState[ord(symbol)]

    def getHeadMove(self, symbol):
        return self.headMove[ord(symbol)]

    def getWrite(self, symbol):
        return self.write[ord(symbol)]

    def isSimpleState(self):
        return False

class Tape(object):
    # By convention the first symbol in the alphabet is the initial symbol
    def __init__(self, name, initSymbol):
        self.name = name
        self.headLoc = 0
        self.tapePos = [initSymbol]
        self.tapeNeg = []
        self.initSymbol = initSymbol

    def readSymbol(self):
        return self._readSymbol(self.headLoc)

    def _readSymbol(self, pos):
        try:
            if pos >= 0:
                return self.tapePos[pos]
            else:
                return self.tapeNeg[~pos]
        except IndexError:
            return self.initSymbol

    def writeSymbol(self, symbol):
        if self.headLoc >= 0:
            self.tapePos[self.headLoc] = symbol
        else:
            self.tapeNeg[~self.headLoc] = symbol

    def moveHead(self, direction):
        if direction == "L":
            self.headLoc -= 1
            self.continueTape()

        elif direction == "R":
            self.headLoc += 1
            self.continueTape()

        elif direction == "-":
            pass
        else:
            print "bad head move", headmove
            raise

    def continueTape(self):
        if self.headLoc >= 0:
            assert 0 <= self.headLoc <= len(self.tapePos)
            if self.headLoc == len(self.tapePos):
                self.tapePos.append(self.initSymbol)
        else:
            pos = ~self.headLoc
            assert 0 <= pos <= len(self.tapeNeg)
            if pos == len(self.tapeNeg):
                self.tapeNeg.append(self.initSymbol)

    def printTape(self, start, end, output=None):
        out = self.getTapeOutput(start, end)
        if output == None:
            print out,
        else:
            output.write(out)

    def getTapeOutput(self, start, end):
        headString = []
        tapeString = []
        for i in range(start, end):
            if i == self.headLoc:
                headString .append("v")
            else:
                headString.append(" ")

            tapeString.append(self._readSymbol(i)[0])
        
        if not self.name == None:
            tapeString.append(" " + self.name)
        
        headString = "".join(headString)
        tapeString = "".join(tapeString)
        return headString + "\n" + tapeString + "\n"
