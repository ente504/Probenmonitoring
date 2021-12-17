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
    dataframe[1][1] = str(random.randint(10,30))
    dataframe[1][2] = str(round(random.uniform(0.1, 1),2))
    return dataframe


# Variable declerations:

# load variable from the config file using ConfigParser.
# The config file needs to be locate in the root Folder of the program

CONFIG_FILE = "config.ini"
config = configparser.ConfigParser()
config.read(CONFIG_FILE)

DeviceName = str(config["GENERAL"]["DeviceName"])
DeviceType = int(config["GENERAL"]["DeviceType"])
SpecimenNameString = config["DATA"]["SpecimenNameList"]
SpecimenDataString = config["DATA"]["SpecimenDefaultData"]
broker = str(config["MQTT"]["Broker"])
port = int(config["MQTT"]["Port"])
username = str(config["MQTT"]["UserName"])
passkey = str(config["MQTT"]["PassKey"])

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

logging.basicConfig(filename="probenmonitoring.log", filemode="w", level=logging.DEBUG)


class ConsoleWorker(QObject):
    """
    this class is for packing the signal handling methods and the runing progress of the basic application
    in a QObjekt frame to take part in the QApplication EventLoop
    """
    #TODO: Change Signal Datatype to Flaot for Temp and humidety

    def handle_temp_signal(self, temperature):
        print("\nTemperature: %0.1f C" % float(temperature))
        SpecimenDataFrame[1][1] = str(temperature)

    def handle_humid_signal(self, humidity):
        print("Humidity: %0.1f %%" % float(humidity))
        SpecimenDataFrame[1][2] = str(humidity)

    def handle_heater_signal(self):
        print("heater gestartet")

    def run_measuring_thread(self):

        # init of the Tread class Object
        self.sensor = TempHumSensor(wait_time=2, heater_status=True, heater_interval=10)
        # connect signals to worker Methods
        self.sensor.finished.connect(self.sensor.quit)
        self.sensor.finished.connect(self.sensor.deleteLater)
        self.sensor.Temperature_Signal.connect(self.handle_temp_signal)
        self.sensor.relative_Humidity_Signal.connect(self.handle_humid_signal)
        self.sensor.Heater_Signal.connect(self.handle_heater_signal)
        # run Thread Object
        self.sensor.start()
        #self.sensor.start_sensor()

    def start_worker(self):

        print("Threadstart angestoßen")
        self.run_measuring_thread()
        print("thread gestartet")

        #hier Programmtext reinhacken#



#main program
#Client = MqttPublisher(DeviceName, broker, port, "", "")




if __name__ == "__main__":

    if DeviceType == 1:
        app = QCoreApplication(sys.argv)
        cw = ConsoleWorker()
        cw.start_worker()
        sys.exit(app.exec())

    #folloed by other IF clouses for other Device Types

    #TODO: understand PyQt Apllications
    #TODO: Pack Sensor in Movetothreadfunktion