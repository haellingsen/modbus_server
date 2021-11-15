#!./venv/bin/python
from pyModbusTCP.server import ModbusServer, DataBank
from time import sleep
from random import uniform, random
import os, json, itertools
import http.server
import socketserver
import threading
from datetime import datetime

WEBPORT = 8000
MODBUSPORT = 502
WEBDIRECTORY = "webui"
MODBUS_CO_COUNT = 30
MODBUS_DI_COUNT = 30
MODBUS_HR_COUNT = 30
MODBUS_IR_COUNT = 30
MODBUS_PRINT_TO_TERMINAL_ENABLED = False
httpServerThread=""

def fronius_logic():
    start_welding = DataBank.get_coils(0)[0]
    main_current_signal = DataBank.get_discrete_inputs(6)[0]
        
    if start_welding and not main_current_signal: # if welding started and not main current signal set (used to determine if welding is active on op panel)
            sleep(0.4)
            DataBank.set_discrete_inputs(6, [True])
            DataBank.set_input_registers(0, [49914])
            print(f"Turning welding process on.")
            print(f"setting discrete input 6 to: {DataBank.get_discrete_inputs(6)}")
            print(f"setting input register 0 to: {DataBank.get_input_registers(0)}")
    elif not start_welding and main_current_signal: # if welding stopped
            DataBank.set_discrete_inputs(6, [False])
            DataBank.set_input_registers(0, [2])
            print(f"Turning process off: {DataBank.get_discrete_inputs(6)}")
            
    if main_current_signal:
        wirefeed_speed_command = DataBank.get_holding_registers(5)    
        welding_voltage = uniform(22,24)
        welding_current = uniform(230,250)
        welding_wirefeed_speed = uniform(wirefeed_speed_command-1, wirefeed_speed_command+1)

        

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
    return uniform(0,65536)

def randomBit():
    return random() < 0.5

def setupAndStartModbusServer():
    server = ModbusServer("0.0.0.0", MODBUSPORT, no_block=True)
    try:    
        print("Starting modbus server...")
        server.start()
        print("Modbus server is online")

        while True:     
            fronius_logic()

            holding_registers = dict(list(enumerate(DataBank.get_holding_registers(0, MODBUS_HR_COUNT))))
            input_registers = dict(list(enumerate(DataBank.get_input_registers(0, MODBUS_IR_COUNT))))
            coils = dict(list(enumerate(DataBank.get_coils(0, MODBUS_CO_COUNT)))) 
            discrete_inputs = dict(list(enumerate(DataBank.get_discrete_inputs(0, MODBUS_DI_COUNT))))
            server_data = {"coils": coils, "discreteInputs": discrete_inputs, "holdingRegisters": holding_registers, "inputRegisters": input_registers, "timestamp": datetime.now().isoformat()}
            dict_to_json("./webui/modbus.json", server_data)

            if MODBUS_PRINT_TO_TERMINAL_ENABLED:
                os.system("cls" if os.name == "nt" else "clear")
                print(json.dumps(bits, indent = 1), json.dumps(words, indent = 1))
                print(f"{'Bits':<20}{'Words'}")
                for d1, d2 in itertools.zip_longest(sorted(bits), sorted(words), fillvalue='0'): 
                    print(f"{d1:>2}: {bits.get(d1, 'NA'):<15} {d2:>2}: {words.get(d2, 'NA')}")
                        
            sleep(0.1)

    except Exception as e:
            print(e)
            print("Shuting down modbus server...")
            server.stop()
            print("Modbus server shut down")

def main():
    setupThreadAndStartWebServer()
    sleep(2)
    setupAndStartModbusServer()

if __name__ == '__main__':
    main()
