'''
/*
 * Copyright 2010-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *  http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */
 '''

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import logging
import time
import argparse
import json
import requests

AllowedActions = ['both', 'publish', 'subscribe']

# Custom MQTT message callback
def customCallback(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")
    
    # try:
    with open(test_file, 'r') as object_file:
        object_text = object_file.read()
    response = requests.put(message.payload, data=object_text)
    print("Finished large file put with:")
    print(response)
    # except FileNotFoundError:
    #     print(f"Couldn't find {args.key}. For a PUT operation, the key must be the "f" name of a file that exists on your computer.")


host = "a24dapxtisvrk0-ats.iot.us-east-1.amazonaws.com" #Change to your account endpoint
rootCAPath = './rootCA.pem'
certificatePath = './certificate1.pem'
privateKeyPath = './privatekey1.key'
clientId = 'JACDJ58X527J08183' #This can be changed to your sample VIN (optional)
topic = 'data/'+clientId+'/payload/url/get'
port = 8883
test_file = './testfile.txt' #Modify the path to match your test file
test_file_name = 'testfile.txt' #Modify the filename for the file that will be written to S3 (optional)

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)


myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
myAWSIoTMQTTClient.configureEndpoint(host, port)
myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()
myAWSIoTMQTTClient.subscribe(topic+'/accepted', 1, customCallback)
time.sleep(2)

# Publish the filename and wait for a message on the subscription
message = {}
message['message'] = test_file_name
messageJson = json.dumps(message)
myAWSIoTMQTTClient.publish(topic, messageJson, 1)
print('Published topic %s: %s\n' % (topic, messageJson))
while True:
    time.sleep(30)
