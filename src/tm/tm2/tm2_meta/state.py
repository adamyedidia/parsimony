import string
import re

# removes all entries equal to x from list l
def removeAll(l, x):
	while True:
		try:
			l.remove(x)
		except:
			return l

class SimpleState:
	def __init__(self, stateName, alphabet=["_", "1", "H", "E"]):
		self.stateName = stateName
		self.nextStateDict = {}
		self.headMoveDict = {}
		self.writeDict = {}

		if alphabet == None:
			self.alphabet = ["_", "1", "H", "E"]
		else:
			self.alphabet = alphabet

		for symbol in self.alphabet:
			self.nextStateDict[symbol] = self
			self.headMoveDict[symbol] = "-"
			self.writeDict[symbol] = symbol

		self.isStartState = False

	def isState(self):
		return True

	def isSimpleState(self):
		return True

# a group of states associated with writing a function
class FunctionGroup:
	def __init__(self, functionName, functionLines, functionVariableDictionary, 
		functionLabelDictionary, functionDictionary, convertNumberToBarCode, listOfStates,
		inState=None, firstFunction=False):
		
		name = "write_code_" + functionName
		
		if inState == None:
			self.inState = State(name + "_underscore_1")
		else:
			self.inState = inState
		funcName_State2 = State(name + "_underscore_2")
		funcName_State3 = State(name + "_underscore_3")
		
		if firstFunction:
			self.inState.set3("_", funcName_State2, "R", "H")
			self.charString = "H"
		else:
			self.inState.set3("_", funcName_State2, "R", "_")
			self.charString = "_"
			
		funcName_State2.set3("_", funcName_State3, "R", "H")

		# I think the bar code is always E, and we come back and increment it later...
		functionBarCode = "E"
		
		self.charString += "HH" + functionBarCode
		
		listOfBarCodeStates = []
		
		for i, char in enumerate(functionBarCode):
			listOfBarCodeStates.append(State(name + "_" + str(i)))
		
		funcName_State3.set3("_", listOfBarCodeStates[0], "R", "H")	
			
		for state in listOfBarCodeStates[:-1]:
			state.set3("_", listOfBarCodeStates[i+1], "R", functionBarCode[i])
		
		listOfLineGroups = []
		
		lineNumber = 1
		
		hadFirstLine = False
		for line in functionLines:
			if not (line == "\n" or line[0:2] == "//" or line[0:5] == "input"):
				if not hadFirstLine:
					listOfLineGroups.append(LineGroup(line, functionName, lineNumber, \
						functionVariableDictionary, functionLabelDictionary, functionDictionary, \
						convertNumberToBarCode, listOfStates, True))
					hadFirstLine = True
				
				else:
					listOfLineGroups.append(LineGroup(line, functionName, lineNumber, \
						functionVariableDictionary, functionLabelDictionary, functionDictionary, \
						convertNumberToBarCode, listOfStates))
			
			lineNumber += 1

		listOfBarCodeStates[-1].set3("_", listOfLineGroups[0].inState, "R", functionBarCode[-1])
		
		for i, lineGroup in enumerate(listOfLineGroups[:-1]):
			lineGroup.attach(listOfLineGroups[i+1])
			self.charString += lineGroup.charString
			
		self.charString += listOfLineGroups[-1].charString
			
		self.outState = listOfLineGroups[-1].outState
		
		listOfStates.extend([self.inState, funcName_State2, funcName_State3])
		listOfStates.extend(listOfBarCodeStates)
			
	def attach(self, otherFunctionGroup):
		self.outState.setNextState("_", otherFunctionGroup.inState)

# a group of states associated with writing a line of code
class LineGroup:
	def __init__(self, lineString, functionName, lineNumber, functionVariableDictionary, \
		functionLabelDictionary, functionDictionary, convertNumberToBarCode, listOfStates, 
		isFirstLine=False):
		
		name = "write_code_" + functionName + "_" + str(lineNumber)
		
		self.inState = State(name + "_underscore_1")
		
		self.charString = ""
		
		if not isFirstLine:
			lineNumber_State2 = State(name + "_ln_underscore_2")
			self.charString += "_"
			
		lineNumberHState = State(name + "ln_H")
		
		if isFirstLine:
			self.inState.set3("_", lineNumberHState, "R", "_")
		
		if not isFirstLine:				
			self.inState.set3("_", lineNumber_State2, "R", "_")
			lineNumber_State2.set3("_", lineNumberHState, "R", "_")
			listOfStates.append(lineNumber_State2)

		listOfStates.extend([self.inState, lineNumberHState])
		
		self.charString += "_H"
		
		if "[" in lineString:
			# then it must be a direct tape command
			
			splitLine = re.split("[\[|\]]", lineString)
			
			variableName = splitLine[1]
			reactions = string.split(splitLine[2], ";")
			
			listOfReactionGroups = []
			
			for reaction in reactions:
				listOfReactionGroups.append(ReactionGroup(reaction, functionName, \
					lineNumber, convertNumberToBarCode, functionLabelDictionary, listOfStates))
		
			variableBarCode = convertNumberToBarCode( \
			functionVariableDictionary[functionName][variableName])
			
			varName1State = State(name + "_varname_preamble_1")
			
			self.charString += "1" + variableBarCode
			
			lineNumberHState.set3("_", varName1State, "R", "H")
			
			listOfBarCodeStates = [State(name + "_varname_" + str(i)) for i in \
				range(len(variableBarCode))]
			
			assert len(variableBarCode) > 0
				
			varName1State.set3("_", listOfBarCodeStates[0], "R", "1")
			
			for i, state in enumerate(listOfBarCodeStates[:-1]):
				state.set3("_", listOfBarCodeStates[i+1], "R", variableBarCode[i])

			listOfBarCodeStates[-1].set3("_", listOfReactionGroups[0].inState, \
				"R", variableBarCode[-1])
				
			for i, reactionGroup in enumerate(listOfReactionGroups[:-1]):
				reactionGroup.attach(listOfReactionGroups[i+1])
				self.charString += reactionGroup.charString
			
			self.charString += listOfReactionGroups[-1].charString	
				
			self.outState = listOfReactionGroups[-1].outState
			
			listOfStates.extend([varName1State])
			listOfStates.extend(listOfBarCodeStates)
		
		elif "function" in lineString:
#			if ":" in lineString:
#				everythingButLabel = string.split(lineString, ":")[1]
#			else:
#				everythingButLabel = lineString

			everythingButLabel = string.split(lineString, ":")[-1]
			
			splitLine = string.split(everythingButLabel)
			
			listOfVarGroups = []
			
			for variableName in splitLine[2:]:
				listOfVarGroups.append(VarGroup(variableName, functionName, lineNumber, \
					convertNumberToBarCode, functionVariableDictionary, listOfStates))
			
			funcNameEState = State(name + "_funcname_preamble_E")
			
			lineNumberHState.set3("_", funcNameEState, "R", "H")
			            
			functionBarCode = convertNumberToBarCode(functionDictionary[splitLine[1]])
			
			self.charString += "E" + functionBarCode
			
			listOfBarCodeStates = []
			
			for i, char in enumerate(functionBarCode):
				listOfBarCodeStates.append(State(name + "_funcname_" + str(i)))
				
			funcNameEState.set3("_", listOfBarCodeStates[0], "R", "E")
				
			for i, state in enumerate(listOfBarCodeStates[:-1]):
				state.set3("_", listOfBarCodeStates[i+1], "R", functionBarCode[i])
				
			listOfBarCodeStates[-1].set3("_", listOfVarGroups[0].inState, "R", functionBarCode[-1])
			
			for i, varGroup in enumerate(listOfVarGroups[:-1]):
				varGroup.attach(listOfVarGroups[i+1])	
				self.charString += varGroup.charString
			
			self.charString += listOfVarGroups[-1].charString
			
			self.outState = listOfVarGroups[-1].outState
			
			listOfStates.extend([funcNameEState])
			listOfStates.extend(listOfBarCodeStates)
			
		elif "return" in lineString:
			lineNumberHState.setHeadMove("_", "R")
			lineNumberHState.setWrite("_", "H")
			
			self.outState = lineNumberHState
		
		else:
			"Line", str(lineNumber), "is incomprehensible:", lineString
			raise 
			
	def attach(self, otherLineGroup):
		self.outState.setNextState("_", otherLineGroup.inState)
		
class ReactionGroup:
	
	def __init__(self, reactionString, functionName, lineNumber, convertNumberToBarCode, \
		functionLabelDictionary, listOfStates):
		
		splitReaction = removeAll(re.split("[ |(|,|)]", reactionString.strip()), "")
				
		symbolRead = splitReaction[0]
		name = "write_code_" + functionName + "_" + str(lineNumber) + "_" + symbolRead
	
		write = symbolRead
		headMove = "-"
		nextLine = None
	
		for x in splitReaction[1:]:
			if x in ["_", "1", "E"]:
				write = x
			elif x in ["-", "L", "R"]:
				headMove = x
			else:
				nextLine = x
	
		headMoveToSymbol = {"L": "1", "R": "E", "-": "_"}
		
		self.inState = State(name + "_underscore")
		oneState = State(name + "_one")
		readState = State(name + "_read")
		writeState = State(name + "_write")
		headMoveState = State(name + "_headmove")
		
		self.inState.set3("_", oneState, "R", "_")
		oneState.set3("_", readState, "R", "1")
		readState.set3("_", writeState, "R", symbolRead)
		writeState.set3("_", headMoveState, "R", write)
		
		self.charString = "_1" + symbolRead + write + headMoveToSymbol[headMove]
		
		listOfNextLineStates = []
		
		if nextLine == None:
			lineBarCode = ""
			self.outState = headMoveState
			self.outState.setHeadMove("_", "R")
			self.outState.setWrite("_", headMoveToSymbol[headMove])
			
		else:
			lineBarCode = convertNumberToBarCode(functionLabelDictionary[functionName][nextLine])

			for i, char in enumerate(lineBarCode):
				listOfNextLineStates.append(State(name + "_linenumber_" + str(i)))
				self.charString += char
		
			headMoveState.set3("_", listOfNextLineStates[0], "R", headMoveToSymbol[headMove])	
		
			for i, state in enumerate(listOfNextLineStates[:-1]):
				state.set3("_", listOfNextLineStates[i+1], "R", lineBarCode[i])
						
			self.outState = listOfNextLineStates[-1]				
			self.outState.setHeadMove("_", "R")
			self.outState.setWrite("_", lineBarCode[-1])
		
		listOfStates.extend([self.inState, oneState, readState, writeState, headMoveState])
		listOfStates.extend(listOfNextLineStates)
	
	def attach(self, otherReactionGroup):
		self.outState.setNextState("_", otherReactionGroup.inState)
		
class VarGroup:

	def __init__(self, variableName, functionName, lineNumber, convertNumberToBarCode, 
		functionVariableDictionary, listOfStates):
		
		name = "write_code_" + functionName + "_" + str(lineNumber) + "_" + variableName
		
		self.inState = State(name + "_underscore")
		self.charString = "_"
			        
		variableBarCode = convertNumberToBarCode(functionVariableDictionary[functionName][variableName])

		listOfBarCodeStates = []
		for i, char in enumerate(variableBarCode):
			listOfBarCodeStates.append(State(name + "_name_" + str(i)))
			self.charString += char

		self.inState.set3("_", listOfBarCodeStates[0], "R", "_")
		
		for i, state in enumerate(listOfBarCodeStates[:-1]):
			state.set3("_", listOfBarCodeStates[i+1], "R", variableBarCode[i])
			
		self.outState = listOfBarCodeStates[-1]
		self.outState.setHeadMove("_", "R")
		self.outState.setWrite("_", variableBarCode[-1])
		
		listOfStates.append(self.inState)
		listOfStates.extend(listOfBarCodeStates)

	def attach(self, otherReactionGroup):
		self.outState.setNextState("_", otherReactionGroup.inState)

class State(object):
	def __init__(self, stateName, description="", alphabet=["_", "1", "H", "E"]):
	
		self.stateName = stateName
		self.nextStateDict = {}
		self.headMoveDict = {}
		self.writeDict = {}
		self.description = description

		if alphabet == None:
			self.alphabet = ["_", "1", "H", "E"]
		else:
			self.alphabet = alphabet

		errorState = SimpleState("ERROR", self.alphabet)

		for symbol in self.alphabet:
			self.nextStateDict[symbol] = errorState
			self.headMoveDict[symbol] = "-"
			self.writeDict[symbol] = symbol

		self.isStartState = False
	
	def __eq__(self, other):
		if not isinstance(other, self.__class__):
			return False
		
		for i, symbol in enumerate(self.alphabet):
			if other.alphabet[i] != symbol:
				return False

		for symbol in self.alphabet:
			if self.nextStateDict[symbol].stateName != other.nextStateDict[symbol].stateName:
				return False
			
			if self.headMoveDict[symbol] != other.headMoveDict[symbol]:
				return False

			if self.writeDict[symbol] != other.writeDict[symbol]:
				return False

		return True

	def __ne__(self, other):
		return not self.__eq__(other)

	def infoHash(self):
		returnString = ""
		
		for symbol in self.alphabet:
			returnString += symbol + ":" + self.nextStateDict[symbol].stateName + ";" + \
					self.headMoveDict[symbol] + self.writeDict[symbol]

		return returnString

	def setNextState(self, symbol, nextState):
		assert symbol in self.alphabet
		assert nextState.isState()
		self.nextStateDict[symbol] = nextState
			
	def setHeadMove(self, symbol, headMove):
		assert symbol in self.alphabet
		try:
			assert headMove in ["L", "R", "-"]
		except:
			print "Unacceptable! headMove was", headMove
			raise
		self.headMoveDict[symbol] = headMove
			
	def setWrite(self, symbol, write):
		assert symbol in self.alphabet
		assert write in self.alphabet
		self.writeDict[symbol] = write

	def set3(self, symbol, nextState, headMove, write):
		self.setNextState(symbol, nextState)
		self.setHeadMove(symbol, headMove)
		self.setWrite(symbol, write)

	def setAllNextStates(self, nextState):
		assert nextState.isState()
		for symbol in self.alphabet:
			self.nextStateDict[symbol] = nextState

	def setAllHeadMoves(self, headMove):
		try:
			assert headMove in ["L", "R", "-"]
		except:
			print "Unacceptable! Headmove was", headMove
			raise
            
		for symbol in self.alphabet:
			self.headMoveDict[symbol] = headMove

	def setAllWrites(self, write):
		assert write in self.alphabet
		for symbol in self.alphabet:
			self.writeDict[symbol] = write

	def setAll3(self, nextState, headMove, write):
		self.setAllNextStates(nextState)
		self.setAllHeadMoves(headMove)
		self.setAllWrites(write)

	def getNextState(self, symbol):
		return self.nextStateDict[symbol]

	def getNextStateName(self, symbol):
		try:
			return self.nextStateDict[symbol].stateName
		except KeyError:
			print "Error: I, state", self.stateName, "don't know about symbol", symbol
			print "My alphabet is", self.alphabet
			raise

	def getHeadMove(self, symbol):
		return self.headMoveDict[symbol]

	def getWrite(self, symbol):
		try:
			return self.writeDict[symbol]		
		except KeyError:
			print "Error: I, state", self.stateName, "don't know about symbol", symbol
			print "My alphabet is", self.alphabet
			raise
	
	def isState(self):
		return True

	def isSimpleState(self):
		return False

	def makeStartState(self):
		self.isStartState = True
