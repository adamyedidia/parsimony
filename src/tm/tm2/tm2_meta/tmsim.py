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

class SingleTapeTuringMachine(object):
    def __init__(self, path, alphabet=["_", "1", "H", "E"]):        
        self.tape = Tape(None, alphabet[0])

        startState, stateDictionary = parseMachine(
                path, alphabet)
        startState = stateDictionariesToLists(
                stateDictionary, alphabet, startState)
        self.startState = startState

    def run(self, quiet=False, numSteps=float("Inf"), output=None):
        
        state = self.startState
        tape = self.tape
        ordsymbol = tape.readSymbolOrd()

        stepCounter = 0
        halted = False
        numSteps = int(numSteps)

        while stepCounter < numSteps:
            if not quiet:
                self.printTape(state, -2, 340, output)
            
            stepCounter += 1

            if state.isSimpleState():
                if state.stateName == "ERROR":
                    print "Turing machine threw error!"
                    halted = True
                    break

                if state.stateName == "ACCEPT":
                    print "Turing machine accepted after", stepCounter, "steps."
                    print tape.length(), "squares of memory were used."
                    halted = True
                    break

                if state.stateName == "REJECT":
                    print "Turing machine rejected after", stepCounter, "steps."
                    print tape.length(), "squares of memory were used."
                    halted = True
                    break

                if state.stateName == "HALT":
                    print "Turing machine halted after", stepCounter, "steps."
                    print tape.length(), "squares of memory were used."
                    halted = True
                    break

                if state.stateName == "OUT":
                    print "Turing machine execution incomplete: reached out state."
                    print "Perhaps this Turing machine wants to be melded with another machine."

            state, write, headmove = state.transitionFunc(ordsymbol)
            ordsymbol = tape.writeSymbolMoveAndRead(write, headmove)

        if not halted:
            print "Turing machine ran for", numSteps, "steps without halting."
    
    def printTape(self, state, start, end, output):
        if output == None:
        
            print state.stateName

            self.tape.printTape(start, end)
#           print "--------------------------------------"
        else:
            output.write(state.stateName + "\n")

            self.tape.printTape(start, end, output)
#           output.write("--------------------------------------\n")    


class SimulationState(object):
    def __init__(self):
        self.nextState = [None] * 256
        self.headMove = [0] * 256
        self.write = [0] * 256

    def _initFromState(self, realState, simulationStates):
        self.stateName = realState.stateName
        self.description = realState.description
        self.alphabet = realState.alphabet
        self.isStartState = realState.isStartState
        for symbol in self.alphabet:
            move = realState.headMoveDict[symbol]
            if move == "L":
                move = -1
            elif move == "R":
                move = 1
            elif move == "-":
                move = 0
            else:
                raise ValueError("unknown move %s" % move)
            self.headMove[ord(symbol)] = move
            self.write[ord(symbol)] = ord(realState.writeDict[symbol])
            self.nextState[ord(symbol)] = simulationStates[
                    realState.nextStateDict[symbol]]

    def transitionFunc(self, ordsymbol):
        return (self.nextState[ordsymbol],
                self.write[ordsymbol],
                self.headMove[ordsymbol])

    def getNextState(self, ordsymbol):
        return self.nextState[ordsymbol]

    def getHeadMove(self, ordsymbol):
        return self.headMove[ordsymbol]

    def getWrite(self, ordsymbol):
        return self.write[ordsymbol]

    def isSimpleState(self):
        return False

class Tape(object):
    # By convention the first symbol in the alphabet is the initial symbol
    def __init__(self, name, initSymbol):
        self.name = name
        self.headLoc = 0
        self.initSymbol = initSymbol
        self.initSymbolOrd = ord(initSymbol)
        # initialize tapes with a few initSymbols
        self.tapePos = bytearray(self.initSymbol * 100)
        self.tapeNeg = bytearray(self.initSymbol * 100)

    def length(self):
        return len(self.tapePos) + len(self.tapeNeg)


    def readSymbol(self):
        return self._readSymbol(self.headLoc)

    def readSymbolOrd(self):
        return self._readSymbolOrd(self.headLoc)

    def _readSymbol(self, pos):
        return chr(self._readSymbolOrd(pos))

    def _readSymbolOrd(self, pos):
        try:
            if pos >= 0:
                return self.tapePos[pos]
            else:
                return self.tapeNeg[~pos]
        except IndexError:
            return self.initSymbolOrd

    def writeSymbolOrd(self, ordsymbol):
        if self.headLoc >= 0:
            self.tapePos[self.headLoc] = ordsymbol
        else:
            self.tapeNeg[~self.headLoc] = ordsymbol

    def writeSymbolMoveAndRead(self, ordsymbol, direction):
        # somewhat obsfuscated code for the benefit of CPython
        headLoc = self.headLoc
        tapePos = self.tapePos
        tapeNeg = self.tapeNeg
        initSymbolOrd = self.initSymbolOrd
        # write the symbol
        if headLoc >= 0:
            tapePos[headLoc] = ordsymbol
            if direction == 0:
                return ordsymbol
            headLoc += direction
            self.headLoc = headLoc
            if headLoc == len(tapePos):
                tapePos.append(initSymbolOrd)
                return initSymbolOrd
            if headLoc == -1:
                return tapeNeg[0]
            return tapePos[headLoc]
        else:
            pos = ~headLoc
            tapeNeg[pos] = ordsymbol
            if direction == 0:
                return ordsymbol
            headLoc += direction
            self.headLoc = headLoc
            if headLoc == 0:
                return tapePos[headLoc]
            if ~tapePos == len(tapeNeg):
                tapeNeg.append(initSymbolOrd)
                return initSymbolOrd
            return tapeNeg[pos]

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
                headString.append("v")
            else:
                headString.append(" ")

            tapeString.append(self._readSymbol(i)[0])
        
        if not self.name == None:
            tapeString.append(" " + self.name)
        
        headString = "".join(headString)
        tapeString = "".join(tapeString)
        return headString + "\n" + tapeString + "\n"
