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
MODBUS_BITCOUNT = 100
MODBUS_WORDCOUNT = 100
MODBUS_ENABLE_RANDOM_NUMBER_POPULATION_BITS = False
MODBUS_ENABLE_RANDOM_NUMBER_POPULATION_WORDS = False
MODBUS_RANDOM_NUMBER_COUNT_BITS = MODBUS_BITCOUNT
MODBUS_RANDOM_NUMBER_COUNT_WORDS = MODBUS_WORDCOUNT
MODBUS_RANDOM_NUMBER_START_BITS = 25
MODBUS_RANDOM_NUMBER_START_WORDS = 25
MODBUS_PRINT_TO_TERMINAL_ENABLED = False
httpServerThread=""

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


def setupAndStartModbusServer():
    server = ModbusServer("0.0.0.0", MODBUSPORT, no_block=True)
    try:    
        print("Starting modbus server...")
        server.start()
        print("Modbus server is online")

        while True:
            if MODBUS_ENABLE_RANDOM_NUMBER_POPULATION_WORDS:
                DataBank.set_words(MODBUS_RANDOM_NUMBER_START_WORDS, [uniform(0,65536) for i in range(MODBUS_RANDOM_NUMBER_COUNT_WORDS)])
            if MODBUS_ENABLE_RANDOM_NUMBER_POPULATION_BITS:
                DataBank.set_bits(MODBUS_RANDOM_NUMBER_START_BITS, [random() < 0.5 for i in range(MODBUS_RANDOM_NUMBER_COUNT_BITS)])
            
            words = dict(list(enumerate(DataBank.get_words(0, MODBUS_WORDCOUNT))))
            bits = dict(list(enumerate(DataBank.get_bits(0, MODBUS_BITCOUNT)))) 
            server_data = {"bits": bits, "words": words, "timestamp": datetime.now().isoformat()}
            dict_to_json("./webui/modbus.json", server_data)
            if MODBUS_PRINT_TO_TERMINAL_ENABLED:
                os.system("cls" if os.name == "nt" else "clear")
                print(json.dumps(bits, indent = 1), json.dumps(words, indent = 1))
                print(f"{'Bits':<20}{'Words'}")
                for d1, d2 in itertools.zip_longest(sorted(bits), sorted(words), fillvalue='0'): 
                    print(f"{d1:>2}: {bits.get(d1, 'NA'):<15} {d2:>2}: {words.get(d2, 'NA')}")
            
            # if welding start goes HI. Set robot motion release HI
            if bits.get(0):
                sleep(0.5)
                DataBank.set_bits(9, [True])
            else:
                DataBank.set_bits(9, [False])
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