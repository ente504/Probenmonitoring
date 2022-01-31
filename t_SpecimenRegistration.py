# !/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Revision: @ente504
# 0.0.1: Initial version


import paho.mqtt.client as mqtt
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
import logging
import time


class MqttSubscriber(QThread):
    """
    This class handles the registration of the Specimen via MQTT.
    (check in and check out of Specimen on mobile climate measurement stations via android app)
    """
    # initialize logging
    logging.basicConfig(filename="probenmonitoring.log", filemode="w", level=logging.DEBUG)

    # Signals
    new_PKID_Signal = pyqtSignal(str, name="new_PKID_Signal")

    def __init__(self, client_name, mqtt_broker, mqtt_port, mqtt_username, mqtt_passkey, mqtt_topic):

        super().__init__()
        self.Client_Name = client_name
        self.mqtt_Broker = mqtt_broker
        self.mqtt_Port = mqtt_port
        self.mqtt_Username = mqtt_username
        self.mqtt_Passkey = mqtt_passkey
        self.mqtt_Topic = mqtt_topic
        self.is_running = True

        # configure mqtt client
        try:
            self.mqtt_client = mqtt.Client()
            if self.mqtt_Username not in ["", " ", None] or self.mqtt_Passkey not in ["", " ", None]:
                self.mqtt_client.username_pw_set(self.mqtt_Username, self.mqtt_Passkey)
            else:
                logging.info("the server is not using a User authentication")

            self.mqtt_client.connect(self.mqtt_Broker)
            self.mqtt_client.subscribe(self.mqtt_Topic)

        except:
            print("no connection to the mqtt broker")
            logging.error("no connection to the mqtt broker")

    def return_client_name(self):
        return self.Client_Name

    def return_mqtt_broker(self):
        return self.mqtt_Broker

    def return_mqtt_port(self):
        return self.mqtt_Port

    def return_mqtt_username(self):
        return self.mqtt_Username

    def return_mqtt_passkey(self):
        return self.mqtt_Passkey

    def on_message(self, client, userdata, message):
        print("received message: ", str(message.payload.decode("utf-8")) + "\n")
        self.new_PKID_Signal.emit(str(message.payload.decode("utf-8")))

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            client.connected_flag = True
            print("connected OK")
            logging.info("connected OK, Server: " + self.mqtt_Broker + ":" + self.mqtt_Port + " username: "
                         + self.mqtt_Username + " Passkey: " + self.mqtt_Passkey)
        else:
            print("Bad connection Returned code=", rc)
            logging.error("Bad connection Returned code= " + rc + " " + self.mqtt_Broker + ":" + self.mqtt_Port +
                          " username: " + self.mqtt_Username + " Passkey: " + self.mqtt_Passkey)

    @pyqtSlot(str)
    def stop(self):
        self.is_running = False
        print('Stopping thread...')
        self.terminate()

    @pyqtSlot(str)
    def run(self):
        while True:
            # client needs to run in a loop
            self.mqtt_client.loop_start()
            self.mqtt_client.on_message = self.on_message
            time.sleep(1)
            self.mqtt_client.loop_stop()