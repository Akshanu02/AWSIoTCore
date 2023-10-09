#!/usr/bin/python

# AWS IoT For Automotive - Device Shadows
# Make sure your host and region are correct.

import sys
import ssl
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient, AWSIoTMQTTClient
import json
import time
from random import randint

# Our vehicle is not currently moving.
CURRENT_SPEED = 0
VIN = "JACDJ58X527J08183"

ENDPOINT = "a24dapxtisvrk0-ats.iot.us-east-1.amazonaws.com"
CERT_FILEPATH = "certificate1.pem"
PRIVATE_KEY_FILEPATH="privatekey1.key"
ROOT_CA_FILEPATH="rootCA.pem"
#Setup our MQTT client and security certificates
#Make sure your certificate names match what you downloaded from AWS IoT

#Note we are use the Shadow Client here, rather than the regular AWSIoTMQTTClient.
mqttShadowClient = AWSIoTMQTTShadowClient(VIN)

#Use the endpoint from the settings page in the IoT console
mqttShadowClient.configureEndpoint(ENDPOINT,8883)
mqttShadowClient.configureCredentials(ROOT_CA_FILEPATH,PRIVATE_KEY_FILEPATH,CERT_FILEPATH)

#Set up the Shadow handlers
shadowClient=mqttShadowClient.createShadowHandlerWithName(VIN,True)

#We can retrieve the underlying MQTT connection from the Shadow client to make regular MQTT publish/subscribe
mqttClient = mqttShadowClient.getMQTTConnection()

def createDeviceClassicShadow():
    global shadowClient
    #Set the shadow with the current status and check if it was successful by calling the custom callback
    print("Creating Classic Shadow with latest vehicle status")
    shadowMessage = {"state":{"reported":{"status": "on","currentSpeed": "0","firmwareVersion": "1.0.23","subscription": "standard","latitude": "32.342043","longitude": "73.34304"}}}
    shadowMessage = json.dumps(shadowMessage)
    #UPDATE - Creates a shadow if it doesn't exist, or updates the contents of an existing shadow with the state information provided in the message body.
    shadowClient.shadowUpdate(shadowMessage, customShadowCallback_Update, 5)

# Custom Shadow callback for updating, checks if the update was successful.
def customShadowCallback_Update(payload, responseStatus, token):
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
    if responseStatus == "timeout":
        print("Update request " + token + " time out!")
    if responseStatus == "accepted":
        ##print(payload)
        data = json.loads(payload)
        state = data.get('state')
        reported = state.get('reported')
        currentSpeed = reported.get('currentSpeed')
        status = reported.get('status') 
        if status is not None:
            print("Classic Shadow updated successfully")
        elif currentSpeed is not None:
            print("Current Speed successfully updated in Device Shadow to: " + str(currentSpeed))
    if responseStatus == "rejected":
        print("Update request " + token + " rejected!")
        
#Function to encode a payload into JSON
def json_encode(string):
        return json.dumps(string)

mqttClient.json_encode=json_encode

#This sends a speed update message to the shadow topic, 
def sendUpdate():
    global SPEED
    speed = randint(0, 100)

    shadowMessage = {"state":{"reported":{"currentSpeed": speed}}}
    shadowMessage = json.dumps(shadowMessage)
    #UPDATE - Creates a shadow if it doesn't exist, or updates the contents of an existing shadow with the state information provided in the message body.
    shadowClient.shadowUpdate(shadowMessage, customShadowCallback_Update, 5)

    print("Speed Update Message Published to Classic Shadow")

#Connect to the gateway
mqttShadowClient.connect()
print("Connected")

#Set the initial engine status in the device shadow
createDeviceClassicShadow()

time.sleep(5)
    
#Loop until terminated
while True:
    sendUpdate()
    time.sleep(5)

mqttShadowClient.disconnect()


