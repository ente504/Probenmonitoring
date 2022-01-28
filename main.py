# !/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Revision: @ente504
# 0.0.1: Initial version


from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, QCoreApplication

from t_temphumsensor import TempHumSensor
from mqtt_communicator import MqttPublisher
import logging
import time
import random
import configparser
import sys
import csv
import json
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget)


def convert_str_to_list(datastring):
    """
    :param datastring: string that shoud be counerted to a List. Seperation whenn the elemen ", " (with space) is found.
    :return: the input datastring is returnd as a List element. Additionaly all found "None" Strings are converted
    Type 2D     to the python None Element.
    """
    DataList = datastring.split(", ")

    for index, value in enumerate(DataList):
        if value == "None":
            DataList[index] = None
    return DataList


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
    :param dataframe: takes the Dataframe Dataframe
    :return: json string build oput of the provided Dataframe
    """
    data_set = {}
    json_dump=""
    dataframe_length = int(len(dataframe[1]))

    if len(dataframe[0]) == len(dataframe[1]):
        for x in range(0, dataframe_length):
            if dataframe[1][x] not in ["", " ", None]:
                key = str(dataframe[0][x])
                value = str(dataframe[1][x])
                data_set[key] = [value]

            json_dump = json.dumps(data_set)
    else:
        logging.ERROR("Error while transforming list into json String")

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
Variable declerations:
oad variable from the config file using ConfigParser.
The config file needs to be locate in the root Folder of the program
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
construkt SpecimenDataFrame:
The contained Data in this Dataframe is of Type String
The order of the Elements is to be respected 0 to 6
SpecimenDataFrame = [PKID, Temp, Humidity, Weight, Measurement 1, Measurement 2, Measurement 3]
The Names are taken from the SpecimenNameFrame
"""

SpecimenNameList = convert_str_to_list(SpecimenNameString)
SpecimenDataList = convert_str_to_list(SpecimenDataString)
SpecimenDataFrame = [SpecimenNameList, SpecimenDataList]
#initialize logging
logging.basicConfig(filename="probenmonitoring.log", filemode="w", level=logging.DEBUG)


class ConsoleWorkerSensor(QObject):
    """
    this class is for packing the signal handling methods and the runing progress of the basic application
    in a QObject frame to take part in the QApplication EventLoop
    """

    # TODO: Change Signal Datatype to Flaot for Temp and humidety

    @staticmethod
    def handle_temp_signal(temperature):
        """
        resives the Signal with the Temperatur Information from the Sensor Thread and
        positions it in the corresponding slot in the Dataframe.
        :param temperature: Temperatur resived ffrom the Sensor Thread as String
        """
        # console output
        print("\nTemperature: %0.1f C" % float(temperature))

        # update SpecimenDataframe
        entry_found = False
        i = 0

        # find right slot in the SpecimenDataframe
        while not entry_found:
            if SpecimenDataFrame[0][i] == "Temp":
                SpecimenDataFrame[1][i] = float(temperature)
                entry_found = True
            if i == len(SpecimenDataFrame[0]) and entry_found is False:
                print("no category Temp was found in the SpecimenDataframe. please check config.ini")
                entry_found = False
            i += 1

    def handle_humid_signal(self, humidity):
        """
        resives the Signal with the humidety Information from the Sensor Thread and
        positions it in the corresponding slot in the Dataframe.
        :param temperature: Humidity resieved from the Sensor Thread as String
        """

        # console output
        print("Humidity: %0.1f %%" % float(humidity))

        # update SpecimenDataframe
        entry_found = False
        i = 0

        # find right slot in the SpecimenDataframe
        while not entry_found:
            if SpecimenDataFrame[0][i] == "Humidity":
                SpecimenDataFrame[1][i] = float(humidity)
                entry_found = True
            if i == len(SpecimenDataFrame[0]) and entry_found is False:
                print("no category Temp was found in the SpecimenDataframe. please check config.ini")
                entry_found = False
            i += 1

    def handle_heater_signal(self):
        print("heater gestartet")

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
        # self.sensor.start_sensor()


class PublishData(QThread):
    """
    Thread class for continuously publishing the updated specimenDataframe
    to the MQTT Broker
    """

    @pyqtSlot()
    def run(self):
        self.Client = MqttPublisher(DeviceName, broker, port, username, passkey)

        while True:
            self.Client.publish(BaseTopic, build_json(SpecimenDataFrame))
            time.sleep(Interval+1)


class ConsoleWorkerPublish(QObject):
    """
    corresponding worker Object to  for continuously publishing the updated specimenDataframe
    """

    def start_communication_tread(self):
        self.Communicator = PublishData()
        self.Communicator.start()


# main program


if __name__ == "__main__":

    if DeviceType == 1:
        # init_csv(SpecimenDataFrame[0])
        app = QCoreApplication(sys.argv)
        cws = ConsoleWorkerSensor()
        cws.run_measuring_thread()
        print("gestartet")

        cwp = ConsoleWorkerPublish()
        cwp.start_communication_tread()
        print("cwp gestartet")

        sys.exit(app.exec())

    # folloed by other IF clouses for other Device Types

    # TODO: understand PyQt Apllications
    # TODO: Pack Sensor in Movetothreadfunktion
