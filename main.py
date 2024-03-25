import struct
import time
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from random import randrange
import json
import requests
import pandas as pd
from io import StringIO
from datetime import datetime
from fastapi.responses import JSONResponse


import platform


def is_raspberry_pi():
    # Überprüfe, ob die Plattform "linux" und der Prozessor "aarch64" ist
    return platform.machine().startswith('aarch64') and platform.system() == 'Linux'


if is_raspberry_pi():
    from smbus2 import SMBus

#region hivehours
# Get the current date
now = datetime.today().strftime('%Y-%m-%d')

# Endpoint and headers
url = 'https://beta-gql.hive.com/graphql'
headers = {
    'Accept': 'application/json, multipart/mixed',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-AT,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,fr-FR;q=0.6,fr;q=0.5,de;q=0.4',
    'Api-Key': '',
    'Cache-Control': 'no-cache',
    'Content-Type': 'application/json',
    'Dnt': '1',
    'Origin': 'https://developers.hive.com',
    'Pragma': 'no-cache',
    'Referer': 'https://developers.hive.com/',
    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# GraphQL query
payload = {
    "query": """
        query MyQuery {
            getTimesheetReportingCsvExportData(
                workspaceId: "oRdNLcDeGWs8Sdjwz"
                startDate: "2023-01-01"
                endDate: """ + '"' + now + '"' + """
                columns: hours
                groupBy: DAY
            )
        }
    """,
    "variables": None,
    "operationName": "MyQuery"
}

# Convert the payload to a JSON format
data = json.dumps(payload)

# Make the request
response = requests.post(url, headers=headers, data=data)

# Check for errors and print the response
if response.status_code == 200:
    totalstring = ((response.json()["data"]["getTimesheetReportingCsvExportData"]))
else:
    print("Query failed to run with a status code of {}. {}".format(response.status_code, data))


#print(totalstring)

# Specify column names explicitly
column_names = ["Person", "Email", "Role", "Project", "Other costs", "Category", "Approver", "Date unit", "Hours", "Date", "Est hours", "Utiliz", "Billed amount", "Utilization Target"]


data = StringIO(totalstring)
df = pd.read_csv(data, names=column_names, header=None, skiprows=1)

#print(df[["Person", "Email", "Role", "Project", "Other costs", "Category", "Approver", "Date unit", "Date", "Hours", "Est hours", "Utiliz", "Billed amount", "Utilization Target"]])

# Convert the 'Hours' column to numeric, to handle any non-numeric entries gracefully
df['Hours'] = pd.to_numeric(df['Hours'], errors='coerce')

# Calculating total hours
total_hours = df.groupby("Person")["Hours"].sum()
#endregion



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
    "Sensors": 0x71,
    "Water": 0x11,
    "Sun": 0x12,
    "PSU": 0x13,
    "Misc": 0x14,
    "Fans": 0x70
}

sensors = {
    "AirPressure":0x01,
    "AirTemperature":0x02,
    "Brightness":0x03,
    "UV-Brightness":0x04,
    "AirHumidity":0x05,
    "FanSpeed":0x14,
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

#region setValue
@app.put("/setValue", tags=["setValue"])
def setValue(schedule: ScheduleSet):
    set_data(schedule)
    return {"message": schedule}

 #endregion


# region Air
@app.get("/air/pressure", tags=["Air"])
def get_air_quality():
    data = get_data("Sensors", "AirPressure")
    return {"AirPressure": data[0]}


@app.get("/air/temperature", tags=["Air"])
def get_air_temperature():
    data = get_data("Sensors", "AirTemperature")
    return {"AirTemperature": data[0]}

@app.get("/air/humidity", tags=["Air"])
def get_air_humidity():
    data = get_data("Sensors", "AirHumidity")
    return {"AirHumidity": data[0]}


#endregion

# region Fans

@app.get("/fan/fanspeed", tags=["Fans"])
def get_air_fanspeed():
    data = get_data("Fans", "FanSpeed")
    return {"Fan 1 rpm": data[0], "Fan 2 rpm": data[1]}


#endregion

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

 #endregion

#region Sun

@app.get("/sun/brightness", tags=["Sun"])
def get_sun_brightness():
    data = get_data("Sensors", "Brightness")
    return {"SunBrightness": data}


@app.get("/sun/uvbrightness", tags=["Sun"])
def get_sun_uvBrightness():
    data = get_data("Sensors", "UV-Brightness")
    return {"UVBrightness": data}

#endregion

#region PSU
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


@app.get("/psu/internaltemperature", tags=["PSU"])
def get_psu_internaltemperature():
    data = get_data("PSU", "PSUInternalTemperature")
    return {"PSUInternalTemperature1": data[0]+10, "PSUInternalTemperature2": data[1]+10} #Calibration


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
#endregion


#region Hivehours
@app.get("/")
def get_root():
    return {"Status" : "OK"}

@app.get("/hours")
def get_hours():
    # Check if df is defined and not empty
    if 'df' in globals() and not df.empty:
        # Ensure the required columns exist in df
        if 'Person' in df.columns and 'Hours' in df.columns:
            # Group by 'Person' and sum 'Hours'
            total_hours = df.groupby('Person')['Hours'].sum()

            # Get the current Unix timestamp
            timestamp = int(time.time())

            # Convert to list of dictionaries with 'email', 'Number', and 'timestamp'
            result = [{"email": person, "Number": hours} for person, hours in total_hours.items()]

            return JSONResponse(content=result)
        else:
            # Columns not found
            return JSONResponse(content={"error": "Required columns not found in DataFrame"}, status_code=400)
    else:
        # DataFrame not defined or empty
        return JSONResponse(content={"error": "DataFrame is not defined or empty"}, status_code=400)




@app.post("/TTS")
async def create_upload_file(file: UploadFile):
    return {"filename": file.filename}

# endregion