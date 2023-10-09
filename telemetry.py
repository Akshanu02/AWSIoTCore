#!/usr/bin/python

# AWS IoT For Automotive - Setting up.
# Make sure your host and region are correct.
import sys
import ssl
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import json
import time
import datetime
import csv
import uuid

VIN = "JACDJ58X527J08183" ##This is your Thing name
ENDPOINT = "a24dapxtisvrk0-ats.iot.us-east-1.amazonaws.com"
CERT_FILEPATH = "certificate1.pem"
PRIVATE_KEY_FILEPATH="privatekey1.key"
ROOT_CA_FILEPATH="rootCA.pem"
#Setup our MQTT client and security certificates
#Make sure your certificate names match what you downloaded from AWS IoT

mqttc = AWSIoTMQTTClient(VIN)

#Make sure you use the correct region!
mqttc.configureEndpoint(ENDPOINT,8883)
mqttc.configureCredentials(ROOT_CA_FILEPATH,PRIVATE_KEY_FILEPATH,CERT_FILEPATH)

#Connect to the gateway
mqttc.connect()
print("Connected")

#Function to encode a payload into JSON
def json_encode(string):
    return json.dumps(string)

mqttc.json_encode=json_encode

#Declaring our variables
message ={
    "MessageId": "",
    "SimulationId": "",
    "CreationTimeStamp": "",
    "SendTimeStamp": "",
    "VIN": "",
    "TripId": "",
    "Latitude": 0,
    "Longitude": 0,
    "Heading": 0,
    "Speed": 0,
    "BatteryVoltage": 0,
    "Name": "CRtdESVEf",
    "BatterySOC": 0
  }

simId = uuid.uuid4().hex
tripId = uuid.uuid4().hex
ts =datetime.datetime.now().timestamp()

def main():
    publish_topic = "$aws/rules/IoTForAutoWorkshop/JACDJ58X527J08183".replace("JACDJ58X527J08183", VIN)
    array = json.dumps(message)
    data = json.loads(array)
    data["SimulationId"]= simId
    data["CreationTimeStamp"]= ts
    data["VIN"]= VIN
    data["TripId"] = tripId
    
    with open('latLong2.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for line in reader:
            #print index wise
            print(line[0], line[1])
            data["MessageId"] = VIN + "-" + str(datetime.datetime.now().timestamp())
            data["Latitude"] = float(line[1])
            data["Longitude"] = float(line[2])
            data["Heading"] = float(line[3])
            data["Speed"] = float(line[4])
           #data["BatteryVoltage"] = float(line[4])
            data["BatterySOC"] = float(line[5])
            messageFinal = mqttc.json_encode(data)
            #This sends our test message to the iot topic
            mqttc.publish(publish_topic, messageFinal, 0)
            print("Message Published to <topic>".replace("<topic>", publish_topic))
            #To check and see if your message was published to the message broker go to the MQTT Client and subscribe to the iot topic and you should see your JSON Payload
            time.sleep(3)
        #Loop until EOF
        mqttc.disconnect()

if __name__ == "__main__":
    main()

