import struct
from pydantic import BaseModel
from datetime import datetime
import time
import json
from pydantic import TypeAdapter

import platform
def is_raspberry_pi():
    # Überprüfe, ob die Plattform "linux" und der Prozessor "aarch64" ist
    return platform.machine().startswith('aarch64') and platform.system() == 'Linux'

modules = {
    "Air":0x55,
    "Water":0x11,
    "Sun":0x12,
    "PSU":0x13,
    "Misc":0x14
}

sensors = {
    "AirQuality":0x01,
    "AirCO2":0x02,
    "AirTemperature":0x03,
    "AirHumidity":0x04,
    "FanSpeed":0x05,
    "WaterLevel":0x06,
    "WaterFlow":0x07,
    "WaterTemperature":0x08,
    "SunIntensity":0x09,
    "PSUVoltage":0x0A,
    "PSUCurrent":0x0B,
    "PSUPower":0x0C,
    "PSUGridVoltage":0x0D,
    "PSUGridCurrent":0x0E,
    "PSUGridPower":0x0F,
    "PSUInternalTemperature":0x10,
    "PSUFanSpeed":0x11,
    "Door":0x20
}

actuators = {
    "Wind":0x01,
    "Regen":0x02,
    "Sonne":0x04
}

print("Raspberry Pi: " + str(is_raspberry_pi()))

if is_raspberry_pi():
    from smbus2 import SMBus

current_time = int(time.time())
print("Time: " + str(current_time))


class Value(BaseModel):
    intensity: int
    time: int

class ScheduleSet(BaseModel):
    UpdateID: int
    Sonne: list[Value] | None = None
    Regen: list[Value] | None = None
    Wind: list[Value] | None = None


with open("schedule.json", "r") as schedule_file:
    schedule = ScheduleSet.model_validate_json(schedule_file.read())



def set_data(module, actuator, data):
    module_adress = modules.get(module)
    actuator_code = actuators.get(actuator)
    if not is_raspberry_pi():
        print("Module: " + hex(module_adress))
        return
    data_byte = data.to_bytes(1, byteorder="big")
    bus = SMBus(1)
    bus.write_i2c_block_data(module_adress, actuator_code, data_byte)
    bus.close()  

schedule = schedule.model_dump().items()

print(schedule)

for module, values in schedule:
    # Prüfen, ob values eine Liste ist, bevor wir versuchen, darüber zu iterieren
    if isinstance(values, list):
        for value in values[:]:
            if value["time"] < current_time:
                match module:
                    case "Sonne":
                        set_data("Sun", "Sonne", value["intensity"])
                    case "Regen":
                        set_data("Water", "Regen", value["intensity"])
                    case "Wind":
                        set_data("Air", "Wind", value["intensity"])
                values.remove(value)
                # print(schedule)
                # print(module + ": " + str(value["intensity"]) + " at " + str(value["time"]))
                # print("Remove " + str(value))



schedule = dict(schedule)  # convert to dict
print(schedule)
schedule = ScheduleSet.model_validate(schedule)
print(schedule)


with open("schedule.json", "w") as schedule_file:
    schedule_json = schedule.model_dump_json()
    print(schedule_json)
    schedule_file.write(schedule_json)

