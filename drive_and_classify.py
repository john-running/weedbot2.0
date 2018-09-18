from __future__ import absolute_import
from __future__ import division
import argparse
import sys
import numpy as np
import tensorflow as tf
from scripts.label_image import load_graph,read_tensor_from_image_file,load_labels
import smbus
import time
import wget
import sqlite3
from subprocess import call
from mdev import mDEV

			

#function to control driving of Weedbot

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

	time.sleep(drivetime) #keep motor on for prescribed time

	stop()

#function to control turning of weedbot

def turn(direction="right",turntime=3):
	
	if direction == "right":
		dir1 = 1
		dir2 = 0
	else:
		dir1 = 0
		dir2 = 1

	mdev.writeReg(mdev.CMD_DIR1,dir1)
	mdev.writeReg(mdev.CMD_DIR2,dir2)
	mdev.writeReg(mdev.CMD_PWM1,1000)
	mdev.writeReg(mdev.CMD_PWM2,1000)

	time.sleep(turntime) #keep motor on for prescribed turn time

	stop()
	
#stop function
def stop():
	mdev.writeReg(mdev.CMD_PWM1,0) # turn off electric motors 
	mdev.writeReg(mdev.CMD_PWM2,0)


def capture_image(i):
	second = str(time.localtime().tm_sec)
	hour =  str(time.localtime().tm_hour)
	day =  str(time.localtime().tm_yday)
	year =  str(time.localtime().tm_year)
	
	filename = year+day+hour+second+str(i)+'.jpg' 
	file_location = "static/" + filename
	call(["fswebcam", "-r", "320x240", "--no-banner", file_location]) # take picture with fswebcam
	return filename

def write_to_database(filename,result):
	conn=sqlite3.connect('GS.db')
	curs=conn.cursor()
	curs.execute("""INSERT INTO image_classifications (rDatetime,image_name,tf_result) values(datetime(CURRENT_TIMESTAMP, 'localtime'),
	(?), (?))""", (filename,result))
	conn.commit()
	conn.close()

#function to do the magic - take picture, classify, then store 

def classify_image(i):

	filename = capture_image(i)
	file_location = "static/" + filename
	
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

	write_to_database(filename,tf_result)
	

# funciton to drive in a prescribed path taking a set number of pictures on every leg of the trip
def driveandsnap(pictures):
	for i in range (0,pictures):  # drive then take picture then display whether weed or not
		#Drive for half a second
		drive("forward",0.5)
		time.sleep(.1)
	 	classify_image(i)

mdev = mDEV()

loopcount = 0

# run short loop to drive, take picture, classify, then turn, then repeat
while loopcount < 2:
	driveandsnap(2)
	turn("right",2)
	loopcount +=1 






