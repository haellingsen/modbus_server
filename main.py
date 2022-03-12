#!./venv/bin/python
from pyModbusTCP.server import ModbusServer, DataBank
from time import sleep
from random import uniform, random
import os
import json
import itertools
import http.server
import socketserver
import threading
from datetime import datetime

from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

WEBPORT = 8000
MODBUSPORT = 502
WEBDIRECTORY = "webui"
MODBUS_CO_COUNT = 30
MODBUS_DI_COUNT = 30
MODBUS_HR_COUNT = 30
MODBUS_IR_COUNT = 30
MODBUS_PRINT_TO_TERMINAL_ENABLED = False
httpServerThread = ""


def fronius_logic(simulation_active, simulation_active_old):
    start_welding = DataBank.get_coils(0)[0]
    main_current_signal = DataBank.get_discrete_inputs(6)[0]
    simulation_active_changed = simulation_active != simulation_active_old
    # if welding started and not main current signal set (used to determine if welding is active on op panel)
    if start_welding and not main_current_signal:
        sleep(0.4)
        DataBank.set_discrete_inputs(6, [True])
        DataBank.set_input_registers(0, [49914])
        print(f"Turning welding process on.")
        print(
            f"setting discrete input 6 to: {DataBank.get_discrete_inputs(6)}")
        print(
            f"setting input register 0 to: {DataBank.get_input_registers(0)}")
    elif not start_welding and main_current_signal:  # if welding stopped
        DataBank.set_discrete_inputs(6, [False])
        DataBank.set_input_registers(0, [2])
        print(f"Turning process off: {DataBank.get_discrete_inputs(6)}")

    if main_current_signal:
        wirefeed_speed_command = DataBank.get_holding_registers(5)[0]
        welding_voltage = uniform(22, 24)
        welding_current = uniform(230, 250)
        welding_wirefeed_speed = uniform(
            wirefeed_speed_command-1, wirefeed_speed_command+1)
        DataBank.set_input_registers(
            4, [int(welding_voltage*100), int(welding_current*10), int(welding_wirefeed_speed)])
        #print(f"simulating welding with parameters: {welding_voltage} V,  {welding_current} A,  and {welding_wirefeed_speed/100} m/min.")

    if simulation_active_changed and simulation_active:
        DataBank.set_holding_registers(
            1, [DataBank.get_holding_registers(1)[0] + 1])
    elif not simulation_active and simulation_active_changed:
        DataBank.set_holding_registers(
            1, [DataBank.get_holding_registers(1)[0] - 1])

def dict_to_json(filename, _dict):
    with open(filename, "w", encoding="utf-8") as f:
        return json.dump(_dict, f)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEBDIRECTORY, **kwargs)


def runHttpServer():
    with socketserver.TCPServer(("", WEBPORT), Handler) as httpd:
        print("serving web ui at port", WEBPORT)
        httpd.serve_forever()


def setupThreadAndStartWebServer():
    httpServerThread = threading.Thread(target=runHttpServer)
    httpServerThread.setDaemon(True)
    httpServerThread.start()


def randomWord():
    return uniform(0, 65536)


def randomBit():
    return random() < 0.5


@app.route('/signals')
def get_signal_dict():
    holding_registers = DataBank.get_holding_registers(0, MODBUS_HR_COUNT)
    input_registers = DataBank.get_input_registers(0, MODBUS_IR_COUNT)
    coils = DataBank.get_coils(0, MODBUS_CO_COUNT)
    discrete_inputs = DataBank.get_discrete_inputs(0, MODBUS_DI_COUNT)

    signal_list = [{
                "type": "holdingRegister",
                "address": {
                    "absolute": word_address * 16,
                    "register": word_address},
                "name": f"holdingRegister_{word_address}",
                "value": value
            } for (word_address, value) in enumerate(holding_registers)]

    signal_list.extend(
        [
            {
                "type": "inputRegister",
                "address": {
                    "absolute": word_address * 16,
                    "register": word_address},
                "name": f"inputRegister_{word_address}",
                "value": value
            } for (word_address, value) in enumerate(input_registers)])

    signal_list.extend(
        [
            {
                "type": "discreteInput",
                "address": {
                    "absolute": bit_address,
                    "register": int(bit_address/16)},
                "name": f"discreteInput_{bit_address}",
                "value": value
            } for (bit_address, value) in enumerate(discrete_inputs)])

    signal_list.extend(
        [
            {
                "type": "coil",
                "address": {
                    "absolute": bit_address,
                    "register": int(bit_address/16)},
                "name": f"coil_{bit_address}",
                "value": value
            } for (bit_address, value) in enumerate(coils)])


    return {
        "signals": signal_list,
        "timestamp": datetime.now().isoformat()
    }


def setupAndStartModbusServer():
    simulation_active = False
    simulation_active_old = False

    server = ModbusServer("0.0.0.0", MODBUSPORT, no_block=True)
    try:
        print("Starting modbus server...")
        server.start()
        print("Modbus server is online")

        while True:
            simulation_active = DataBank.get_coils(16)[0]

            fronius_logic(simulation_active, simulation_active_old)

#            sleep(0.1)
            simulation_active_old = simulation_active

    except Exception as e:
        print(e)
        print("Shuting down modbus server...")
        server.stop()
        print("Modbus server shut down")


def main():
    setupThreadAndStartWebServer()
    sleep(2)
    modbusServerThread = threading.Thread(target=setupAndStartModbusServer)
    modbusServerThread.setDaemon(True)
    modbusServerThread.start()
    app.run(host="0.0.0.0", port=8080)

if __name__ == '__main__':
    main()

