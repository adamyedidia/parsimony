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

class SingleTapeTuringMachine:
    def __init__(self, path, alphabet=["_", "1", "H", "E"]):        
        self.state = None
        self.tape = Tape(None, alphabet[0])

        listOfSymbols = alphabet

        inp = open(path, "r")
        tmLines = inp.readlines()

        self.stateDictionary = {"ACCEPT": SimpleState("ACCEPT", alphabet),
            "REJECT": SimpleState("REJECT", alphabet),
            "ERROR": SimpleState("ERROR", alphabet),
            "HALT": SimpleState("HALT", alphabet),
            "OUT": SimpleState("OUT", alphabet)}

        self.listOfRealStates = []

        # initialize state dictionary
        for line in tmLines[1:]:
            if line != "\n": # not a blank line
                lineSplit = string.split(line)
                                
                if lineSplit[0] == "START":
                    stateName = getStateName(line[6:])
                    self.startState = State(stateName, None, alphabet)
                    self.stateDictionary[stateName] = self.startState
                    self.listOfRealStates.append(self.stateDictionary[stateName])
                    self.startState.makeStartState()
                                
                elif not lineSplit[0] in listOfSymbols:
                    stateName = getStateName(line)
                    self.stateDictionary[stateName] = State(stateName, None, alphabet)
                    self.listOfRealStates.append(self.stateDictionary[stateName])
                
        currentStateBeingModified = None

        # fill in state dictionary
        for line in tmLines[1:]:
            if line != "\n":
                lineSplit = string.split(line)
            
                if lineSplit[0] == "START":
                    stateName = getStateName(line[6:])
                    currentStateBeingModified = self.stateDictionary[stateName]
                
                elif not lineSplit[0] in listOfSymbols:
                    stateName = getStateName(line)
                    currentStateBeingModified = self.stateDictionary[stateName]    

                else:
                    symbol = lineSplit[0]
                    stateName = lineSplit[2][:-1]
                    headMove = lineSplit[3][:-1]
                    write = lineSplit[4]                    

                    currentStateBeingModified.setNextState(symbol, 
                        self.stateDictionary[stateName])
                    currentStateBeingModified.setHeadMove(symbol, headMove)
                    currentStateBeingModified.setWrite(symbol, write)

    def run(self, quiet=False, numSteps=float("Inf"), output=None):
        
        self.state = self.startState

        stepCounter = 0
        halted = False
        numSteps = float(numSteps)

        while stepCounter < numSteps:
            if not quiet:
                self.printTape(-2, 340, output)
            
            stepCounter += 1

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
            self.tape.moveHead(self.state.getHeadMove(symbol))  
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

class Tape(object):
    # By convention the first symbol in the alphabet is the initial symbol
    def __init__(self, name, initSymbol):
        self.name = name
        self.headLoc = 0
        self.tapeDict = {0: initSymbol}
        self.initSymbol = initSymbol

    def readSymbol(self):
        return self.tapeDict[self.headLoc]

    def writeSymbol(self, symbol):
        self.tapeDict[self.headLoc] = symbol

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
        if not self.headLoc in self.tapeDict:
            self.tapeDict[self.headLoc] = self.initSymbol

    def printTape(self, start, end, output=None):
        headString = ""
        tapeString = ""
        for i in range(start, end):
            
            if i == self.headLoc:
                headString += "v"
            else:
                headString += " "

            if i in self.tapeDict:
                tapeString += self.tapeDict[i][0]
            else:
                tapeString += self.initSymbol
        
        if not self.name == None:
            tapeString += " " + self.name

        if output == None:
            print headString
            print tapeString
        else:       
            output.write(headString + "\n")
            output.write(tapeString + "\n")

    def getTapeOutput(self, start, end):
        headString = ""
        tapeString = ""
        for i in range(start, end):
            
            if i == self.headLoc:
                headString += "v"
            else:
                headString += " "

            if i in self.tapeDict:
                tapeString += self.tapeDict[i][0]
            else:
                tapeString += self.initSymbol
        
        if not self.name == None:
            tapeString += " " + self.name
        
        return headString + "\n" + tapeString + "\n"
