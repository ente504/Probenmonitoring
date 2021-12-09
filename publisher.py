import paho.mqtt.client as mqtt
import logging
import time
import random
import configparser
import shlex

class MqttCommunicator:
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
        #TODO:make every variable returnable? For mor Object character?
        self.Client_Name = client_name
        self.mqtt_Broker = mqtt_broker
        self.mqtt_Port = mqtt_port
        self.mqtt_Username = mqtt_username
        self.mqtt_Passkey = mqtt_passkey

        #setup mqtt client
        self.mqtt_client = mqtt.Client(self.Client_Name)

        if self.mqtt_Username not in ["", " ", None]  or self.mqtt_Passkey not in ["", " ", None]:
            self.mqtt_client.username_pw_set(self.mqtt_Username, self.mqtt_Passkey)
        else:
            logging.info("the server is not using a User authentication")

        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_publish = self.on_publish
        self.mqtt_client.connect(mqtt_broker, mqtt_port)

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
#TODO: implement Configparser

def Convert_Str_To_List(datastring):
    """
    :param datastring: string that shoud be counerted to a List. Seperation wenn the elemen ", " (with space) is found.
    :return: the input datastring is returnd as a List element. Additionaly all found "None" Strings are converted
             to the python None Element.
    """
    DataList = datastring.split(", ")

    for index, value in enumerate(DataList):
        if value == "None":
            DataList[index] = None
    return DataList


def randomize_Dataframe(dataFrame):
    """
    :param dataFrame: takes the Dataframe Type 2D Dataframe
    :return: returns modified Dataframe

    method is for debugging and test purposes. It simulates Sensor Data input in form of randomized Data
    """
    dataFrame[1][1] = str(random.randint(10,30))
    dataFrame[1][2] = str(round(random.uniform(0.1, 1),2))

    return dataFrame

#Variable Declerations
#load variable from the config file useing ConfigParser.
# The config file needs to be locate in the root Folder of the programm

CONFIG_FILE = "config.ini"
config = configparser.ConfigParser()
config.read(CONFIG_FILE)

DeviceName = str(config["GENERAL"]["DeviceName"])
SpecimenNameString = config["DATA"]["SpecimenNameList"]
SpecimenDataString = config["DATA"]["SpecimenDefaultData"]
broker = str(config["MQTT"]["Broker"])
port = int(config["MQTT"]["Port"])
username = str(config["MQTT"]["UserName"])
passkey = str(config["MQTT"]["PassKey"])

#construckt SpecimenDataFrame
"""
The contained Data in this Dataframe is of Type String
The order of the Elements is to be respected 0 to 6
SpecimenDataFrame = [PKID, Temp, Humidity, Weight, Measurement 1, Measurement 2, Measurement 3]
The Names are taken from the SpecimenNameFrame
"""
SpecimenNameList = Convert_Str_To_List(SpecimenNameString)
SpecimenDataList = Convert_Str_To_List(SpecimenDataString)
SpecimenDataFrame = [SpecimenNameList, SpecimenDataList]

logging.basicConfig(filename='probenmonitoring.log', filemode='w', level=logging.DEBUG)


#main program
Client = MqttCommunicator(DeviceName, broker, port, "", "")

for y in range(0,20):
    NewFrame = randomize_Dataframe(SpecimenDataFrame)
    SpecimenDataFrame = NewFrame

    res = Client.publish_data(SpecimenDataFrame)
    print(res)
    time.sleep(1)
