import paho.mqtt.client as mqtt
import logging

#TODO: implement Configparser

#Variable Declerations
"""
The contained Data in this Dataframe is of Type String
The order of the Elements is to be respected 0 to 6
SpecimenDataFrame = [PKID, Temp, Humidity, Weight, Messurment 1, Messurment 2, Messurment 3]
"""
SpecimenDataFrame = [none, none, none, none, none, none, none]
mqtt_broker="192.168.178.53"
mqtt_port=1883

def on_publish(client,userdata,result):
    print("data published \n")
    logging.info("data published")
    pass


def on_connect(client, userdata, flags, rc):
    logging.info("Connected flags" + str(flags) + "result code " \
                 + str(rc) + "client1_id ")
    client.connected_flag = True

    print>("Connected flags" + str(flags) + "result code " \
                 + str(rc) + "client1_id ")

def publish_data(PKID, Data_Type, Data):

    """
    :param PKID:        Probenkörper ID obtained from Barcode Scan or manual entry :str:
    :param Data_Type:   Temp , Humidity, Mesurments, weight :str:
    :param Data:        coressponding Data Type can be :str: :int: or Dataframes
    :return:            payload
    """
    try:
        mqtt_Topic = PKID + "/" + Data_Type
        client.publish(mqtt_Topic, str(Data))
    except:
        logging.info("Error while publishinng Data to the mqtt broker")

client = mqtt.Client("Python client 1")
client.on_connect = on_connect
client.on_publish = on_publish
client.connect(mqtt_broker,mqtt_port)
publish_data("Probekörper42", "Temp", 24)
