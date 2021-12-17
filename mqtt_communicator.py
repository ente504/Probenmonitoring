# !/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Revision: @ente504
# 0.0.1: Initial version


import paho.mqtt.client as mqtt
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from t_temphumsensor import TempHumSensor
import logging
import time
import random
import configparser
import shlex

#TODO:Publish json


class MqttPublisher:
    def __init__(self, client_name, mqtt_broker, mqtt_port, mqtt_username, mqtt_passkey):
        """
        :param client_name: Name for the mqtt client Type: str
        :param mqtt_broker: ip or url of the mqtt broker Type: str
        :param mqtt_port: port of the mqtt broker Type:int
        :param mqtt_username: User to log on mqtt broker Type:str
        :param mqtt_passkey: Passkey to log on mqtt broker Type:str
        :param nameframe: Corresponding names for the Data stored in the Specimen Dataframe
        """
        #asign variables
        self.Client_Name = client_name
        self.mqtt_Broker = mqtt_broker
        self.mqtt_Port = mqtt_port
        self.mqtt_Username = mqtt_username
        self.mqtt_Passkey = mqtt_passkey

        try:
            #setup mqtt client
            self.mqtt_client = mqtt.Client(self.Client_Name)

            if self.mqtt_Username not in ["", " ", None]  or self.mqtt_Passkey not in ["", " ", None]:
                self.mqtt_client.username_pw_set(self.mqtt_Username, self.mqtt_Passkey)
            else:
                logging.info("the server is not using a User authentication")

            self.mqtt_client.on_connect = self.on_connect
            self.mqtt_client.on_publish = self.on_publish
            self.mqtt_client.connect(mqtt_broker, mqtt_port)
        except:
            print("no connection to the mqtt broker")

    def return_Client_Name(self):
        return self.Client_Name

    def return_mqtt_Broker(self):
        return self.mqtt_Broker

    def return_mqtt_Port(self):
        return self.mqtt_Port

    def return_mqtt_Username(self):
        return self.mqtt_Username

    def return_mqtt_Passkey(self):
        return self.mqtt_Passkey

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            client.connected_flag = True
            print("connected OK")
            logging.info("connected OK, Server: " + self.mqtt_Broker + ":" + self.mqtt_Port + " username: "
                         + self.mqtt_Username + " Passkey: " + self.mqtt_Passkey)
        else:
            print("Bad connection Returned code=", rc)
            logging.ERROR("Bad connection Returned code= " + rc + " " + self.mqtt_Broker + ":" + self.mqtt_Port +
                          " username: " + self.mqtt_Username + " Passkey: " + self.mqtt_Passkey)

    def on_publish(self, client, userdata, result):
        print("data published \n")
        logging.info("data published")
        pass

    def publish_data(self, dataframe):
        """
        :param dataframe: Takes the Dataframe with the Specimen Data to publish via mqtt
        :return: retuns the actually published Data as a list of String.

        method goes throw the Dataframe and publishes each measurement not None to the corresponding Topic under the
        Topic of the PKID transfeared in the Dataframe
        """
        published_dataframe = []
        if len(dataframe[0]) == len(dataframe[1]):

            if dataframe[1][0] not in ["", " "]:
                pkid = str(dataframe[1][0])
                dataframe_length = int(len(dataframe[1]))

                for x in range(1, dataframe_length):
                    if dataframe[1][x] not in ["", " ", None]:
                        mqtt_Topic = str(pkid + "/" + str(dataframe[0][x]))
                        published_dataframe.append(dataframe[0][x] + " " + dataframe[1][x])
                        try:
                            self.mqtt_client.publish(mqtt_Topic, str(dataframe[1][x]))
                        except:
                            logging.info("Error while publishing Data to the mqtt broker")
            else:
                logging.ERROR("no PKID defined! Was not able to publish Information")
        else:
            logging.ERROR("not all elements of the SpecimenDataFrame are named. Check the SpecimenNameFrame!")
        return published_dataframe


#class end

class MqttSubscriber:
    """
    class for retriving control signals via MQTT
    (check in an out of Specimen und mobile climat messurment stations via android app)
    """

    def __init__(self, client_name, mqtt_broker, mqtt_port, mqtt_username, mqtt_passkey, mqtt_topic):

        self.Client_Name = client_name
        self.mqtt_Broker = mqtt_broker
        self.mqtt_Port = mqtt_port
        self.mqtt_Username = mqtt_username
        self.mqtt_Passkey = mqtt_passkey
        self.mqtt_Topic = mqtt_topic

        #configure mqtt client
        client = mqtt.Client(self.Client_Name)
        client.connect(self.mqtt_Broker)
        client.subscribe(self.mqtt_Topic)
        client.on_message = on_message
        client.on_connect = on_connect


#TODO: implement the subscriber class in qThread an emmit a signal for handling the PKID resivment

    def on_message(client, userdata, message):
        print("received message: ", str(message.payload.decode("utf-8")))
        #TODO: emitte signal to mainthread

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("connected OK Returned code=", rc)
        else:
            print("Bad connection Returned code=", rc)

    def run(self):
        while True:
            # clint needs to run in a loop
            client.loop_start()
            client.on_message = on_message
            time.sleep(1)
            client.loop_stop()