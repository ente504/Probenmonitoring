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
                print("PW set")
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


    def publish(self, topic, data):
        """
        This method publishes Data in an provided Topic on the specified Broker.
        :param topic: Topic to publish th Data in String format
        :param data: Data that should be published.
        :return: retuns published Data
        """

        try:
            self.mqtt_client.publish(topic, data)
        except:
            logging.ERROR("Error while publishing Data to the mqtt broker")
        return data


#class end