# TODO: Add support for 2 power supplies, be able to set fan speed


import struct
import time
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from random import randrange

import platform


def is_raspberry_pi():
    # Überprüfe, ob die Plattform "linux" und der Prozessor "aarch64" ist
    return platform.machine().startswith('aarch64') and platform.system() == 'Linux'


if is_raspberry_pi():
    from smbus2 import SMBus

description = """
                All returnvalues are in the range of 0-100.
                Inputvalues are in the range of 0-100, except for the schedule starttime and endtime, which are in the range of 0-4294967295 (Unix timestamp).
                """


# Tags
tags_metadata = [
    {"name": "Air", "description": "Endpoints related to air quality and control"},
    {"name": "Water", "description": "Endpoints related to water quality and control"},
    {"name": "Sun", "description": "Endpoints related to sun intensity control"},
    {"name": "PSU", "description": "Endpoints related to power supply unit"},
    {"name": "Misc", "description": "Miscellaneous endpoints"},
    {"name": "setValue", "description": "Set values"},
    {"name": "TTS", "description": "Text to speech"}
]

app = FastAPI(
    title="Klimakammer API",
    description=description,
    summary="API for controlling the Klimakammer",
    version="0.0.1",
    license_info={
        "name": "GPL-3.0 License",
        "url": "https://www.gnu.org/licenses/gpl-3.0.html",
    },
    openapi_tags=tags_metadata
)

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

modules = {
    "Air": 0x55,
    "Water": 0x11,
    "Sun": 0x12,
    "PSU": 0x13,
    "Misc": 0x14
}

sensors = {
    "AirQuality": 0x01,
    "AirCO2": 0x02,
    "AirTemperature": 0x03,
    "AirHumidity": 0x04,
    "FanSpeed": 0x05,
    "WaterLevel": 0x06,
    "WaterFlow": 0x07,
    "WaterTemperature": 0x08,
    "SunIntensity": 0x09,
    "PSUVoltage": 0x0A,
    "PSUCurrent": 0x0B,
    "PSUPower": 0x0C,
    "PSUGridVoltage": 0x0D,
    "PSUGridCurrent": 0x0E,
    "PSUGridPower": 0x0F,
    "PSUInternalTemperature": 0x10,
    "PSUFanSpeed": 0x11,
    "Door": 0x20
}


class Value(BaseModel):
    intensity: int
    time: int


class ScheduleSet(BaseModel):
    UpdateID: int
    Sonne: list[Value] | None = None
    Regen: list[Value] | None = None
    Wind: list[Value] | None = None


# Change to use 32bit floats
def get_data(module, sensor):
    module_address = modules.get(module)
    sensor_code = sensors.get(sensor)
    if not is_raspberry_pi():
        return randrange(100), randrange(100)
    bus = SMBus(1)
    # Workaround for bug in Firmware, read is always one step behind
    bus.read_i2c_block_data(module_address, sensor_code, 8)
    time.sleep(0.1)
    data_bytes = bus.read_i2c_block_data(module_address, sensor_code, 8)
    bus.close()
    data_bytes1 = data_bytes[0:4]
    data_bytes2 = data_bytes[4:8]
    data1 = struct.unpack("<f", bytes(data_bytes1))[0]
    data2 = struct.unpack("<f", bytes(data_bytes2))[0]
    return data1, data2


def set_data(schedule):
    # TODO: Change code to write data to json file. JSON-File will be read by another script running with cron
    schedule_set_json = schedule.json()
    with open("schedule.json", "w") as schedule_file:
        schedule_file.write(schedule_set_json)


# region setValue
@app.put("/setValue", tags=["setValue"])
def setValue(schedule: ScheduleSet):
    set_data(schedule)
    return {"message": schedule}
# endregion

# region Air


@app.get("/air/quality", tags=["Air"])
def get_air_quality():
    """
    Get the air quality data.

    :return: Air quality data.
    """
    data = get_data("Air", "AirQuality")
    return {"AirQuality": data}


@app.get("/air/co2", tags=["Air"])
def get_air_CO2():
    data = get_data("Air", "AirCO2")
    return {"CO2": data}


@app.get("/air/temperature", tags=["Air"])
def get_air_temperature():
    data = get_data("Air", "AirTemperature")
    return {"Air": data}


@app.get("/air/humidity", tags=["Air"])
def get_air_humidity():
    data = get_data("Air", "AirHumidity")
    return {"Humidity": data}


@app.get("/air/fanspeed", tags=["Air"])
def get_air_fanspeed():
    data = get_data("Air", "FanSpeed")
    return {"Fanspeed": data}

# endregion

# region Water


@app.get("/water/level", tags=["Water"])
def get_water_level():
    data = get_data("Water", "WaterLevel")
    return {"Level": data}


@app.get("/water/flow", tags=["Water"])
def get_water_flow():
    data = get_data("Water", "WaterFlow")
    return {"Flow": data}


@app.get("/water/temperature", tags=["Water"])
def get_water_temperature():
    data = get_data("Water", "WaterTemperature")
    return {"Temperature": data}

# endregion

# region Sun


@app.get("/sun/intensity", tags=["Sun"])
def get_sun_intensity():
    data = get_data("Sun", "SunIntensity")
    return {"Intensity": data}

# endregion

# region PSU


@app.get("/psu/voltage", tags=["PSU"])
def get_psu_voltage():
    data = get_data("PSU", "PSUVoltage")
    return {"PSUVoltage1": data[0], "PSUVoltage2": data[1]}


@app.get("/psu/current", tags=["PSU"])
def get_psu_current():
    data = get_data("PSU", "PSUCurrent")
    return {"PSUCurrent1": data[0], "PSUCurrent2": data[1]}


@app.get("/psu/power", tags=["PSU"])
def get_psu_power():
    data = get_data("PSU", "PSUPower")
    return {"PSUPower": data[0]/1000, "PSUPower2": data[1]/1000}


@app.get("/psu/gridvoltage", tags=["PSU"])
def get_psu_gridvoltage():
    data = get_data("PSU", "PSUGridVoltage")
    return {"PSUGridVoltage1": data[0], "PSUGridVoltage2": data[1]}


@app.get("/psu/gridcurrent", tags=["PSU"])
def get_psu_gridcurrent():
    data = get_data("PSU", "PSUGridCurrent")
    return {"PSUGridCurrent1": data[0], "PSUGridCurrent2": data[1]}


@app.get("/psu/gridpower", tags=["PSU"])
def get_psu_gridpower():
    data = get_data("PSU", "PSUGridPower")
    return {"PSUGridPower": data[0]/10, "PSUGridPower2": data[1]/10}


@app.get("/psu/internaltemperature", tags=["PSU"])
def get_psu_internaltemperature():
    data = get_data("PSU", "PSUInternalTemperature")
    # Calibration
    return {"PSUInternalTemperature1": data[0]+10, "PSUInternalTemperature2": data[1]+10}


@app.get("/psu/fanspeed", tags=["PSU"])
def get_psu_fanspeed():
    data = get_data("PSU", "PSUFanSpeed")
    return {"PSUFanSpeed": data[0], "PSUFanSpeed2": data[1]}


@app.get("/psu/status", tags=["PSU"])
def get_psu_status():
    data = get_data("PSU", "PSUStatus")
    return {"PSUStatus": data}


@app.get("/psu/fault", tags=["PSU"])
def get_psu_fault():
    data = get_data("PSU", "PSUFault")
    return {"PSUFault": data}

# endregion

# region Misc


@app.get("/misc/door", tags=["Misc"])
def get_misc_door():
    data = get_data("Misc", "Door")
    return {"Door": data}
# endregion


@app.post("/STT/set", tags=["STT"])
async def create_upload_file(file: UploadFile):
    return {"filename": file.filename}


@app.get("/STT/get", tags=["STT"])
def get_STT_cmd():
    data = '{"Command": 2,"Feature": "Sonne","data": [{"value": 50,"Time": 234875842758},{"value": 99},{"Place": "Wien"}]}'
    data = "None"
    return {data}
