import io, re
from array import array
from numbers import Number
from collections import Sequence
from gphoto2 import *

class xray(array):  # simplified array that allows sparseness
	def __new__(cls, typecode= 'f', initObj= ()):
		if typecode=="c" :
			cls= xray_c
		elif typecode=="u" :
			cls= xray_u
		return super(xray, cls).__new__(cls, typecode, initObj)  # calls the array constructor
	def __setitem__(self, index, value):
		sizeDiff= index - self.__len__()
		if sizeDiff > 0 :
			self.extend((0,) * sizeDiff)
			self.append(value)
		elif sizeDiff==0 :
			self.append(value)
		else:
			array.__setitem__(self, index, value)
class xray_c(xray):  # specialized support for an array of ascii characters in python 2
	def __new__(cls, initObj= None):
		super(xray, cls).__new__(cls, 'c', initObj)
	def __setitem__(self, index, value):
		sizeDiff= index - self.__len__()
		if sizeDiff > 0 :
			self.extend((chr(0),) * sizeDiff)
			self.append(value)
		elif sizeDiff==0 :
			self.append(value)
		else:
			array.__setitem__(self, index, value)
try:
	unichr(0)
except:
	unichr= chr
class xray_u(xray):  # specialized support for an array of unicode characters
	def __new__(cls, initObj= ()):
		return super(xray, cls).__new__(cls, 'u', initObj)
	def __setitem__(self, index, value):
		sizeDiff= index - self.__len__()
		if sizeDiff > 0 :
			self.extend((unichr(0),) * sizeDiff)
			self.append(value)
		elif sizeDiff==0 :
			self.append(value)
		else:
			array.__setitem__(self, index, value)

def updateCalibrationData(file_OR_filePath= None):
	stepArray= getCalibrationData(file_OR_filePath, True) # this reads and interpolates the lens calibration data
	stepCount= stepArray.stepCount
	stepCount2= stepArray.stepCount2
	stepCount3= stepArray.stepCount3
	pass # ToDo: finish...

__getIndexReg= re.compile("^\s*(\d+)")
__getStepSizeReg= re.compile("^\s*([a-z]+)\s+steps", re.IGNORECASE)
__getPropertyReg= re.compile("^\s*(\d+)\s*:\s*([\d.]+)\s*(\w+)?\s*$")
def getCalibrationData(file_OR_filePath, interpolateNow= True):
	file= None
	currStepSize= 0
	currStepIndex= 0
	currStepCount= 0
	currStepValue= 0
	currStepUnit= None
	
	stepArray= xray('f') # simplified array that allows sparseness
	stepCounts= array('I', ( 0, 0, 0, 0 ))
	
	if hasattr(file_OR_filePath, "__iter__") and not isinstance(file_OR_filePath, str) :
		file= file_OR_filePath
	else:
		try:
			file= getCalibrationDataFile(file_OR_filePath)
		except:
			pass
	
	if file :
		for line in file :
			if currStepSize==1 :
				propertyMatch= __getPropertyReg.match(line)
			elif currStepSize > 1 :
				propertyMatch= __getIndexReg.match(line)
			else:
				propertyMatch= None
			if propertyMatch :
				currStepIndex= int(propertyMatch.group(1))
				if currStepIndex > currStepCount :
					stepCounts[currStepSize]= currStepCount= currStepIndex
				if currStepSize==1 and currStepIndex : # if stepIndex is 0, it's ignored
					try:
						currStepValue= float(propertyMatch.group(2)) # xfocus always uses centimeters internally
					except:
						print ( "Waring: Ignored invalid calibration data item \""+propertyMatch.group(2)+"\"" )
						continue
					currStepUnit= propertyMatch.group(3)
					if currStepUnit and currStepUnit!="cm" :
						if currStepUnit=="mm" :
							currStepValue/= 10 
						elif currStepUnit=="m" :
							currStepValue*= 100
						elif currStepUnit=="km" :
							currStepValue*= 100000
						else:
							print ( "Warning: Ignored calibration data item with unsupported unit \""+currStepUnit+"\"" )
							continue
					#if currStepValue < 0 : # negative numbers would never match the regular expression
					#	currStepValue= 0
					if currStepValue > 0xFFFF :
						currStepValue= 0xFFFF
					stepArray[currStepIndex-1]= currStepValue
			else:
				stepSizeMatch= __getStepSizeReg.match(line)
				if stepSizeMatch :
					currStepSize= stepSizeMatch.group(1).lower()
					if currStepSize=="large" :
						currStepSize= 3
					elif currStepSize=="medium" :
						currStepSize= 2
					elif currStepSize=="small" :
						currStepSize= 1
					else:
						currStepSize= 0 # invalid step size
					currStepCount= stepCounts[currStepSize]
				
	stepArray.stepCount= stepCounts[1]
	stepArray.stepCount2= stepCounts[2]
	stepArray.stepCount3= stepCounts[3]
	
	if interpolateNow :
		interpolateData(stepArray)

	return stepArray



__stripLensReg= re.compile("EF|\W")
__stripLensReg2= re.compile("[^\dFIU-]")
def getCalibrationDataFile(filePathOrName= None):
	if filePathOrName :
		filePathOrName= str(filePathOrName)
		firstChar= filePathOrName[0]
		if firstChar=="\\" or firstChar=="/" or ":" in filePathOrName :
			return io.open(filePathOrName, "rt")  # absolute file paths are opened by the system
	else:
		try:
			lensName= __stripLensReg.replace(getCameraConfig().main.status.lensname.value().upper(), "")\
									.replace("ISUSM","-IU").replace("IS", "-I").replace("USM", "-U")
			return CameraFile(__stripLensReg2.replace(lensName, "")[0:8]+".TXT")
		except:
			return CameraFile("xfocus.txt")
	return CameraFile(filePathOrName)


# Discards repeating values, interpolating the data in-between as a hyperbolic curve
def interpolateData(dataArray, startValue= None, maxValue= 0xFFFF):  # operates directly on number arrays
	__inf= float("inf")
	__nan= float("nan")
	__negInf= float("-inf")
	_dataArray= dataArray
	if isinstance(dataArray, array) :  # checks if all items are
		dataLength= len(dataArray)
		if dataArray.typecode in ('u', 'c') :
			return None
		elif dataArray.typecode not in ('d', 'f') :
			dataArray= xray(  'd' if dataArray.itemsize > 2 else 'f'  )
			for currIndex in range(0, dataLength):
				try:
					currValue= float(_dataArray[currIndex])
				except:
					currValue= __nan
				dataArray.append(currValue)
	elif isinstance(dataArray, Sequence) and not isinstance(dataArray, basestring) :
		dataLength= len(dataArray)
		dataArray= xray('d')  # use double-precision just in case
		for currIndex in range(0, dataLength):
			try:
				currValue= float(_dataArray[currIndex])
			except:
				currValue= __nan
			dataArray.append(currValue)
	else:
		return None
	
	if startValue is not None :
		try:
			startValue= float(startValue)
		except:
			startValue= None  # if startValue wasn't a number it's determined by the data
	if startValue is None or not startValue > __negInf :  # start value can NOT be -Infinity
		startValue= __inf
		started= False
		for currIndex in range(0, dataLength):
			currValue= dataArray[currIndex]
			if currValue :
				if currValue <= startValue :
					startValue= currValue
					started= True
				else :
					break
		if not started :
			startValue= 0
			
	if maxValue is not None :
		try:
			maxValue= float(maxValue)
		except:
			maxValue= None
	if maxValue is None or not maxValue >= startValue :  # max value can NOT be less than the startValue
		maxValue= __inf
		
	if dataLength < 1 :
		return None
	_dataLength= dataLength
	dataLength-= 1
	
	c0= 0
	c1= 0
	c2= 0
	lastJump= 0
	nextJump= 0
	futrJump= _dataLength
	lastValue= None
	currValue= None
	futrValue= maxValue
	lastFactor= 0
	nextFactor= 0
	started=  dataArray[0] <= startValue
	dataArray[0]= nextValue= startValue  # makes sure the data starts at startValue

	# Find the index of the next jump
	for i in range(0, _dataLength):
		v= dataArray[i]
		if not started :  # checks if the function has actually reached the startValue yet
			started=  v <= startValue
		elif v > nextValue :  # ignores any areas where the data decreases (at least for now)
			futrJump= i
			futrValue= v
			break

	for currIndex in range(0, dataLength) :
	
		if currIndex >= nextJump :
			c0= c1
			c1= c2
			lastFactor= nextFactor
			lastJump= nextJump
			nextJump= futrJump
			lastValue= currValue
			currValue= nextValue
			nextValue= futrValue
			if nextValue < maxValue :

				for i in range(nextJump+1, _dataLength):
					v= dataArray[i]
					if v > nextValue :  # ignores any areas where the data decreases (at least for now)
						futrJump= i
						futrValue= v
						break

				if futrJump == nextJump :
					futrJump= _dataLength
					futrValue= maxValue

				#jumpWeight= float(c1)/dataLength
				#jumpWeight= 0.5 + jumpWeight * jumpWeight / 2   # the weight-factor or the priority given to futrJump over nextJump
				#c2= int( nextJump * ( 1 - jumpWeight ) + futrJump * jumpWeight + 0.5 )  # rounds c2 to the nearest integer
				c2= ( nextJump + futrJump ) / 2  # fit curve to middle of each step
				nextFactor= float(dataLength-c2)/(c2-c1)*(nextValue-currValue)

			else:
				c2= dataLength
				nextFactor= 0.0
				nextJump= _dataLength
		
		if lastFactor == 0 :  # near beginning of array
			dataArray[currIndex]= currValue + (currIndex-c1)/(dataLength-currIndex)*nextFactor
		elif nextFactor > 0 :
			dataArray[currIndex]= \
			    (
			        ( lastValue + (currIndex-c0)/(dataLength-currIndex)*lastFactor ) * (nextJump-currIndex)
			         +
			        ( currValue + (currIndex-c1)/(dataLength-currIndex)*nextFactor ) * (currIndex-lastJump)
			    ) / (nextJump-lastJump)
		else:  # near end of array
			dataArray[currIndex]= lastValue + (currIndex-c0)/(dataLength-currIndex)*lastFactor
	
	if dataLength > 0 :
		dataArray[dataLength]= maxValue
			
	return dataArray
