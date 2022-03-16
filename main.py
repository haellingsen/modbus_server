#!./venv/bin/python
from ast import Lambda
from pyModbusTCP.server import ModbusServer, DataBank
from time import sleep
from random import uniform, random
import json
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
active_power_source_type = ""


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

def json_to_dict(filename):
    with open(filename, 'r', encoding="utf-8") as f:
        return json.load(f)

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEBDIRECTORY, **kwargs)


def runHttpServer():
    with socketserver.TCPServer(("", WEBPORT), Handler) as httpd:
        print("serving web ui at port", WEBPORT)
        socketserver.TCPServer.allow_reuse_address = True
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
    global active_power_source_type
    active_power_source_type=json_to_dict('./config.json').get("activePowerSourceType")

    signal_mapping={
        "holdingRegister": (lambda address : DataBank.get_holding_registers(address)[0]),
        "inputRegister": (lambda address : DataBank.get_input_registers(address)[0]),
        "discreteInput": (lambda address : DataBank.get_discrete_inputs(address)[0]),
        "coil": (lambda address : DataBank.get_coils(address)[0])
    }
    power_source_signals={}
    if active_power_source_type=="Fronius":
        power_source_signals = json_to_dict('./powersourcetypes/fronius.json')
    elif active_power_source_type=="Kemppi":
        power_source_signals = json_to_dict('./powersourcetypes/kemppi.json')

    for signal in power_source_signals:
        if signal.get("type") in ["coil", "discreteInput"]:
            signal["value"] = signal_mapping.get(signal.get("type"))(signal.get("address").get("absolute"))
            #print(signal.get("name"), signal.get("type"), signal.get("address").get("absolute"), signal_mapping.get(signal.get("type"))(signal.get("address").get("absolute")))
        elif signal.get("type") in ["holdingRegister", "inputRegister"]:
            signal["value"] = signal_mapping.get(signal.get("type"))(signal.get("address").get("register"))
            #print(signal.get("name"), signal.get("type"), signal.get("address").get("register"), signal_mapping.get(signal.get("type"))(signal.get("address").get("register")))

    
    return {
        "powerSourceType": active_power_source_type,
        "signals": power_source_signals,
        "timestamp": datetime.now().isoformat()
    }


def setupAndStartModbusServer():
    simulation_active = False
    simulation_active_old = False
    global active_power_source_type

    server = ModbusServer("0.0.0.0", MODBUSPORT, no_block=True)
    try:
        print("Starting modbus server...")
        server.start()
        print("Modbus server is online at port: " + str(MODBUSPORT))
        prev_active_power_source_type = "not set"
        while True:
            if prev_active_power_source_type != active_power_source_type:
                print(f"Running {active_power_source_type} Logic")

            if active_power_source_type=="Fronius":
                simulation_active = DataBank.get_coils(16)[0]
                fronius_logic(simulation_active, simulation_active_old)
                simulation_active_old = simulation_active
            elif active_power_source_type=="Kemppi":
                #TODO implement kemppi logic here
                pass

            prev_active_power_source_type = active_power_source_type

    except Exception as e:
        print(e)
        print("Shuting down modbus server...")
        server.stop()
        print("Modbus server shut down")


def main():
    global active_power_source_type
    active_power_source_type=json_to_dict('./config.json').get("activePowerSourceType")
    setupThreadAndStartWebServer()
    sleep(2)
    modbusServerThread = threading.Thread(target=setupAndStartModbusServer)
    modbusServerThread.setDaemon(True)
    modbusServerThread.start()
    app.run(host="0.0.0.0", port=8080)

if __name__ == '__main__':
    main()

