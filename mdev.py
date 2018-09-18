import smbus
import time
import threading
from threading import Lock



#Class for controlling motors

class mDEV:
	CMD_SERVO1 		= 	0
	CMD_SERVO2 		= 	1
	CMD_SERVO3 		= 	2
	CMD_SERVO4 		= 	3
	CMD_PWM1		=	4
	CMD_PWM2		=	5
	CMD_DIR1		=	6
	CMD_DIR2		=	7
	CMD_BUZZER		=	8
	CMD_IO1			=	9
	CMD_IO2			=	10
	CMD_IO3			=	11
	CMD_SONIC		=	12
	SERVO_MAX_PULSE_WIDTH = 2500
	SERVO_MIN_PULSE_WIDTH = 500
	SONIC_MAX_HIGH_BYTE = 50
	Is_IO1_State_True = False
	Is_IO2_State_True = False
	Is_IO3_State_True = False
	Is_Buzzer_State_True = False
	handle = True
	mutex = Lock()
	def __init__(self,addr=0x18):
		self.address = addr	#default address of mDEV
		self.bus=smbus.SMBus(1)
		self.bus.open(1)
	def i2cRead(self,reg):
		self.bus.read_byte_data(self.address,reg)
		
	def i2cWrite1(self,cmd,value):
		self.bus.write_byte_data(self.address,cmd,value)
		
	def i2cWrite2(self,value):
		self.bus.write_byte(self.address,value)
	
	def writeReg(self,cmd,value):
		try:
			self.bus.write_i2c_block_data(self.address,cmd,[value>>8,value&0xff])
			time.sleep(0.001)
			self.bus.write_i2c_block_data(self.address,cmd,[value>>8,value&0xff])
			time.sleep(0.001)
			self.bus.write_i2c_block_data(self.address,cmd,[value>>8,value&0xff])
			time.sleep(0.001)
		except Exception,e:
			print Exception,"I2C Error :",e
		
	def readReg(self,cmd):		
		##################################################################################################
		#Due to the update of SMBus, the communication between Pi and the shield board is not normal. 
		#through the following code to improve the success rate of communication.
		#But if there are conditions, the best solution is to update the firmware of the shield board.
		##################################################################################################
		for i in range(0,10,1):
			self.bus.write_i2c_block_data(self.address,cmd,[0])
			a = self.bus.read_i2c_block_data(self.address,cmd,1)
			
			self.bus.write_byte(self.address,cmd+1)
			b = self.bus.read_i2c_block_data(self.address,cmd+1,1)
			
			self.bus.write_byte(self.address,cmd)
			c = self.bus.read_byte_data(self.address,cmd)
			
			self.bus.write_byte(self.address,cmd+1)
			d = self.bus.read_byte_data(self.address,cmd+1)
			#print i,a,b,c,d
			#'''
			if(a[0] == c and c < self.SONIC_MAX_HIGH_BYTE ): #and b[0] == d
				return c<<8 | d
			else:
				continue
			#'''
			'''
			if (a[0] == c and c < self.SONIC_MAX_HIGH_BYTE) :
				return c<<8 | d
			elif (a[0] > c and c < self.SONIC_MAX_HIGH_BYTE) :
				return c<<8 | d
			elif (a[0] < c and a[0] < self.SONIC_MAX_HIGH_BYTE) :
				return a[0]<<8 | b[0]
			else :
				continue
			'''
		return 0
		#################################################################################################
		#################################Old codes#######################################################
		#[a,b]=self.bus.read_i2c_block_data(self.address,cmd,2)
		#print "a,b",[a,b]
		#return a<<8 | b
		#################################################################################################
	
	def getSonicEchoTime():
		SonicEchoTime = mdev.readReg(mdev.CMD_SONIC)
		return SonicEchoTime
		
	def getSonic(self):
		SonicEchoTime = mdev.readReg(mdev.CMD_SONIC)
		distance = SonicEchoTime * 17.0 / 1000.0
		return distance
	def setShieldI2cAddress(self,addr): #addr: 7bit I2C Device Address 
		if (addr<0x03) or (addr > 0x77) :
			return 
		else :
			mdev.writeReg(0xaa,(0xbb<<8)|(addr<<1))