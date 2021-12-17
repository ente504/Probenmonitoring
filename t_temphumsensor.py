# !/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Revision: @ente504
# 0.0.1: Initial version


from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
import time
import logging
import board
import adafruit_sht31d


class TempHumSensor(QThread):
    #TODO: implement a .csv logger for local storage if needed
    #TODO: write comments for the methods

    # Signals
    Temperature_Signal = pyqtSignal(str, name="Temperature_Signal")
    relative_Humidity_Signal = pyqtSignal(str, name="relative_Humidity_Signal")
    Heater_Signal = pyqtSignal(name="Heater_Signal")

    def __init__(self, wait_time, heater_status, heater_interval):
        super().__init__()
        self.i2c = board.I2C()
        self.sensor_sht31d = adafruit_sht31d.SHT31D(self.i2c)
        self.wait_time = wait_time
        self.Heater_Status = heater_status
        self.Heater_Interval = heater_interval
        self.Temperature = ""
        self.relative_Humidity = ""
        self.is_running = True
        logging.info("initialisation of the TempHumSensor Class finished")

    @pyqtSlot(str)
    def stop(self):
        self.runner = False
        self.i2c.deinit()

    @pyqtSlot(str)
    def run(self):
        """
        :return: The last Temeratur and Humidity reading is returned
        """
        #self.sensor_sht31d.reset()
        logging.info(self.sensor_sht31d.status)
        loopcount = 0

        while True:
            loopcount += 1
            self.Temperature = self.sensor_sht31d.temperature
            self.Temperature_Signal.emit(str(self.Temperature))
            self.relative_Humidity = self.sensor_sht31d.relative_humidity
            self.relative_Humidity_Signal.emit(str(self.relative_Humidity))
            #print("\nTemperature: %0.1f C" % self.sensor_sht31d.temperature)
            #print("Humidity: %0.1f %%" % self.sensor_sht31d.relative_humidity)
            if (self.Heater_Status is True) and (loopcount == self.Heater_Interval):
                try:
                    self.sensor_sht31d.heater = True
                    self.Heater_Signal.emit()
                    time.sleep(1)
                    self.sensor_sht31d.heater = False
                    loopcount = 0
                except:
                    logging.ERROR("Error while using the Heater")
            time.sleep(self.wait_time)
        return [self.Temperature, self.relative_Humidity]

    def stop(self):
        self.is_running = False
        print('Stopping thread...')
        self.terminate()




