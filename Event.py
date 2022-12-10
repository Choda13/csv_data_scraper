from datetime import datetime
from time import strptime
from dateutil.parser import parse
import numpy as np
import pandas as pd
import io
import traceback


class Event:
    def __init__(self, line=None, separator=','):
        if line is None:
            return
        words = line.split(separator)
        self.id = words[0]
        self.date = words[1]
        self.eventtype = words[2]
        self.event = words[3]
        self.value = words[4]
        self.unit = words[5]
        self.user = words[6]
        self.device = words[7]
        self.zone = words[8]
        self.channel = words[9]
        self.other = words[10]

    def Initiliaze(self, id: int, date: datetime, eventtype: str, event: str, value: float, unit: str, user: str, device: str, zone: str, channel: str, other: str = "Error"):
        self.id = id
        self.date = date
        self.eventtype = eventtype
        self.event = event
        self.value = value
        self.unit = unit
        self.user = user
        self.device = device
        self.zone = zone
        self.channel = channel
        self.other = other

    def to_dict(self):
        dict = {}
        dict["Id"] = pd.to_numeric(self.id)
        try:
            # datetime.strptime(self.date, '%d.%m.%Y %H:%M')
            dict["Date"] = parse(self.date, dayfirst=True)
        except:
            dict["Date"] = self.date
        dict["Event Type"] = self.eventtype
        dict["Event"] = self.event
        try:
            dict["Value"] = pd.to_numeric(self.value)
        except:
            dict["Value"] = pd.to_numeric(correct_mistakes(self.value))
        dict["Unit"] = self.unit
        dict["User"] = self.user
        dict["Device"] = self.device
        dict["Zone"] = self.zone
        dict["Channel"] = self.channel
        dict["Other"] = self.other

        return dict

# Load names of csv file


def GetFileNames(input_file: str):
    content = io.open(input_file, 'r', encoding='utf-8-sig').readlines()
    return [s.strip() for s in content]


def AutoDetectSeparator(filename: str):
    f = io.open(filename, 'r', encoding='utf-8-sig')
    line = f.readline()
    separator = ','
    max = 0

    for sep in [',', ';', ':', '|', '\t', '^', ' ']:
        if(line.split(sep).__len__() > max):
            max = line.split(sep).__len__()
            separator = sep

    return separator

# Correct corrupted info for 'Value' column


def correct_mistakes(data: str):
    words = data.split('.')
    value = pd.to_numeric(words[0]) + strptime(words[1], "%b").tm_mon/10
    return value


def LoadFiles(files: list[str]):
    dataframes = []

    # Load every dataframe per file
    for file in files:
        try:
            dataframes.append(pd.read_csv(
                file, delimiter=AutoDetectSeparator(file), index_col=False))
        except ValueError:
            print("Error message " + traceback.format_exc())
            continue

    return dataframes


def Convert_To_Date(value):
    try:
        # datetime.strptime(value, '%d.%m.%Y %H:%M')
        result = parse(value, dayfirst=True)
    except:
        result = value
    return result


def DataFrame_to_Events(df: pd.DataFrame):
    events = []
    for index, row in df.iterrows():
        event = Event()
        event.Initiliaze(id=row['Id'],
                         date=row['Date'],
                         eventtype=row['Event Type'],
                         event=row['Event'],
                         value=row['Value'],
                         unit=row['Unit'],
                         user=row['User'],
                         device=row['Device'],
                         zone=row['Zone'],
                         channel=row['Channel'])
        events.append(event)
    return events


def CompressAlarmEvents(events: dict[Event]):
    alarms = []
    flag = True

    for event in events:
        if flag and event.event == 'Alarm 3':
            flag = False
            alarms.append(event)
        if event.event == 'End Alarm 3' and not flag:
            flag = True
            alarms.append(event)
    
    return alarms

def CreateBeginEndAlarms3(events: dict[Event]):
    if events[0].event == 'End Alarm 3':
        events.pop(0)
    if events.__len__() % 2:
        events.pop()

    alarm_events = []
    for i in range(events.__len__()):
        data = {}
        if events[i].event == 'Alarm 3' and events[i]:
            data['Id'] = events[i].id
            data['Pocetak'] = events[i].date
            data['Kraj'] = events[i+1].date
            data['Tip alarma'] = events[i].event
            data['Vrednost '] = events[i].value
            data['Unit'] = events[i].unit
            data['Zona'] = events[i].zone
            data['Senzor'] = events[i].channel
            alarm_events.append(data)

    return alarm_events

def ExtractAlarms(events: dict[Event]):
    alarm3Flag = True
    alarm2Flag = True
    alarms2 = []
    alarms3 = []

    for event in events:
        if event.event == 'Alarm 2' and alarm2Flag:
            alarm2Flag = False
            alarms2.append(event)
        if event.event == 'End Alarm 2' and not alarm2Flag:
            alarm2Flag = True
            alarms2.append(event)

        if event.event == 'Alarm 3' and alarm3Flag:
            alarm3Flag = False
            alarms3.append(event)
        if event.event == 'End Alarm 3' and not alarm3Flag:
            alarm3Flag = True
            alarms3.append(event)
    alarms = alarms2 + alarms3

    return alarms

# append delimter to file header row


def AddColumnRaw(filenames: list[str]):
    for file in filenames:
        sep = AutoDetectSeparator(file)
        line = io.open(file, 'r', encoding='utf-8-sig').readline().strip()
        len = line.split(sep).__len__()

        if len < 11:
            line = line.strip() + sep + 'Other' + '\n'
            lines = io.open(file, 'r', encoding='utf-8-sig').readlines()
            lines[0] = line
            io.open(file, 'w', encoding='utf-8-sig').writelines(lines)
        elif (line.strip()).split(sep)[len-1] == '':
            line = line.strip() + 'Other' + '\n'
            lines = io.open(file, 'r', encoding='utf-8-sig').readlines()
            lines[0] = line
            io.open(file, 'w', encoding='utf-8-sig').writelines(lines)
