#!/usr/bin/python2
import rospy
import math
from ivy.std_api import *
from std_msgs.msg import String
#from geometry_msgs.msg import Pose2D
from tracking.msg import TaggedPose2D
import time
"""kill_log resides in the upper directory to this script"""
import os
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.insert(0,parentdir)
import kill_log

# global values
deg2rad = math.pi / 180
rad2deg = 180 / math.pi
lat = 52.138821 * deg2rad  # Latitude of FIN
lon = 11.645634  * deg2rad # Longitude of FIN
gps_lat = 52.13882 * 10000000
gps_lon = 11.645634 * 10000000
weekInMilliseconds = 604800000

class IvyCalibrationNode:
    def __init__(self):
        self.myKillLog = kill_log.KillLog()
    
    def IvyInitStart(self):
        """ Initializes the Ivy Server and ROS Subscriber

        Should only be called once per session.
        """
	

        try:
            IvyInit('Calibration Node', '', 0)
        except AssertionError:
            print('Assertion Error in IvyInit(!= none), is there a server already running? Exiting')
            IvyStop()
            raise SystemExit()
        IvyStart()
        try:
            self.initRosSub()
        except rospy.exceptions.ROSInitException as e:
            print('\nInitialization failed due to ROS error, exiting...')
            self.IvyInitStop()
        time.sleep(1)
        print('Ivy Calibration Node ready!')
	
        # initial value for oldTime
	
	global oldX
	oldX = 0
	global oldY
	oldY = 0
	global oldZ
	oldZ = 0
	global tow
	tow = 0
        global oldTime 
	oldTime = rospy.get_rostime()
	global oldData
	global course
	course = 0.0

        rospy.spin()
        print("after ctrl + c")
        self.IvyInitStop()


    def IvyInitStop(self):
        """Stops the Ivy Server.
        """
        time.sleep(1)
        IvyStop()


    def handlePos(self, data):
        """ Callback for the ROS subscriber.


        """
        global oldTime
	global oldData
	global oldX
	global oldY
	global oldZ
	global tow
	global course

	# offsets for camera positions
	offsetX =  data.x
	offsetY =  data.y
	offsetZ =  0

	# offsets for Latitude = 52.1205 and Longitude = 11.6276 (Rotation around Y and Z)
	#offsetX =  math.cos(lat)*math.cos(lon)*data.x - math.cos(lat)*math.sin(lon)*data.y
	#offsetY =  math.sin(lon)* data.x              + math.cos(lon) * data.y
	#offsetZ = -math.sin(lat)*math.cos(lon)*data.x + math.sin(lat)*math.sin(lon)*data.y

	## offsets for Latitude = 52.1205 and Longitude = 11.6276 (Rotation around X and Z)
	#offsetX =  math.cos(lon)*data.x                - math.sin(lon)*data.y
	#offsetY =  math.cos(lat)*math.sin(lon)* data.x + math.cos(lat)*math.cos(lon) * data.y 
	#offsetZ =  math.sin(lat)*math.sin(lon)*data.x  + math.sin(lat)*math.cos(lon) * data.y
	
	#rospy.loginfo("cameraPos %f, %f", data.x, data.y)
	#rospy.loginfo("Offsets %f, %f, %f", offsetX, offsetY, offsetZ)
	#rospy.loginfo("Distances %f, %f, %f", offsetX - oldX, offsetY - oldY, offsetZ - oldZ)


	# getting time difference between now and last run
	now = data.header.stamp
	timediff = 0
	if( (now.secs - oldTime.secs) == 0):
		timediff = now.nsecs - oldTime.nsecs
	else:
		timediff = 1000000000 + now.nsecs - oldTime.nsecs
	oldTime = now
	timediff = timediff / 1000000000.0
	
	#rospy.loginfo("timediff float %f", timediff)

	# geting difference for X pos and Y pos and Z pos and calculate speed
	
	ecef_xd= (offsetX - oldX) / timediff	
	ecef_yd= (offsetY - oldY) / timediff	
	ecef_zd= (offsetZ - oldZ) / timediff	
	
	#rospy.loginfo("Speeds %f, %f, %f", ecef_xd, ecef_yd, ecef_zd)

	oldX = offsetX
	oldY = offsetY
	oldZ = offsetZ

	# for TOW
	if (tow == 0):
		tow = now.secs * 1000 + int(now.nsecs / 1000000)
		tow = tow % weekInMilliseconds

	if (timediff < 1.0):
		tow += int(timediff * 1000)
		tow = tow % weekInMilliseconds

	# tow = now.secs
	# for Course we need angle (in rad) of LTP.  We get LTP by ECEF and LLA and Rot Mat of ECEF 2 ENU

	# Rot_ecef2enu

	#enu_xd = -math.sin(lon)*ecef_xd               + math.cos(lon)*ecef_yd
	#enu_yd = -math.sin(lat)*math.cos(lon)*ecef_xd + (-math.sin(lat)*math.sin(lon)*ecef_yd) + math.cos(lat)*ecef_zd
	#enu_zd =  math.cos(lat)*math.cos(lon)*ecef_xd + math.cos(lat)*math.sin(lon)*ecef_yd    + math.sin(lat)*ecef_zd
	
	#course = math.atan2(enu_yd, enu_xd)	

	rospy.loginfo("type %s", type(data))
	
	previousCourse = course	

	try:
		distX = data.x - oldData.x
		distY = data.y - oldData.y
		dist = math.sqrt(distX*distX + distY*distY)		
	
		course = math.acos(distX / dist)

		if(distY < 0):
			course = 2*math.pi - course
	except:
		oldData = data
		rospy.loginfo("error olddata")
		course = previousCourse/10000000.0
	
	rospy.loginfo("course %f", course)
	# course in rad*1e7, [0, 2*Pi]*1e7 (CW/north)
	rospy.loginfo("data-x %f  data-y %f", data.x, data.y)
	rospy.loginfo("data-x %s  data-y %s", type(data.x), type(data.y))
	rospy.loginfo("data-x %d  data-y %d", int(384205200 + data.x), int(79184900 + data.y))
	rospy.loginfo("data-x %s  data-y %s", type(int(384205200 + data.x)), type(int(79184900 + data.y)))

	course = int(course * 10000000)

	earthRadius = 636485000
	ecef_magnitude = math.sqrt((384205200 + offsetX)*(384205200 + offsetX) + (79184900 + offsetY)*(79184900 + offsetY) + (501233200 + offsetZ)*(501233200 + offsetZ))
	hmsl = (ecef_magnitude - earthRadius) * 10 # in mm
        #test value
	hmsl = 1000;

                             #AC_ID, numsv, ecef_x, ecef_y, ecef_z, 					     lat, lon, alt, hmsl, ecef_xd, ecef_yd, ecef_zd, tow, course
        #self.IvySendRemoteGPS(1,     6,     384205200 + offsetX, 79184900 + offsetY, 501233200 + offsetZ,      gps_lat,   gps_lon,   0,   hmsl,  ecef_xd, ecef_yd, ecef_zd, tow, course)
	self.IvySendRemoteGPS(3,     6,     384205200 + data.x , 79184900 + data.y, 501233200 + 60,      gps_lat,   gps_lon,   0,   hmsl,  ecef_xd, ecef_yd, ecef_zd, tow, course)
	#self.IvySendRemoteGPS(3,     6,     384205200, 79184900, 501233200,      0,   0,   0,   hmsl,  ecef_xd, ecef_yd, ecef_zd, tow, course)
	#self.IvySendRemoteGPS(1,     6,     384205200, 79184900 , 501233200 ,      0,   0,   0,   hmsl, 0, 0, 0, tow, course)

        # loop for sending GPS for swarmbehaviour to all other copters
	#IvySendGPSBroadcast(AC_ID, copter_id, gps_x, gps_y, gps_z, gps_xd, gps_yd, gps_zd)


	#send camera heading in degree
	self.IvySendCameraTheta(3, 0, data.theta + 185)

	#just for tests a virtual copter 2 sends its position to copter 1
	#self.IvySendINSBroadcast(1, 2, 35, 53, 14, 0, 0, 0, 0, 0, 0)
	#self.IvySendINSBroadcast(1, 2, 1500, 1300, 14, 0, 0, 0, 0, 0, 0)
	oldData = data

    def initRosSub(self):
        """ Initializes the ROS subscriber.

        Is automatically called during the Ivy initialization process
        in IvyInitStart().
        """
        try:
            rospy.init_node('poseListener', anonymous=False)
        except KeyboardInterrupt:
            print('\nROS initialization canceled by user')
        except rospy.exceptions.ROSInitException as e:
            print('\nError Initializing ROS:')
            print(str(e))
            raise
	
        #rospy.Subscriber("copters/0/pose", Pose2D, self.handlePos)
	rospy.Subscriber("/copter/blue", TaggedPose2D, self.handlePos)


    def IvyGetPos(self):
        """Simply returns the position grabbed via ROS to the caller

        """
        try:
            return copterPos
        except NameError as e:
            print("CopterPos not yed defined! (No data from ROS?):")
            print(str(e))

    def IvyGetPosList(self):
        """Returns the position to a list for less dependency with ros
           Returns
           -------
           List
        """
        position = self.IvyGetPos()
        return [position.x, position.y, position.theta]

    def IvySendCalib(self,param_ID, AC_ID, value):
        """Sends the given parameter via Ivy

        AC_ID:      ID of the aricraft to be calibrated
        param_ID:   ID of the parameter to be calibrated
                     phi   = 58 roll
                     theta = 59 pitch
                     psi   = 60 yaw
        value:      value to be set for the parameter !in degrees!
        """
        print("sending calib msg")
        IvySendMsg('dl SETTING %d %d %f' %
                    (AC_ID,
                    param_ID,
                    value
                    ))


    def IvySendKill(self, AC_ID):
        """Sends a kill message to the aircraft

        """
        IvySendMsg('dl KILL %d 1' %
                    (AC_ID
                    ))
        
    def SetInDeadZone(self,inDeadZone):
        self.myKillLog.inDeadZone = inDeadZone

    def IvySendCalParams(self, AC_ID, turn_leds, roll, pitch, yaw):
        IvySendMsg('dl CALPARAMS %d %d %f %f %f' %
                    (AC_ID, turn_leds, roll, pitch, yaw
                    ))

    def IvySendCopterPose(self, AC_ID, posX, posY, theta):
        IvySendMsg('dl COPTERPOSE %d %f %f %f' %
                    (AC_ID, posX, posY, theta
                    ))

    def IvySendCameraTheta(self, AC_ID, dummy, theta):
        IvySendMsg('dl CAMERA_THETA %d %d %f' %
                    (AC_ID, dummy, theta) )

    def IvySendRemoteGPS(self, AC_ID, numsv, ecef_x, ecef_y, ecef_z, lat, lon, alt, hmsl, ecef_xd, ecef_yd, ecef_zd, tow, course):
	rospy.loginfo("gps-x %s  gps-y %s", (ecef_x), (ecef_y))
        IvySendMsg('dl REMOTE_GPS %d %d %d %d %d %d %d %d %d %d %d %d %d %d' %
                    (AC_ID, numsv, int(ecef_x), int(ecef_y), int(ecef_z), lat, lon, alt, hmsl, int(ecef_xd), int(ecef_yd), int(ecef_zd), tow, course
                    ))
	
    def IvySendINSBroadcast(self, AC_ID, copter_id, ins_x, ins_y, ins_z, ins_xd, ins_yd, ins_zd, ins_xdd, ins_ydd, ins_zdd):
        IvySendMsg('dl COPTER_INS %d %d %d %d %d %d %d %d %d %d %d' %
                    (AC_ID, copter_id, ins_x, ins_y, ins_z, ins_xd, ins_yd, ins_zd, ins_xdd, ins_ydd, ins_zdd
                    ))

    def IvySendGPSBroadcast(self, AC_ID, copter_id, gps_x, gps_y, gps_z, gps_xd, gps_yd, gps_zd):
        IvySendMsg('dl COPTER_GPS %d %d %d %d %d %d %d %d' %
                    (AC_ID, copter_id, gps_x, gps_y, gps_z, gps_xd, gps_yd, gps_zd
                    ))


    def IvySendUnKill(self, AC_ID):
        """Sends an unkill message to the aircraft

        """
        IvySendMsg('dl KILL %d 0' %
                    (AC_ID
                    ))



    def IvySendSwitchBlock(self, AC_ID, block_ID):
        """Sends a message to switch the flight plan

        """
        IvySendMsg('dl BLOCK %d %d' %
                    (block_ID,
                     AC_ID,
                     ))
                     
    def SaveIvyKillLog(self):
        self.myKillLog.saveLog()
