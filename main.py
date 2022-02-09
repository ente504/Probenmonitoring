# !/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Revision: @ente504
# 0.0.1: Initial version


from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, QCoreApplication

from t_temphumsensor import TempHumSensor
from t_SpecimenRegistration import MqttSubscriber
from t_publishData import MqttPublisher
import lcddriver
import logging
import time
import random
import configparser
import sys
import csv
import json
import paho.mqtt.client as mqtt

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget)

# TODO: write Misstake detection procedure

def convert_str_to_list(datastring):
    """
    :param datastring: string that should be converted to a List. Separation when the element ", " (with space) is found.
    :return: the input data string is returned as a List element. Additional all found "None" Strings are converted
    Type 2D     to the python None Element.
    """
    data_list = datastring.split(", ")

    for index, value in enumerate(data_list):
        if value == "None":
            data_list[index] = None
    return data_list


def randomize_dataframe(dataframe):
    """
    :param dataframe: takes the Dataframe  Dataframe
    :return: returns modified Dataframe
    method is for debugging and test purposes. It simulates Sensor Data input in form of randomized Data
    """
    dataframe[1][1] = str(random.randint(10, 30))
    dataframe[1][2] = str(round(random.uniform(0.1, 1), 2))
    return dataframe


def build_json(dataframe):
    """
    :param dataframe: takes the 2D Array SpecimenDataframe
    :return: json string build output of the provided Dataframe
    """
    data_set = {}
    json_dump = ""
    dataframe_length = int(len(dataframe[1]))

    if len(dataframe[0]) == len(dataframe[1]):
        for x in range(0, dataframe_length):
            if dataframe[1][x] not in ["", " ", None]:
                key = str(dataframe[0][x])
                value = str(dataframe[1][x])
                data_set[key] = [value]

            json_dump = json.dumps(data_set)
    else:
        logging.error("Error while transforming list into json String")

    return json_dump


def init_csv(top_line_content):
    with open('temp_hum_log.csv', 'a', newline='') as log_file:
        writer = csv.writer(log_file)
        writer.writerow(top_line_content)


def update_csv(content):
    with open('temp_hum_log.csv', 'a', newline='') as log_file:
        writer = csv.writer(log_file)
        writer.writerow(content)
        print(content)


"""
Variable declarations:
load variables from the config file using ConfigParser.
The config file needs to be locate in the root Folder of the program.
"""

CONFIG_FILE = "config.ini"
config = configparser.ConfigParser()
config.read(CONFIG_FILE)

DeviceName = str(config["GENERAL"]["DeviceName"])
DeviceType = int(config["GENERAL"]["DeviceType"])
Interval = int(config["GENERAL"]["Interval"])
SpecimenNameString = config["DATA"]["SpecimenNameList"]
SpecimenDataString = config["DATA"]["SpecimenDefaultData"]
broker = str(config["MQTT"]["Broker"])
port = int(config["MQTT"]["Port"])
username = str(config["MQTT"]["UserName"])
passkey = str(config["MQTT"]["PassKey"])
BaseTopic = str(config["MQTT"]["BaseTopic"])

"""
construct SpecimenDataFrame:
The Specimen Dataframe contains the relevant Data
The contained Data in this Dataframe is of Type String
The order of the Elements is to be respected 0 to 6
SpecimenDataFrame = [PKID, STID, Temp, Humidity, Weight, Measurement 1, Measurement 2, Measurement 3]
The Names are taken from the SpecimenNameFrame
"""

SpecimenNameList = convert_str_to_list(SpecimenNameString)
SpecimenDataList = convert_str_to_list(SpecimenDataString)
SpecimenDataFrame = [SpecimenNameList, SpecimenDataList]

# initialize logging
logging.basicConfig(filename="probenmonitoring.log", filemode="w", level=logging.DEBUG)

# initialize LCD Display
lcd_display = lcddriver.lcd()


class ConsoleWorkerSensor(QObject):
    """
    this class is for packing the signal handling methods and the running progress of the basic application
    in a QObject frame to take part in the QApplication EventLoop.
    """

    LCD_Display_String = "T:      H:     "

    @staticmethod
    def replace_substring_between_index(single_line, string_to_replace, start_pos, end_pos):
        """
        this method is for updating the temperature and humidity Data in the LCD_Display_String
        for display on the LCD display.
        :param single_line: input string
        :param string_to_replace: string that should replace part of the input string
        :param start_pos: insert start position
        :param end_pos: insert end position
        :return: returns the input string with the patched in replacement String
        """
        try:
            single_line = single_line[:start_pos] + string_to_replace + single_line[end_pos:]
        except Exception as e:
            exception = "There is Exception at this step while calling replace_str_index method, Reason = " + str(e)
        return single_line

    @staticmethod
    def handle_temp_signal(temperature):
        """
        receives the Signal with the Temperature Information from the Sensor Thread and
        positions it in the corresponding slot in the Dataframe.
        :param temperature: Temperature receives from the Sensor Thread as String
        """
        # console output
        print("\nTemperature: %0.1f C" % float(temperature))
        # LCD display output
        ConsoleWorkerSensor.LCD_Display_String = ConsoleWorkerSensor.replace_substring_between_index(
            ConsoleWorkerSensor.LCD_Display_String,
            "%0.2f" % float(temperature),
            2,
            7)
        lcd_display.lcd_display_string(ConsoleWorkerSensor.LCD_Display_String, 2)

        # update SpecimenDataframe
        entry_found = False
        i = 0

        # find right slot in the SpecimenDataframe
        while not entry_found:
            if SpecimenDataFrame[0][i] == "Temp":
                SpecimenDataFrame[1][i] = float(temperature)
                entry_found = True
            if i == len(SpecimenDataFrame[0]) and entry_found is False:
                print("no category Temp was found in the SpecimenDataframe. please check config.ini\n")
                entry_found = False
            i += 1

    @staticmethod
    def handle_humid_signal(humidity):
        """
        resives the Signal with the humidity Information from the Sensor Thread and
        positions it in the corresponding slot in the Dataframe.
        :param: temperature: Humidity relieved from the Sensor Thread as String.
        """

        # console output
        print("Humidity: %0.1f %%" % float(humidity))

        # LCD display output
        ConsoleWorkerSensor.LCD_Display_String = ConsoleWorkerSensor.replace_substring_between_index(
            ConsoleWorkerSensor.LCD_Display_String,
            "%0.2f" % float(humidity),
            10,
            15)
        lcd_display.lcd_display_string(ConsoleWorkerSensor.LCD_Display_String, 2)

        # update SpecimenDataframe
        entry_found = False
        i = 0

        # find right slot in the SpecimenDataframe
        while not entry_found:
            if SpecimenDataFrame[0][i] == "Humidity":
                SpecimenDataFrame[1][i] = float(humidity)
                entry_found = True
            if i == len(SpecimenDataFrame[0]) and entry_found is False:
                print("no category Temp was found in the SpecimenDataframe. Please check config.ini\n")
                entry_found = False
            i += 1

    @staticmethod
    def handle_heater_signal():
        print("heater started\n")

    def run_measuring_thread(self):

        # init of the Tread class Object
        self.sensor = TempHumSensor(wait_time=Interval, heater_status=True, heater_interval=10)
        # connect signals to worker Methods
        self.sensor.finished.connect(self.sensor.quit)
        self.sensor.finished.connect(self.sensor.deleteLater)
        self.sensor.Temperature_Signal.connect(self.handle_temp_signal)
        self.sensor.relative_Humidity_Signal.connect(self.handle_humid_signal)
        self.sensor.Heater_Signal.connect(self.handle_heater_signal)
        # run Thread Object
        self.sensor.start()


class ConsoleWorkerSpecimenRegistration(QObject):
    """
    class to start the watcher Thread for receiving new PKIDs
    and handling PKIDs.
    """

    @staticmethod
    def handle_new_pkid_signal(pkid):
        """
        The method checks if the with the pyQt received PKID is a new or an old ID.
        It either checks the Specimen in or out.
        :param pkid: pkid type String transferred Data from th pyQt Signal
        :return: returns pkid as String
        """

        old_pkid = SpecimenDataFrame[1][0]
        new_pkid = pkid

        if old_pkid == new_pkid:
            SpecimenDataFrame[1][0] = None
            print("PKID " + old_pkid + " has been checked out.")
            lcd_display.lcd_display_string("                ", 1)
            lcd_display.lcd_display_string("PKID: " + str(SpecimenDataFrame[1][0]), 1)
            logging.info("PKID " + old_pkid + " has been checked out.")

        if old_pkid != new_pkid:
            SpecimenDataFrame[1][0] = new_pkid
            print("PKID " + new_pkid + " has been checked in.")
            lcd_display.lcd_display_string("                ", 1)
            lcd_display.lcd_display_string("PKID: " + str(SpecimenDataFrame[1][0]), 1)
            logging.info("PKID " + new_pkid + " has been checked in.")

        return new_pkid

    def run_specimen_registration_thread(self):
        
        topic = str(SpecimenDataFrame[1][1] + "/PKID")
        self.Client = MqttSubscriber(SpecimenDataFrame[1][1], broker, port, username, passkey, topic)
        # connect signals to worker methods
        self.Client.finished.connect(self.Client.quit)
        self.Client.finished.connect(self.Client.deleteLater)
        self.Client.new_PKID_Signal.connect(self.handle_new_pkid_signal)
        # run thread Object
        self.Client.start()


# TODO: Move this shit to on thread script.
class PublishData(QThread):
    """
    Thread class for continuously publishing the updated specimenDataframe
    to the MQTT Broker
    """

    @pyqtSlot()
    def run(self):
        self.Client = MqttPublisher(DeviceName, broker, port, username, passkey)

        while True:
            if str(SpecimenDataFrame[1][0]) not in ["", " ", "none", "None", "False", "false"]:
                self.Client.publish(BaseTopic, build_json(SpecimenDataFrame))
            time.sleep(Interval+1)


class OnlineMessenger(QThread):
    """
    class for emitting messages on MQTT for the Android App to recognise the online status of the
    climate Station
    """

    def __init__(self, client_name, mqtt_broker, mqtt_port, mqtt_username, mqtt_passkey, mqtt_topic):
        """
        :param client_name: Name for the mqtt client Type: str
        :param mqtt_broker: ip or url of the mqtt broker Type: str
        :param mqtt_port: port of the mqtt broker Type:int
        :param mqtt_username: User to log on mqtt broker Type:str
        :param mqtt_passkey: Passkey to log on mqtt broker Type:str
        :param nameframe: Corresponding names for the Data stored in the Specimen Dataframe
        """
        #asign variables
        super().__init__()
        self.Client_Name = client_name
        self.mqtt_Broker = mqtt_broker
        self.mqtt_Port = mqtt_port
        self.mqtt_Username = mqtt_username
        self.mqtt_Passkey = mqtt_passkey
        self.mqtt_Topic = mqtt_topic
        self.running = True

        try:
            # setup mqtt client
            self.mqtt_client = mqtt.Client(self.Client_Name)

            # set up last will and testament
            lwt_topic = str(SpecimenDataFrame[1][1]) + "/online"
            self.mqtt_client.will_set(lwt_topic, payload="False", qos=0, retain=False)

            if self.mqtt_Username not in ["", " ", None] or self.mqtt_Passkey not in ["", " ", None]:
                self.mqtt_client.username_pw_set(self.mqtt_Username, self.mqtt_Passkey)
            else:
                logging.info("the server is not using a User authentication")

            self.mqtt_client.on_connect = self.on_connect
            self.mqtt_client.on_publish = self.on_publish
            self.mqtt_client.connect(mqtt_broker, mqtt_port)

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

    def on_publish(self, client, userdata, result):
        logging.info("data published")

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
            logging.error("Error while publishing Data to the mqtt broker")
        return data

    @pyqtSlot()
    def run(self):
        while self.running:
            self.publish(self.mqtt_Topic, "True")
            time.sleep(1)

    @pyqtSlot()
    def stop(self):
        self.running = False
        print('Stopping thread...')
        self.terminate()


class ConsoleWorkerPublish(QObject):
    """
    worker Object to  for continuously publishing the updated specimenDataframe
    see: class PublishData(QThread)
    """
    def start_communication_tread(self):
        self.Communicator = PublishData()
        self.Communicator.start()


class ConsoleWorkerOnlineMessenger(QObject):
    """
    worker Object to  for continuously publishing the "Device online" Message on MQTT
    see: class OnlineMessenger(QThread)
    """
    def run_online_messenger(self):
        clientname = SpecimenDataFrame[1][1] + "_status"
        topic = str(SpecimenDataFrame[1][1]) + "/online"

        self.Client = OnlineMessenger(clientname, broker, port, username, passkey, topic)
        # connect signals to worker methods
        self.Client.finished.connect(self.Client.quit)
        self.Client.finished.connect(self.Client.deleteLater)
        # run thread Object
        self.Client.start()




# main program
if __name__ == "__main__":

    if DeviceType == 1:
        # start the pyQT runtime Environment
        app = QCoreApplication(sys.argv)

        #show Default LCD Display
        lcd_display.lcd_clear()
        lcd_display.lcd_display_string("PKID: " + str(SpecimenDataFrame[1][0]), 1)

        # start online Messenger in a separate thread
        cwom = ConsoleWorkerOnlineMessenger()
        cwom.run_online_messenger()

        # start the Climate measuring in a separate thread
        cws = ConsoleWorkerSensor()
        cws.run_measuring_thread()

        # start the MQTT publisher in a separate thread
        cwp = ConsoleWorkerPublish()
        cwp.start_communication_tread()

        # start the specimen registration thread
        cwsr = ConsoleWorkerSpecimenRegistration()
        cwsr.run_specimen_registration_thread()

        sys.exit(app.exec())

    # followed by other IF closes for other Device Types