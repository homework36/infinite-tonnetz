import argparse
import socket
from socket import timeout as TimeoutException
import json

'''
This class reads the OSC information sent from phone in JSON format.
Doc: https://www.notion.so/Send-OSC-from-phone-to-PC-55ec4f7e780e49d68cd78e8dade89ea5
Author: Lu Yu
Created date: 04/03/2022
Data format:
{
   "device":{
      "name":"unknown device (iPhone13,1)",
      "displayheight":2001,
      "uuid":"pqL6pcundfPUvFbN",
      "os":"ios",
      "osversion":"14.7.1",
      "displaywidth":1125
   },
   "timestamp":"2022_04_03_20:25:10.678",
   "sensordata":{
      "gravity":{
         "y":0.0009562134509906173,
         "x":0.004498600028455257,
         "z":-0.9999894499778748
      },
      # other metrics
   }
'''

class OSCReader:
  def __init__(self, ip, port):
    # Code adopted from https://wiki.python.org/moin/UdpCommunication
    assert isinstance(ip, str) and isinstance(port, int), 'Input not valid'
    self.sock = socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_DGRAM) # UDP

    self.sock.bind((ip, port))

  def get_pos(self):
    try:
      data, addr = self.sock.recvfrom(1024) # buffer size is 1024 bytes
      self.sock.settimeout(.01)
    except TimeoutException:
      # print("Timeout. Please try again.")
      return
    obj = json.loads(data)
    # print(obj)
    return obj['sensordata']
