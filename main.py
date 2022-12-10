from Event import *
import tkinter as tk
from tkinter import filedialog

input_file = 'input.txt'
filenames = GetFileNames(input_file)

fns = filedialog.askopenfilenames()
filenames = fns

#Loads csv files and merge them in one dataframe
AddColumnRaw(filenames)         
dataframes = LoadFiles(filenames)
dataframe = pd.concat(dataframes)

dataframe.drop_duplicates(subset='Id', inplace=True, ignore_index=True)
dataframe['Channel'] = [str(value1)+str(value2) for value1, value2 in zip(dataframe['Channel'], dataframe['Other'])]
dataframe['Id'] = pd.to_numeric(dataframe['Id'])
dataframe['Date'] = [Convert_To_Date(value) for value in dataframe['Date']]
dataframe.sort_values(by=['Id'], inplace=True)

#Filter Data 
options = ['Info', 'Alarm', 'Alarm 3', 'Alarm 2', 'End Alarm 3', 'End Alarm 2']
alarms_dataframes = dataframe[dataframe['Event Type'].isin(options)]
alarms_dataframes = alarms_dataframes[alarms_dataframes['Event'].isin(options)]
alarms3_dataframe = alarms_dataframes[alarms_dataframes['Event'].isin(['Alarm 3', 'End Alarm 3'])]

#Group data by 'Channel' column value for easier proccessing
groups =[]
groupedby = alarms3_dataframe.groupby(['Channel'])

for group in groupedby:
    groups.append(groupedby.get_group(group[0]))

alarms3 = []
for group in groups:
    group.sort_values(by='Id', inplace=True)
    alarms = CompressAlarmEvents(DataFrame_to_Events(group))
    alarms3 += CreateBeginEndAlarms3(alarms)

alarms3.sort(key= lambda x: x['Id'])

# alarm_events = []
# for group in groups:
#     group.sort_values(by='Id', inplace=True)
#     alarm_events+=DataFrame_to_Events(group)

# alarm_events = ExtractAlarms(alarm_events)

# report_events = []
# for i in range(alarm_events.__len__()):
#     data = {}
#     if alarm_events[i].event == 'Alarm 3':
#         data['Id'] = alarm_events[i].id
#         data['Pocetak'] = alarm_events[i].date
#         data['Kraj'] = alarm_events[i+1].date
#         data['Tip alarma'] = alarm_events[i].event
#         data['Vrednost '] = alarm_events[i].value
#         data['Unit'] = alarm_events[i].unit
#         data['Zona'] = alarm_events[i].zone
#         data['Senzor'] = alarm_events[i].channel
#         report_events.append(data)

#Write to file and save 
writer = pd.ExcelWriter("Obradjeno2.xlsx", engine='xlsxwriter')
pd.DataFrame(data=[pd.Series(event) for event in alarms3]).to_excel(writer, sheet_name='Report', index=True)
alarms_dataframes.to_excel(writer, sheet_name='Alarms', index=False)
dataframe.to_excel(writer, sheet_name='SortedUnique', index=False)
writer.save()