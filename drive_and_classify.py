from __future__ import absolute_import
from __future__ import division
import argparse
import sys
import numpy as np
import tensorflow as tf
from scripts.label_image import load_graph,read_tensor_from_image_file,load_labels
import smbus
import time
import threading
from threading import Lock
import wget
import sqlite3
from subprocess import call


def numMap(value,fromLow,fromHigh,toLow,toHigh):
	return (toHigh-toLow)*(value-fromLow) / (fromHigh-fromLow) + toLow

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
			



def drive(direction="forward",drivetime=.5):

	if direction == "forward":
		dir = 0
	else:
		dir = 1

		#Drive for half a second
	mdev.writeReg(mdev.CMD_DIR1,dir)
	mdev.writeReg(mdev.CMD_DIR2,dir)
	mdev.writeReg(mdev.CMD_PWM1,1000)
	mdev.writeReg(mdev.CMD_PWM2,1000)

	time.sleep(drivetime) #keep motor on for .15 seconds

	stop()


def turn(direction="right",turntime=3):
	
	if direction == "right":
		dir1 = 1
		dir2 = 0
	else:
		dir1 = 0
		dir2 = 1

	mdev.writeReg(mdev.CMD_DIR1,dir1)
	mdev.writeReg(mdev.CMD_DIR2,dir2)
	mdev.writeReg(mdev.CMD_PWM1,900)
	mdev.writeReg(mdev.CMD_PWM2,900)

	time.sleep(turntime) #keep motor on for .15 seconds

	stop()
	

def stop():
	mdev.writeReg(mdev.CMD_PWM1,0) # turn off electric motors 
	mdev.writeReg(mdev.CMD_PWM2,0)


def loop():	
	mdev.readReg(mdev.CMD_SONIC)
	while True:
		SonicEchoTime = mdev.readReg(mdev.CMD_SONIC)
		distance = SonicEchoTime * 17.0 / 1000.0
		print "EchoTime: %d, Sonic: %.2f cm"%(SonicEchoTime,distance)
		time.sleep(0.001)





def classify_image(i):

	second = str(time.localtime().tm_sec)
	hour =  str(time.localtime().tm_hour)
	day =  str(time.localtime().tm_yday)
	year =  str(time.localtime().tm_year)
	
	filename = year+day+hour+second+str(i)+'.jpg' 
	file_location = "static/" + filename
	
	call(["fswebcam", "-r", "320x240", "--no-banner", file_location]) # take picture with fswebcam
	time.sleep(0.1)

	model_file = "tf_files/retrained_graph.pb" #local
	label_file = "tf_files/retrained_labels.txt" #local
	input_height = 224
	input_width = 224
	input_mean = 128
	input_std = 128
	input_layer = "input"
	output_layer = "final_result"

	graph = load_graph(model_file)
	t = read_tensor_from_image_file(file_location,
                                    input_height=input_height,
                                    input_width=input_width,
                                    input_mean=input_mean,
                                    input_std=input_std)

	input_name = "import/" + input_layer
	output_name = "import/" + output_layer
	input_operation = graph.get_operation_by_name(input_name);
	output_operation = graph.get_operation_by_name(output_name);

	with tf.Session(graph=graph) as sess:
		start = time.time()
		results = sess.run(output_operation.outputs[0],
                        {input_operation.outputs[0]: t})
		end=time.time()

	results = np.squeeze(results)

	top_k = results.argsort()[-5:][::-1]
	labels = load_labels(label_file)

	dlabels = [] # store results of classification in an array
	dresults = []
	for i in top_k:
		dlabels.append(labels[i])
		dresults.append(results[i])

	tf_result = str(dlabels[0]) + " : " +  str(int(dresults[0]*100))

	conn=sqlite3.connect('GS.db')
	curs=conn.cursor()
	curs.execute("""INSERT INTO image_classifications (rDatetime,image_name,tf_result) values(datetime(CURRENT_TIMESTAMP, 'localtime'),
	(?), (?))""", (filename,tf_result))
	conn.commit()
	conn.close()

def driveandsnap(pictures = 20):

	for i in range (0,pictures):  # drive then take picture then display whether weed or not
		
		#Drive for half a second
		
		drive("forward",0.5)
		time.sleep(.1)
	 	classify_image(i)


mdev = mDEV()

loopcount = 0
while loopcount < 4:
	
	driveandsnap(4)
	turn("right",2)
	
	loopcount +=1 






