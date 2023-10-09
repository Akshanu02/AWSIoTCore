#!/usr/bin/python

# AWS IoT For Automotive - Device Shadows
# Make sure your host and region are correct.

import sys
import ssl
from awscrt import mqtt
from awsiot import iotshadow
from awsiot import mqtt_connection_builder
import json
import time
from random import randint
from uuid import uuid4

# Our vehicle is not currently moving.
CURRENT_SPEED = 0
VIN = "<REPLACE>"
SHADOW_THING_NAME = "BCM-39870"
shadow_client = None
shadow_property = "engine_status"
ENDPOINT = "<REPLACE>-ats.iot.us-east-1.amazonaws.com"
CERT_FILEPATH = "certificate.pem"
PRIVATE_KEY_FILEPATH="privateKey.key"
ROOT_CA_FILEPATH="rootCA.pem"
#Setup our MQTT client and security certificates
#Make sure your certificate names match what you downloaded from AWS IoT

#Note we are use the Shadow Client here, rather than the regular AWSIoTMQTTClient.

mqtt_connection = mqtt_connection_builder.mtls_from_path(
    endpoint= ENDPOINT,
    port=8883,
    cert_filepath=CERT_FILEPATH,
    pri_key_filepath=PRIVATE_KEY_FILEPATH,
    ca_filepath=ROOT_CA_FILEPATH,
    client_id=VIN,
    clean_session=False,
    keep_alive_secs=60)
            

def on_update_named_shadow_accepted(response):
    # type: (iotshadow.UpdateShadowResponse) -> None
    try:
        if response.state.reported != None:
            if shadow_property in response.state.reported:
                print("Finished updating reported shadow value to '{}'.".format(response.state.reported[shadow_property])) # type: ignore
            else:
                print ("Could not find shadow property with name: '{}'.".format(shadow_property)) # type: ignore
        else:
            print("Shadow states cleared.") # when the shadow states are cleared, reported and desired are set to None
    except:
        exit("Updated shadow is missing the target property")

def on_update_named_shadow_rejected(error):
    try:
        exit("Update request was rejected. code:{} message:'{}'".format(
            error.code, error.message))

    except Exception as e:
        exit(e)


def on_get_named_shadow_accepted(response):
    # type: (iotshadow.GetShadowResponse) -> None
    try:

        if response.state:
            if response.state.delta:
                value = response.state.delta.get(shadow_property)
                if value:
                    print("  Shadow contains delta value '{}'.".format(value))
                    #change_shadow_value(value)
                    return

            if response.state.reported:
                value = response.state.reported.get(shadow_property)
                if value:
                    print("  Shadow contains reported value of '{}' to '{}'.".format(shadow_property, value))
                    print("  Named shadow reported status values are '{}".format(response.state.reported))
                    return

        print("  Shadow document lacks '{}' property. Setting defaults...".format(shadow_property))
        #change_shadow_value(SHADOW_VALUE_DEFAULT)
        return

    except Exception as e:
        exit(e)

def on_get_named_shadow_rejected(error):
    try:
        exit("Update request was rejected. code:{} message:'{}'".format(
            error.code, error.message))

    except Exception as e:
        exit(e)

def delta_accepted(delta):
    try:
        print("Received shadow delta event.")
        if delta.state and (shadow_property in delta.state):
            value = delta.state[shadow_property]
            if value is None:
                print("  Delta reports that '{}' was deleted. Resetting defaults...".format(shadow_property))
                #change_shadow_value(SHADOW_VALUE_DEFAULT)
                return
            else:
                print("  Delta reports that desired value is '{}'. Changing local value...".format(value))
                #if (delta.client_token is not None):
                #    print ("  ClientToken is: " + delta.client_token)
                changeNamedShadowValue(value)
        else:
            print("  Delta did not report a change in '{}'".format(shadow_property))

    except Exception as e:
        exit(e)

        
def getDeviceNamedShadow():
    try:
        global shadow_client
        print("Getting Named Shadow with attributes for the Body Control Module")
        token = str(uuid4())
        get_accepted_named_subscribed_future = shadow_client.publish_get_named_shadow(
                request=iotshadow.GetNamedShadowRequest(thing_name=VIN, shadow_name=SHADOW_THING_NAME,client_token=token),
                qos=mqtt.QoS.AT_LEAST_ONCE)

        get_accepted_named_subscribed_future.result()

    except Exception as e:
        print('Error')
        exit(e)   
        
def updateDeviceNamedShadow(state):
    try:
        #Set the shadow with the current status and check if it was successful by calling the custom callback
        print("Updating Named Shadow with attributes for the Body Control Module")
        token = str(uuid4())
        update_accepted_subscribed_future = shadow_client.publish_update_named_shadow(
                request=iotshadow.UpdateNamedShadowRequest(thing_name=VIN, shadow_name=SHADOW_THING_NAME,state=state,client_token=token),
                qos=mqtt.QoS.AT_LEAST_ONCE)
                
        update_accepted_subscribed_future.result()
        update_accepted_subscribed_future.add_done_callback(on_publish_update_shadow)
    except Exception as e:
        print('Error')
        exit(e)   
        
def on_publish_update_shadow(future):
    #type: (Future) -> None
    try:
        future.result()
        print("Update request published.")
    except Exception as e:
        print("Failed to publish update request.")
        exit(e)
        
def changeNamedShadowValue(value):

    print("Changed local shadow value to '{}'.".format(value))

    print("Updating reported shadow value to '{}'...".format(value))

    # use a unique token so we can correlate this "request" message to
    # any "response" messages received on the /accepted and /rejected topics
    token = str(uuid4())

    # if the value is "clear shadow" then send a UpdateShadowRequest with None
    # for both reported and desired to clear the shadow document completely.
    if value == "clear_shadow":
        tmp_state = iotshadow.ShadowState(reported=None, desired=None, reported_is_nullable=True, desired_is_nullable=True)
        updateDeviceNamedShadow(tmp_state)
    # Otherwise, send a normal update request
    else:
        # if the value is "none" then set it to a Python none object to
        # clear the individual shadow property
        if value == "none":
            value = None

        state=iotshadow.ShadowState(
            reported={ shadow_property: value },
            desired={ shadow_property: value },
            )
        
        request = iotshadow.UpdateNamedShadowRequest(
            thing_name=VIN,
            shadow_name=SHADOW_THING_NAME,
            state=iotshadow.ShadowState(
                reported={ shadow_property: value },
                desired={ shadow_property: None },
                ),
                client_token=token,
            )

        future = shadow_client.publish_update_named_shadow(request, mqtt.QoS.AT_LEAST_ONCE)

        future.add_done_callback(on_publish_update_shadow)
  
#Function to encode a payload into JSON
def json_encode(string):
        return json.dumps(string)

#Connect to the gateway
connected_future = mqtt_connection.connect()

shadow_client = iotshadow.IotShadowClient(mqtt_connection)

# Wait for connection to be fully established.
# Note that it's not necessary to wait, commands issued to the
# mqtt_connection before its fully connected will simply be queued.
# But this sample waits here so it's obvious when a connection
# fails or succeeds.
connected_future.result()
print("Connected!")

try:
    # Subscribe to necessary topics.
    # Note that is **is** important to wait for "accepted/rejected" subscriptions
    # to succeed before publishing the corresponding "request".
    print("Subscribing to Get Accepted responses...")
    get_accepted_subscribed_future, _ = shadow_client.subscribe_to_get_named_shadow_accepted(
        request=iotshadow.GetNamedShadowSubscriptionRequest(thing_name=VIN,shadow_name=SHADOW_THING_NAME),
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_get_named_shadow_accepted)
    
    print("Subscribing to Get Rejected responses...")
    get_rejected_subscribed_future, _ = shadow_client.subscribe_to_get_named_shadow_rejected(
        request=iotshadow.GetNamedShadowSubscriptionRequest(thing_name=VIN,shadow_name=SHADOW_THING_NAME),
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_get_named_shadow_rejected)
        
    print("Subscribing to Update Accepted responses...")
    update_accepted_subscribed_future, _ = shadow_client.subscribe_to_update_named_shadow_accepted(
        request=iotshadow.NamedShadowUpdatedSubscriptionRequest(thing_name=VIN,shadow_name=SHADOW_THING_NAME),
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_update_named_shadow_accepted)

    print("Subscribing to Update Rejected responses...")
    update_rejected_subscribed_future, _ = shadow_client.subscribe_to_update_named_shadow_rejected(
        request=iotshadow.NamedShadowUpdatedSubscriptionRequest(thing_name=VIN,shadow_name=SHADOW_THING_NAME),
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_update_named_shadow_rejected)
    
    print("Subscribing to Delta responses...")
    delta_subscribed_future, _ = shadow_client.subscribe_to_named_shadow_delta_updated_events(
        request=iotshadow.NamedShadowDeltaUpdatedSubscriptionRequest(thing_name=VIN,shadow_name=SHADOW_THING_NAME),
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=delta_accepted)
        
    # Wait for subscriptions to succeed
    get_accepted_subscribed_future.result()
    get_rejected_subscribed_future.result()
    update_accepted_subscribed_future.result()
    update_rejected_subscribed_future.result()
    delta_subscribed_future.result()
    
except Exception as e:
    exit(e)

original_state=iotshadow.ShadowState(
    reported={ "engine_status": "off","driverWindow": "up","passengerWindow": "up","driverDoor": "locked","passengerDoor": "locked","driverSeat": "off","passengerSeat": "heat"},
    desired=None, desired_is_nullable=True, delta=None, delta_is_nallable=True
)

#To check and see if your message was published to the message broker go to the MQTT Client and subscribe to the iot topic and you should see your JSON Payload

changeNamedShadowValue("clear_shadow")
updateDeviceNamedShadow(original_state)

#getDeviceNamedShadow()
#this will simulate a remote command to change desired engine status to ON, which will create a response on the Delta topic
#print("  Updating desired engine_status value to 'on'")
#state=iotshadow.ShadowState(
#    desired={ "engine_status": "on" },
#)
#updateDeviceNamedShadow(state)
#print("  Updating reported engine_status value to 'on'")
#state=iotshadow.ShadowState(
#    reported={ "engine_status": "on" },
#    desired=None, desired_is_nullable=True
#)
#updateDeviceNamedShadow(state)

#print (" Return shadow back to original state")

#updateDeviceNamedShadow(original_state)

while True:
    #sendUpdate()
    time.sleep(5)

print (" Completed")
mqtt_connection.disconnect()

#
