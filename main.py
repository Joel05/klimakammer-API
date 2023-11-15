from fastapi import FastAPI
from random import randrange

import platform
def is_raspberry_pi():
    # Überprüfe, ob die Plattform "arm" und der Prozessor "arm" ist
    return platform.machine().startswith('arm') and platform.system() == 'Linux'


if is_raspberry_pi():
    from smbus2 import SMBus

description =   """
                All returnvalues are in the range of 0-255.
                Inputvalues are in the range of 0-255, except for the schedule starttime and endtime, which are in the range of 0-4294967295 (Unix timestamp).
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
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    openapi_tags=tags_metadata
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

def get_data(module, sensor):
    module_adress = modules.get(module)
    sensor_code = sensors.get(sensor)
    if not is_raspberry_pi():
        return randrange(255)
    bus = SMBus(1)
    b = bus.read_byte_data(module_adress, sensor_code)
    bus.close()
    return b

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

@app.put("/air/manual/temperature:{temperature}", tags=["Air"])
def put_air_temperature(temperature):
    set_data_instant("Air", "AirTemperature", temperature)
    return {"message": temperature}

@app.put("/air/manual/humidity:{humidity}", tags=["Air"])
def put_air_humidity(humidity):
    set_data_instant("Air", "AirHumidity", humidity)
    return {"message": humidity}

@app.put("/air/manual/fanspeed:{fanspeed}", tags=["Air"])
def put_air_fanspeed(fanspeed):
    set_data_instant("Air", "FanSpeed", fanspeed)
    return {"message": fanspeed}

@app.put("/air/schedule/temperature:{temperature}:starttime:{starttime}:endtime:{endtime}", tags=["Air"])
def put_air_schedule_temperature(temperature, starttime, endtime):
    set_data_schedule("Air", "AirCO2", 125, 1699995531, 1699995900)
    return {"message": temperature + starttime + endtime}

@app.put("/air/schedule/humidity:{humidity}:starttime:{starttime}:endtime:{endtime}", tags=["Air"])
def put_air_schedule_humidity(humidity, starttime, endtime):
    set_data_schedule("Air", "Humidity", 125, 1699995531, 1699995900)
    return {"message": humidity + starttime + endtime}

@app.put("/air/schedule/fanspeed:{fanspeed}:starttime:{starttime}:endtime:{endtime}", tags=["Air"])
def put_air_schedule_fanspeed(fanspeed, starttime, endtime):
    set_data_schedule("Air", "FanSpeed", 125, 1699995531, 1699995900)
    return {"message": fanspeed + starttime + endtime}
#endregion

#region Water
@app.get("/water/level", tags=["Water"])
def root():
    data = get_data("Water", "WaterLevel")
    return {"Level": data}

@app.get("/water/flow", tags=["Water"])
def root():
    data = get_data("Water", "WaterFlow")
    return {"Flow": data}

@app.get("/water/temperature", tags=["Water"])
def root():
    data = get_data("Water", "WaterTemperature")
    return {"Temperature": data}

@app.put("/water/manual/flow:{flow}", tags=["Water"])
def root(flow):
    set_data_instant("Water", "WaterFlow", flow)
    return {"message": flow}

@app.put("/water/schedule/flow:{flow}:starttime:{starttime}:endtime:{endtime}", tags=["Water"])
def root(flow, starttime, endtime):
    set_data_schedule("Water", "WaterFlow", flow, starttime, endtime)
    return {"message": flow + starttime + endtime}

#endregion

#region Sun
@app.get("/sun/intensity", tags=["Sun"])
def root():
    data = get_data("Sun", "SunIntensity")
    return {"Intensity": data}

@app.put("/sun/manual/intensity:{intensity}", tags=["Sun"])
def root(intensity):
    set_data_instant("Sun", "SunIntensity", intensity)
    return {"message": intensity}

@app.put("/sun/schedule/intensity:{intensity}:starttime:{starttime}:endtime:{endtime}", tags=["Sun"])
def root(intensity, starttime, endtime):
    set_data_schedule("Sun", "SunIntensity", intensity, starttime, endtime)
    return {"message": intensity + starttime + endtime}
#endregion

#region PSU
@app.get("/psu/voltage", tags=["PSU"])
def root():
    data = get_data("PSU", "PSUVoltage")
    return {"PSUVoltage": data}

@app.get("/psu/current", tags=["PSU"])
def root():
    data = get_data("PSU", "PSUCurrent")
    return {"PSUCurrent": data}

@app.get("/psu/power", tags=["PSU"])
def root():
    data = get_data("PSU", "PSUPower")
    return {"PSUPower": data}

@app.get("/psu/status", tags=["PSU"])
def root():
    data = get_data("PSU", "PSUStatus")
    return {"PSUStatus": data}

@app.get("/psu/fault", tags=["PSU"])
def root():
    data = get_data("PSU", "PSUFault")
    return {"PSUFault": data}

@app.post("/psu/clear", tags=["PSU"])
def root():
    set_data_instant("PSU", "PSUFault", 0)
    return {"message": "All errors cleared"}
#endregion

#region Misc
@app.get("/misc/door", tags=["Misc"])
def root():
    data = get_data("Misc", "Door")
    return {"Door": data}
#endregion
