import asyncio
import copy
import logging
from datetime import datetime
import time
from math import sin
import Adafruit_DHT

from asyncua import ua, uamethod, Server

DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4
celsius = 37.5

class SubHandler(object):

    """
    Subscription Handler. To receive events from server for a subscription
    """

    def datachange_notification(self, node, val, data):
        print("Python: New data change event", node, val)

    def event_notification(self, event):
        print("Python: New event", event)


# method to be exposed through server

def func(parent, variant):
    ret = False
    if variant.Value % 2 == 0:
        ret = True
    return [ua.Variant(ret, ua.VariantType.Boolean)]


# method to be exposed through server
# uses a decorator to automatically convert to and from variants

@uamethod
def multiply(parent, x, y):
    print("multiply method call with parameters: ", x, y)
    return x * y


async def main():

    # Setup our server
    server = Server()

    await server.init()
    server.disable_clock()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    server.set_server_name("Raspberry Pi Environmental Monitor")

    # Set all possible endpoint policies for clients to connect through
    server.set_security_policy([
                ua.SecurityPolicyType.NoSecurity,
                ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
                ua.SecurityPolicyType.Basic256Sha256_Sign])

    # Setup our own namespace
    uri = "github.com/awojnarek/opcua-pi"
    idx = await server.register_namespace(uri)

    # Create directly some objects and variables
    sensorobj = await server.nodes.objects.add_object(idx, "SensorObj")
    humval = await sensorobj.add_variable(idx, "HumidityValue", 0.0)
    tempval = await sensorobj.add_variable(idx, "TemperatureValue", 0.0)

    # Starting!
    async with server:
        print("Available loggers are: ", logging.Logger.manager.loggerDict.keys())

        while True:
            await asyncio.sleep(0.1)
            humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
            fahrenheit = (temperature * 1.8) + 32

            if humidity is not None:
                await server.write_attribute_value(humval.nodeid, ua.DataValue(humidity))

            if temperature is not None:
                await server.write_attribute_value(tempval.nodeid, ua.DataValue(fahrenheit))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
