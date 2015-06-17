# -*- coding:utf-8 -*-
"""
Created on Mar 24, 2014

@author: Filip Lindau
"""
import socket
import numpy as np
import threading
import time

class RedPitayaData(object):
	def __init__(self):
		self.triggerMode = 'AUTO'
		self.triggerSource = 'CHANNEL1'
		self.triggerEdge = 'pe'
		self.triggerLevel = 0.0
#		self.triggerDelay = 0.0
		self.triggerDelayTime = 0.0
		self.triggerDelaySamples = 4096
		self.triggerWait = False
		self.recordLength = 8192
		self.decimationFactor = 0
		self.sampleRate = 125e6
		self.waveform1 = np.zeros(2000)
		self.triggerCounter1 = 0
		self.waveform2 = np.zeros(2000)
		self.triggerCounter2 = 0
		self.waveformDatatype = np.float32
		self.timevector = np.zeros(2000)
		self.fps = 0.0
		self.maxADCv_ch1 = 1.0
		self.maxADCv_ch2 = 1.0
		self.dcOffset_ch1 = 0
		self.dcOffset_ch2 = 0
		self.adcFactor_ch1 = 1.0
		self.adcFactor_ch2 = 1.0


class RedPitaya_control(object):
	def __init__(self, ip, port=8888):
		self.redPitayaData = RedPitayaData()

		self.lock = threading.Lock()
		self.dtSize = 10
		self.dtArray = np.zeros(self.dtSize)
		self.dtIndex = 0
		self.t0 = time.time()

		self.ip = ip
		self.port = port
		self.connected = False
		self.connect(self.ip, self.port)

		self.getCalibrationFactors()

	def connect(self, ip, port):
		if self.connected == True:
			self.close()

		self.sock = socket.socket()
		self.sock.settimeout(0.5)
		self.sock.connect((ip, port))
		self.connected = True

	def close(self):
		try:
			self.connected = False
			self.sock.close()
			self.sock = None
		except:
			pass

	def sendReceive(self, msg):
		if self.connected == False:
			self.connect(self.ip, self.port)
		msgLen = len(msg)
		retLen = self.sock.send(msg)
		if retLen != msgLen:
			raise IOError('Did not send full message')
		rep = self.sock.recv(70000)
		return rep

	def initScope(self):
		self.setTriggerSource(self.redPitayaData.triggerSource)
		self.setTriggerMode(self.redPitayaData.triggerMode)
		self.setTriggerLevel(self.redPitayaData.triggerLevel)
#        self.setTriggerEdge(self.redPitayaData.triggerEdge)
		self.setRecordLength(self.redPitayaData.recordLength)
		self.setDecimationFactor(self.redPitayaData.decimationFactor)

	def getCalibrationFactors(self):
		msg = 'getCalibrationOffset:0'
		calString = self.sendReceive(msg)
		self.redPitayaData.dcOffset_ch1 = np.fromstring(calString, dtype=np.int32)[0]
		self.redPitayaData.dcOffset_ch1 = -150
		msg = 'getCalibrationOffset:1'
		calString = self.sendReceive(msg)
		self.redPitayaData.dcOffset_ch2 = np.fromstring(calString, dtype=np.int32)[0]
		self.redPitayaData.dcOffset_ch2 = -150
		msg = 'getCalibrationMaxADC:0'
		calString = self.sendReceive(msg)
		self.redPitayaData.maxADCv_ch1 = np.fromstring(calString, dtype=np.float32)[0]
		msg = 'getCalibrationMaxADC:1'
		calString = self.sendReceive(msg)
		self.redPitayaData.maxADCv_ch2 = np.fromstring(calString, dtype=np.float32)[0]

		self.redPitayaData.adcFactor_ch1 = self.redPitayaData.maxADCv_ch1 / 2 ** 13
		self.redPitayaData.adcFactor_ch2 = self.redPitayaData.maxADCv_ch2 / 2 ** 13

		print 'Calibration factors:'
		print 'max adc 1: ', self.redPitayaData.maxADCv_ch1
		print 'max adc 2: ', self.redPitayaData.maxADCv_ch2
		print 'offset 1: ', self.redPitayaData.dcOffset_ch1
		print 'offset 2: ', self.redPitayaData.dcOffset_ch2

	def setTriggerSource(self, source):
		""" Set the trigger source to use.
		Input: ch1, ch2 or ext
		"""
		sp = str(source).lower()
		if sp in ['ch1', 'channel1', '1']:
			sp = 'channel1'
			sourceMsg = 'CH1'
		elif sp in ['ch2', 'channel2', '2']:
			sp = 'channel2'
			sourceMsg = 'CH2'
		elif sp in ['ext', 'external']:
			sp = 'external'
			sourceMsg = 'EXT'
		else:
			raise ValueError(''.join(('Wrong trigger source ', str(source), ', use ch1, ch2, or ext')))
		edge = self.redPitayaData.triggerEdge
		self.setTriggerSourceEdge(sp, edge)

	def setTriggerSourceEdge(self, source, edge):
		""" Set the trigger source and edge to use.
		Input: 
			source: ch1, ch2 or ext
			edge: pe or ne
		"""
		sp = str(source).lower()
		ed = str(edge).lower()
		if sp in ['ch1', 'channel1', '1']:
			sp = 'channel1'
			sourceMsg = 'RP_TRIG_SRC_CHA'
		elif sp in ['ch2', 'channel2', '2']:
			sp = 'channel2'
			sourceMsg = 'RP_TRIG_SRC_CHB'
		elif sp in ['ext', 'external']:
			sp = 'external'
			sourceMsg = 'RP_TRIG_SRC_EXT'
		else:
			raise ValueError(''.join(('Wrong trigger source ', str(source), ', use ch1, ch2, or ext')))
		if ed == 'pe':
			sourceMsg = ''.join((sourceMsg, '_PE'))
		elif ed == 'ne':
			sourceMsg = ''.join((sourceMsg, '_NE'))
		else:
			raise ValueError(''.join(('Wrong trigger edge ', str(edge), ', use pe, or ne')))
		self.lock.acquire()		
		msg = ''.join(('setTriggerSource:', sourceMsg))
		print msg
		reply = self.sendReceive(msg)
		self.lock.release()
		if reply != 'OK':
			print 'Error setTriggerSource: ', reply 
		self.redPitayaData.triggerSource = sp
		self.redPitayaData.triggerEdge = ed
		
	def getTriggerSource(self):
		return self.redPitayaData.triggerSource

	def setTriggerMode(self, mode):
		sp = str(mode).lower()
		if sp in ['auto', 'a']:
			sp = 'auto'
			cmdMsg = 'AUTO'
		elif sp in ['normal', 'norm', 'n']:
			sp = 'normal'
			cmdMsg = 'NORMAL'
		elif sp in ['single', 'sing', 's']:
			sp = 'single'
			cmdMsg = 'SINGLE'
		else:
			raise ValueError(''.join(('Wrong trigger mode ', str(mode), ', use auto, normal, or single')))
		self.lock.acquire()
		msg = ''.join(('setTriggerMode:', cmdMsg))
		self.sendReceive(msg)
		self.lock.release()
		self.redPitayaData.triggerMode = sp

	def getTriggerMode(self):
		return self.redPitayaData.triggerMode

	def setTriggerEdge(self, edge):
		sp = str(edge).lower()
		if sp in ['rising', 'rise', 'r', '0', 'pe']:
			sp = 'pe'
		elif sp in ['falling', 'fall', 'f', '1', 'ne']:
			sp = 'ne'
		else:
			raise ValueError(''.join(('Wrong trigger edge ', str(edge), ', use rising, or falling')))
		source = self.redPitayaData.triggerSource
		self.setTriggerSourceEdge(source, sp)

	def getTriggerEdge(self):
		if self.redPitayaData.triggerEdge == 'pe':
			return 'POSITIVE'
		else:
			return 'NEGATIVE'

	def setRecordLength(self, recLength):
		if recLength > 12000:
			recLength = 12000
		elif recLength < 1:
			recLength = 1
		self.lock.acquire()
		msg = ''.join(('setRecordLength:', str(recLength)))
		self.sendReceive(msg)
		self.lock.release()
		self.redPitayaData.recordLength = recLength
		self.generateTimevector()

	def getRecordLength(self):
		return self.redPitayaData.recordLength

	def setDecimationFactor(self, decFactor):
		if decFactor > 5:
			decFactor = 5
		elif decFactor < 0:
			decFactor = 0
		self.lock.acquire()
		msg = ''.join(('setDecimation:', str(decFactor)))
		self.sendReceive(msg)
		self.lock.release()
		self.redPitayaData.decimationFactor = decFactor
		self.generateTimevector()

	def getDecimationFactor(self):
		return self.redPitayaData.decimationFactor

	def generateTimevector(self):
		# Base sampling rate 125 MSPS. It is decimated by decimationfactor according to:
		decDict = {0: 1,
				   1: 8,
				   2: 64,
				   3: 1024,
				   4: 8192,
				   5: 16384}
		dt = decDict[self.redPitayaData.decimationFactor] / 125e8
		self.redPitayaData.sampleRate = 125e8 / decDict[self.redPitayaData.decimationFactor]
		self.redPitayaData.timevector = np.linspace(0, dt * self.redPitayaData.recordLength, self.redPitayaData.recordLength)

	def getTimevector(self):
		return self.redPitayaData.timevector

	def getSampleRate(self):
		return self.redPitayaData.sampleRate

	def setTriggerLevel(self, trigLevel):
		if trigLevel > 2:
			trigLevel = 2
		elif trigLevel < -2:
			trigLevel = -2
		self.lock.acquire()
		msg = ''.join(('setTriggerLevel:', str(trigLevel)))
		self.sendReceive(msg)
		self.lock.release()
		self.redPitayaData.triggerLevel = trigLevel

	def getTriggerLevel(self):
		return self.redPitayaData.triggerLevel

	def setTriggerDelayTime(self, trigDelay):
		"""Set trigger delay in s 
		"""
		self.redPitayaData.triggerDelayTime = trigDelay
		triggerDelaySamples = self.redPitayaData.recordLength / 2.0 - trigDelay * self.redPitayaData.sampleRate
		if triggerDelaySamples < 0:
			self.setTriggerDelaySamples(0)
		elif triggerDelaySamples > self.redPitayaData.recordLength:
			self.setTriggerDelaySamples(self.redPitayaData.recordLength)
		else:
			self.setTriggerDelaySamples(triggerDelaySamples)
		

	def setTriggerDelaySamples(self, trigDelay):
		print "New trig delay: ", trigDelay, " samples"
		with self.lock:
			msg = ''.join(('setTriggerDelaySamples:', str(np.int(trigDelay)))) # Trigger delay is in samples
			self.sendReceive(msg)
		self.redPitayaData.triggerDelaySamples = trigDelay
		self.redPitayaData.triggerDelayTime = (self.redPitayaData.recordLength / 2.0 - trigDelay) / self.redPitayaData.sampleRate
		
	def setTriggerPos(self, trigPos):
		self.lock.acquire()
		msg = ''.join(('setTriggerPos:', str(trigPos))) # Trigger delay is in decimated samples
		self.sendReceive(msg)
		self.lock.release()
		self.redPitayaData.triggerDelay = trigPos / self.redPitayaData.sampleRate

	def getTriggerDelayTime(self):
		return self.redPitayaData.triggerDelayTime

	def getTriggerDelaySamples(self):
		return self.redPitayaData.triggerDelaySamples
		
	def getTriggerCounter(self, channel):
		""" triggerCounter = getTriggerCounter(channel)
		
		input: 
			channel = 1 or 2
		output:
			triggerCounter = redpitaya internal trigger counter for the specific
							 channel from the latest updateWaveform call
			
		Returns trigger counter for the waveform stored in the redPitayaData data structure
		"""
		if channel == 1:
			return self.redPitayaData.triggerCounter1
		elif channel == 2:
			return self.redPitayaData.triggerCounter2
		else:
			raise ValueError(''.join(('Wrong channel ', str(channel), ', use 1, or 2')))
		
	def getFPGATemp(self):
		self.lock.acquire()
		msg = 'getFPGATemp' 
		tempString = self.sendReceive(msg)
		self.lock.release()
		return np.double(tempString)

	def getWaveform(self, channel):
		""" waveform = getWaveform(channel)
		
		input: 
			channel = 1 or 2
		output:
			waveform = numpy array containing the data from the latest updateWaveform call
			
		Returns a waveform stored in the redPitayaData data structure
		"""
#        self.lock.acquire()
		if channel == 1:
			return self.redPitayaData.waveform1
		elif channel == 2:
			return self.redPitayaData.waveform2
		else:
			raise ValueError(''.join(('Wrong channel ', str(channel), ', use 1, or 2')))
#        self.lock.release()

	def updateWaveforms(self):
		with self.lock:
			sig1 = self.sendReceive('getWaveformFloat:0')
			if sig1 != 'not triggered':
				retries = 1
				itemsize = self.redPitayaData.waveformDatatype().itemsize
				readLength = np.int(np.fromstring(sig1[0:itemsize], dtype=self.redPitayaData.waveformDatatype))
#				print "getWaveform:0 expected read length ", readLength 
				trigCounter = np.int(np.fromstring(sig1[itemsize:2 * itemsize], dtype=self.redPitayaData.waveformDatatype))
				while len(sig1) < (readLength + 2) * itemsize:
	#				print ''.join(("getWaveform:0 returned ", str(len(sig1)), ' bytes')) 
					try:
						extradata = self.sock.recv(70000)
					except socket.timeout:
						print "getWaveformFloat:0... Receive timeout"
						return False
					sig1 = ''.join((sig1, extradata))
					retries += 1
					if retries > 100:
						print "getWaveformFloat:0... Retries exceeded"
						return False
					if len(sig1) < (readLength + 2) * itemsize:
						time.sleep(0.00005)
				if self.redPitayaData.waveformDatatype == np.int16:
					print "getWaveformFloat:0... Rescaling data"
					self.redPitayaData.waveform1 = self.redPitayaData.adcFactor_ch1 * (np.fromstring(sig1[self.redPitayaData.waveformDatatype().itemsize:], dtype=self.redPitayaData.waveformDatatype) - self.redPitayaData.dcOffset_ch1)
				else:
					self.redPitayaData.waveform1 = np.fromstring(sig1[2 * itemsize:], dtype=self.redPitayaData.waveformDatatype)
					self.redPitayaData.triggerCounter1 = trigCounter
					
				sig2 = self.sendReceive('getWaveformFloat:1')
				retries = 1
				itemsize = self.redPitayaData.waveformDatatype().itemsize
				readLength = np.int(np.fromstring(sig2[0:itemsize], dtype=self.redPitayaData.waveformDatatype))
#				print "getWaveform:1 expected read length ", readLength 
				trigCounter = np.int(np.fromstring(sig2[itemsize:2 * itemsize], dtype=self.redPitayaData.waveformDatatype))
				while len(sig2) < (readLength + 2) * itemsize:
	#				print ''.join(("getWaveform:1 returned ", str(len(sig1)), ' bytes')) 
					try:
						extradata = self.sock.recv(70000)
					except socket.timeout:
						print "getWaveformFloat:1... Receive timeout"
						return False
					sig2 = ''.join((sig2, extradata))
					retries += 1
					if retries > 100:
						print "getWaveformFloat:1... Retries exceeded"
						return False
					if len(sig2) < (readLength + 2) * itemsize:
						time.sleep(0.00005)
				if self.redPitayaData.waveformDatatype == np.int16:
					print "getWaveformFloat:1... Rescaling data"
					self.redPitayaData.waveform2 = self.redPitayaData.adcFactor_ch2 * (np.fromstring(sig1[self.redPitayaData.waveformDatatype().itemsize:], dtype=self.redPitayaData.waveformDatatype) - self.redPitayaData.dcOffset_ch2)
				else:
					self.redPitayaData.waveform2 = np.fromstring(sig2[2 * itemsize:], dtype=self.redPitayaData.waveformDatatype)
					self.redPitayaData.triggerCounter2 = trigCounter
									
				t = time.time()
				dt = t - self.t0
				self.dtArray[self.dtIndex % self.dtSize] = dt
				if self.dtIndex > self.dtSize:
					self.redPitayaData.fps = 1 / self.dtArray.mean()
				else:
					self.redPitayaData.fps = 1 / self.dtArray[0:self.dtIndex]
				self.t0 = t
				self.dtIndex += 1
		if sig1 == 'not triggered':
#			print "Not triggered"
			return False
		else:
			return True

	def updateWaveformsOld(self):
		self.lock.acquire()
		sig1 = self.sendReceive('getWaveform:0')
		if sig1 != 'not triggered':
			retries = 1
			while len(sig1) != self.redPitayaData.recordLength * self.redPitayaData.waveformDatatype().itemsize:
				print ''.join(("getWaveform:0 returned ", str(len(sig1)), ' bytes')) 
				try:
					extradata = self.sock.recv(70000)
				except socket.timeout:
					print "Receive timeout"
					return False
				sig1 = ''.join((sig1, extradata))
				retries += 1
				if retries > 10:
					print "Retries exceeded"
					return False
			self.redPitayaData.waveform1 = self.redPitayaData.adcFactor_ch1 * (np.fromstring(sig1, dtype=self.redPitayaData.waveformDatatype) - self.redPitayaData.dcOffset_ch1)
			t = time.time()
			dt = t - self.t0
			self.dtArray[self.dtIndex % self.dtSize] = dt
			if self.dtIndex > self.dtSize:
				self.redPitayaData.fps = 1 / self.dtArray.mean()
			else:
				self.redPitayaData.fps = 1 / self.dtArray[0:self.dtIndex]
			self.t0 = t
			self.dtIndex += 1
		sig2 = self.sendReceive('getWaveform:1')
		if sig2 != 'not triggered':
			retries = 1
			while len(sig2) != self.redPitayaData.recordLength * self.redPitayaData.waveformDatatype().itemsize:
				try:
					extradata = self.sock.recv(70000)
				except socket.timeout:
					print "Receive timeout"
					return False
				sig2 = ''.join((sig2, extradata))
				retries += 1
				if retries > 10:
					print "Retries exceeded channel 2"
					return False
			self.redPitayaData.waveform2 = self.redPitayaData.adcFactor_ch2 * (np.fromstring(sig2, dtype=self.redPitayaData.waveformDatatype) - self.redPitayaData.dcOffset_ch2)
		self.lock.release()
		if sig1 == 'not triggered':
			print "Not triggered"
			return False
		else:
			return True

#    def updateWaveforms(self):
#        self.lock.acquire()
#        sig1 = self.sendReceive('getWaveforms')
#        if sig1 != 'not triggered':
#            retries = 1
#            while len(sig1) != self.redPitayaData.recordLength * 4 * 2:
#                extradata = self.sock.recv(70000)
#                sig1 = ''.join((sig1, extradata))
#                retries += 1
#                if retries > 10:
#                    return False
#            waveforms = np.fromstring(sig1, dtype=np.float32)
#            self.redPitayaData.waveform1 = self.redPitayaData.adcFactor_ch1 * (waveforms[0:waveforms.shape[0] / 2] - self.redPitayaData.dcOffset_ch1)
#            t = time.time()
#            dt = t - self.t0
#            self.dtArray[self.dtIndex % self.dtSize] = dt
#            if self.dtIndex > self.dtSize:
#                self.redPitayaData.fps = 1 / self.dtArray.mean()
#            else:
#                self.redPitayaData.fps = 1 / self.dtArray[0:self.dtIndex]
#            self.t0 = t
#            self.redPitayaData.waveform2 = self.redPitayaData.adcFactor_ch2 * (waveforms[waveforms.shape[0] / 2:] - self.redPitayaData.dcOffset_ch2)
#        self.lock.release()
#        if sig1 == 'not triggered':
#            return False
#        else:
#            return True

