from fastapi import FastAPI
from smbus2 import SMBus



description = """
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
    bus = SMBus(1)
    b = bus.read_byte_data(module_adress, sensor_code)
    bus.close()
    return b

def set_data_instant(module, sensor, data):
    module_adress = modules.get(module)
    sensor_code = sensors.get(sensor)
    bus = SMBus(1)
    bus.write_byte_data(module_adress, sensor_code, data)
    bus.close()

#Incomplete!!!
def set_data_schedule(module, sensor, data, starttime, endtime):
    module_adress = modules.get(module)
    sensor_code = sensors.get(sensor)
    bus = SMBus(1)
    bus.write_byte_data(module_adress, sensor_code, data)
    bus.close()  

#region Air
@app.get("/air/quality", tags=["Air"])
def root():
<<<<<<< HEAD
    bus = SMBus(1)
<<<<<<< HEAD
    b = bus.read_byte_data(80, 0)
=======
    b = bus.write_byte_data(85, 0, 0)
>>>>>>> 8624514 (I2C-Test implementiert)
    print(b)
    bus.close()
=======
    get_data("Air", "AirQuality")
>>>>>>> 77c4c11 (Added rudimentary I2C support)
    return {"message": "Hello World"}

@app.get("/air/co2", tags=["Air"])
def root():
    return {"message": "Hello World"}

@app.get("/air/temperature", tags=["Air"])
def root():
    return {"message": "Hello World"}

@app.get("/air/humidity", tags=["Air"])
def root():
    return {"message": "Hello World"}

@app.get("/air/fanspeed", tags=["Air"])
def root():
    return {"message": "Hello World"}

@app.put("/air/manual/temperature:{temperature}", tags=["Air"])
def root(temperature):
    return {"message": temperature}

@app.put("/air/manual/humidity:{humidity}", tags=["Air"])
def root(humidity):
    return {"message": humidity}

@app.put("/air/manual/fanspeed:{fanspeed}", tags=["Air"])
def root(fanspeed):
    return {"message": fanspeed}

@app.put("/air/schedule/temperature:{temperature}:starttime:{starttime}:endtime:{endtime}", tags=["Air"])
def root(temperature, starttime, endtime):
    return {"message": temperature + starttime + endtime}

@app.put("/air/schedule/humidity:{humidity}:starttime:{starttime}:endtime:{endtime}", tags=["Air"])
def root(humidity, starttime, endtime):
    return {"message": humidity + starttime + endtime}

@app.put("/air/schedule/fanspeed:{fanspeed}:starttime:{starttime}:endtime:{endtime}", tags=["Air"])
def root(fanspeed, starttime, endtime):
    return {"message": fanspeed + starttime + endtime}
#endregion

#region Water
@app.get("/water/level", tags=["Water"])
def root():
    return {"message": "Hello World"}

@app.get("/water/flow", tags=["Water"])
def root():
    return {"message": "Hello World"}

@app.get("/water/temperature", tags=["Water"])
def root():
    return {"message": "Hello World"}

@app.put("/water/manual/flow:{flow}", tags=["Water"])
def root(flow):
    return {"message": flow}

@app.put("/water/schedule/flow:{flow}:starttime:{starttime}:endtime:{endtime}", tags=["Water"])
def root(flow, starttime, endtime):
    return {"message": flow + starttime + endtime}

#endregion

#region Sun
@app.get("/sun/intensity", tags=["Sun"])
def root():
    return {"message": "Hello World"}

@app.put("/sun/manual/intensity:{intensity}", tags=["Sun"])
def root(intensity):
    return {"message": intensity}

@app.put("/sun/schedule/intensity:{intensity}:starttime:{starttime}:endtime:{endtime}", tags=["Sun"])
def root(intensity, starttime, endtime):
    return {"message": intensity + starttime + endtime}
#endregion

#region PSU
@app.get("/psu/voltage", tags=["PSU"])
def root():
    return {"message": "Hello World"}

@app.get("/psu/current", tags=["PSU"])
def root():
    return {"message": "Hello World"}

@app.get("/psu/power", tags=["PSU"])
def root():
    return {"message": "Hello World"}

@app.get("/psu/status", tags=["PSU"])
def root():
    return {"message": "Hello World"}

@app.get("/psu/fault", tags=["PSU"])
def root():
    return {"message": "Hello World"}

@app.post("/psu/clear", tags=["PSU"])
def root():
    return {"message": "All errors cleared"}
#endregion

#region Misc
@app.get("/misc/door", tags=["Misc"])
def root():
    return {"message": "Hello World"}
#endregion