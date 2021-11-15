#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Modbus/TCP server
#
# run this as root to listen on TCP priviliged ports (<= 1024)
# default Modbus/TCP port is 502 so we prefix call with sudo
# add "--host 0.0.0.0" to listen on all available IPv4 addresses of the host
#
#   sudo ./server.py --host 0.0.0.0

import argparse
from pyModbusTCP.server import ModbusServer, DataBank
from time import sleep

if __name__ == '__main__':
    # parse args
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', type=str, default='localhost', help='Host')
    parser.add_argument('-p', '--port', type=int, default=5020, help='TCP port')
    args = parser.parse_args()
    # start modbus server
    server = ModbusServer(host=args.host, port=args.port, no_block=True)
    server.start()
    print("server started")


    while True:
        if DataBank.get_coils(0)[0] and not DataBank.get_discrete_inputs(6)[0]:
            print(f"Welding start: {DataBank.get_coils(0)}, setting main current signal to True.") 
            sleep(0.4)
            DataBank.set_discrete_inputs(6, [True])
            print(f"setting discrete input 6 to: {DataBank.get_discrete_inputs(6)}")
        elif not DataBank.get_coils(0)[0] and DataBank.get_discrete_inputs(6)[0]:
            DataBank.set_discrete_inputs(6, [False])
            print(f"setting discrete input 6 to: {DataBank.get_discrete_inputs(6)}")
        
        sleep(0.2)