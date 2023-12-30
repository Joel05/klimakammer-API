from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from random import randrange

import platform
def is_raspberry_pi():
    # Überprüfe, ob die Plattform "arm" und der Prozessor "arm" ist
    return platform.machine().startswith('arm') and platform.system() == 'Linux'


if is_raspberry_pi():
    from smbus2 import SMBus

description =   """
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
    "PSUStatus":0x0D,
    "PSUFault":0x0E,
    "Door":0x0F
}

class ScheduleSet(BaseModel):
    data: int
    starttime: int
    endtime: int

class ManualSet(BaseModel):
    data: int


#Change to use 32bit floats
def get_data(module, sensor):
    module_address = modules.get(module)
    sensor_code = sensors.get(sensor)
    if not is_raspberry_pi():
        return randrange(100)
    bus = SMBus(1)
    bus.read_i2c_block_data(module_address, sensor_code, 4) #Workaround for bug in Firmware, read is always one step behind
    data_bytes = bus.read_i2c_block_data(module_address, sensor_code, 4)
    bus.close()
    data = float.from_bytes(data_bytes, byteorder='little', signed=True)
    return data

def set_data_instant(module, sensor, data):
    module_adress = modules.get(module)
    sensor_code = sensors.get(sensor)
    if not is_raspberry_pi():
        return
    bus = SMBus(1)
    bus.write_byte_data(module_adress, sensor_code, data)
    bus.close()

def set_data_schedule(module, sensor, data, starttime, endtime):
    module_adress = modules.get(module)
    sensor_code = sensors.get(sensor)
    if not is_raspberry_pi():
        return
    data_byte = data.to_bytes(1, byteorder="big") + starttime.to_bytes(4, byteorder="big") + endtime.to_bytes(4, byteorder="big")
    bus = SMBus(1)
    bus.write_i2c_block_data(module_adress, sensor_code, data_byte)
    bus.close()  




#region Air
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

@app.put("/air/manual/temperature", tags=["Air"])
def put_air_temperature(manual: ManualSet):
    set_data_instant("Air", "AirTemperature", manual.data)
    return {"message": manual.data}

@app.put("/air/manual/humidity", tags=["Air"])
def put_air_humidity(manual: ManualSet):
    set_data_instant("Air", "AirHumidity", manual.humidity)
    return {"message": manual.data}

@app.put("/air/manual/fanspeed", tags=["Air"])
def put_air_fanspeed(manual: ManualSet):
    set_data_instant("Air", "FanSpeed", manual.fanspeed)
    return {"message": manual.data}

@app.put("/air/schedule/temperature", tags=["Air"])
def put_air_schedule_temperature(schedule: ScheduleSet):
    set_data_schedule("Air", "AirCO2", schedule.data, schedule.starttime, schedule.endtime)
    return {"message": schedule.data + schedule.starttime + schedule.endtime}

@app.put("/air/schedule/humidity", tags=["Air"])
def put_air_schedule_humidity(schedule: ScheduleSet):
    set_data_schedule("Air", "Humidity", schedule.data, schedule.starttime, schedule.endtime)
    return {"message": schedule.data + schedule.starttime + schedule.endtime}

@app.put("/air/schedule/fanspeed", tags=["Air"])
def put_air_schedule_fanspeed(schedule: ScheduleSet):
    set_data_schedule("Air", "FanSpeed", schedule.data, schedule.starttime, schedule.endtime)
    return {"message": schedule.data + schedule.starttime + schedule.endtime}
#endregion

#region Water
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

@app.put("/water/manual/flow", tags=["Water"])
def put_water_manual_flow(manual: ManualSet):
    set_data_instant("Water", "WaterFlow", manual.data)
    return {"message": manual.data}

@app.put("/water/schedule/flow", tags=["Water"])
def put_water_schedule_flow(schedule: ScheduleSet):
    set_data_schedule("Water", "WaterFlow", schedule.data, schedule.starttime, schedule.endtime)
    return {"message": schedule.data + schedule.starttime + schedule.endtime}

#endregion

#region Sun
@app.get("/sun/intensity", tags=["Sun"])
def get_sun_intensity():
    data = get_data("Sun", "SunIntensity")
    return {"Intensity": data}

@app.put("/sun/manual/intensity", tags=["Sun"])
def put_sun_manual_intensity(manual: ManualSet):
    set_data_instant("Sun", "SunIntensity", manual.data)
    return {"message": manual.data}

@app.put("/sun/schedule/intensity", tags=["Sun"])
def put_sun_schedule_intensity(schedule: ScheduleSet):
    set_data_schedule("Sun", "SunIntensity", schedule.data, schedule.starttime, schedule.endtime)
    return {"message": schedule.data + schedule.starttime + schedule.endtime}
#endregion

#region PSU
@app.get("/psu/voltage", tags=["PSU"])
def get_psu_voltage():
    data = get_data("PSU", "PSUVoltage")
    return {"PSUVoltage": data}

@app.get("/psu/current", tags=["PSU"])
def get_psu_current():
    data = get_data("PSU", "PSUCurrent")
    return {"PSUCurrent": data}

@app.get("/psu/power", tags=["PSU"])
def get_psu_power():
    data = get_data("PSU", "PSUPower")
    return {"PSUPower": data}

@app.get("/psu/status", tags=["PSU"])
def get_psu_status():
    data = get_data("PSU", "PSUStatus")
    return {"PSUStatus": data}

@app.get("/psu/fault", tags=["PSU"])
def get_psu_fault():
    data = get_data("PSU", "PSUFault")
    return {"PSUFault": data}

@app.post("/psu/clear", tags=["PSU"])
def clear_psu_fault():
    set_data_instant("PSU", "PSUFault", 0)
    return {"message": "All errors cleared"}
#endregion

#region Misc
@app.get("/misc/door", tags=["Misc"])
def get_misc_door():
    data = get_data("Misc", "Door")
    return {"Door": data}
#endregion
