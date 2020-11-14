from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import requests
import datetime
import json
import sys
import time

#home = str(input("Please enter your home address, to allow for auto-fill: "))
home = "N208EP,London,England,United Kingdom"

# If modifying scopes, delete the file token.pickle
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def main():
    print("Program Started: If you encounter any errors please manually update the data onto the DATA_compile spreadsheet")
    AmbeeKey,VCKey,DatabaseID,DATA_compileID = GetKeys()
    sheets_data = StripSheets(DatabaseID)
    print(sheets_data)
    parsed_sheets_data,locations_list = ParseForInsertion(sheets_data,",")
    print(parsed_sheets_data)
    UpdateCompiledData(parsed_sheets_data,DATA_compileID) #updates the compiled data with what's been stripped
    UpdateEnviroData(locations_list,parsed_sheets_data,AmbeeKey,VCKey,DATA_compileID)

def GetKeys():
    with open('privatekeys.json') as json_file:
        data = json.load(json_file)
    return data[0]['Ambee'],data[0]['Visual Crossing'], data[1]['Database'],data[1]['DATA_compile']

def ParseForInsertion(org_data,seperator):
    locations = []
    for day in range(len(org_data)):
        org_data[day][2] = seperator.join(org_data[day][2])
        org_data[day][3] = seperator.join(org_data[day][3])
        curr = org_data[day].pop(9)
        locations.append(curr)
    print(locations)
    return org_data,locations

def UpdateEnviroData(locations_list,parsed_sheets_data,AmbeeKey,VCKey,ID):
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('sheets', 'v4', credentials=creds)

#Update compiled data with stipped locations incase a change has been made

#Retrieve current contents of compiled data
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=ID,
                                range='Sheet1!J2:J').execute()
    values = result.get('values', [])
    print(values)

    for day in range(len(values)):
        if values[day][0] != locations_list[day]:#location differs, update info
            UpdateEnviroRow(day,locations_list[day],parsed_sheets_data,AmbeeKey,VCKey)

    print("Progress Update: Main database has been updated with new user-inputted data..." + "[" +'{0} cells updated'.format(result.get('totalUpdatedCells'))+ "]")

def UpdateEnviroRow(day,new_location,parsed_sheets_data,AmbeeKey,VCKey):
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('sheets', 'v4', credentials=creds)

    enviro_data = [None,None,None,None,None,new_location] #do not modify entry 4 as it is a placeholder for skin-rating
    date = parsed_sheets_data[day][0]
    try:
        temp,dew_point,lat,long = GetTempDew(date,new_location,VCKey)
    except:
        print("*ERROR 2: Could not access the Visual Crossing Weather api - check number of available requests")
        sys.exit()
    try:
        AQI,major_polt = GetPol(date,lat,long,AmbeeKey)
    except:
        print("*ERROR 2: Could not access the Ambee api for pollution data - check number of available requests")
        sys.exit()


def GetPol(date,lat,long,Key):
    dateold = date
    date = datetime.datetime.strptime(date, '%d %B %Y').strftime('%Y-%m-%d')
    bulk_data = requests.get("https://api.ambeedata.com/history/by-lat-lng?lat="+str(lat)+"&lng="+str(long)+"&from="+date+"%2012%3A00%3A00&to="+date+"%2013%3A00%3A00", headers = {"x-api-key": Key}).json()
    AQI = bulk_data['data'][0]['AQI']
    try:
        AQI = bulk_data['data'][0]['AQI']
    except:
        AQI = 'Unknown'
        print("*ERROR 1: Air Quality Index data was unavaiable for " + str(dateold))

    try:
        major_polt = bulk_data['data'][0]['majorPollutant']
    except:
        major_polt = 'Unknown'
        print("*ERROR 1: Major Pollutant Data was unavaiable for " + str(dateold))

    try:
        bulk_data = requests.get("https://air-quality-forecast.weather.mg/pollen/search?locatedAt="+str(lat)+","+str(long)+"&fields=issuedAt,pollenIndex")



    return AQI,major_polt

def GetTempDew(date,location,Key):
    dateold = date
    date = datetime.datetime.strptime(date, '%d %B %Y').strftime('%Y-%m-%d')
    bulk_data = requests.get("https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/weatherdata/history?&aggregateHours=24&startDateTime=" + date + "T00:00:00&endDateTime="+ date +"T00:00:00&unitGroup=uk&contentType=json&dayStartTime=0:0:00&dayEndTime=0:0:00&location="+location+"&key="+Key).json()

    try:
        temp = bulk_data['locations'][location]['values'][0]['temp']
    except:
        temp = "Unknown"
        print("*ERROR 1: Temperature Data was unavaiable for " + str(dateold)+" at location " + str(location))

    try:
        dew_point = bulk_data['locations'][location]['values'][0]['dew']
    except:
        dew_point = "Unknown"
        print("*ERROR 1: Dew Point Data was unavaiable for " + str(dateold)+" at location " + str(location))

    lat =  bulk_data['locations'][location]['latitude']
    long = bulk_data['locations'][location]['longitude']
    return temp,dew_point,lat,long


def StripSheets(ID):
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId= ID,
                                range='Entry Log!A2:G').execute()
    values = result.get('values', [])

    DATA = []

    DATE = []
    OUT = "0"
    FOODS = []
    EXT = []
    POLLEN = None
    POLLUTION = None
    DEW_POINT = None
    TEMP = None
    SKIN_RATING = -1
    location = home

    count = 0

    if not values:
        print('No data found.')
    else:
        #Strip data from sheets
        for row in values:
            if row[0] != '':
                if DATE != []:
                    DATA.append([DATE,OUT,FOODS,EXT,POLLEN,POLLUTION,DEW_POINT,TEMP,SKIN_RATING,location])
                    count+=1
                try:
                    DATE = str(row[0])
                    OUT = str(row[3])
                    SKIN_RATING = int(row[4])
                except:
                    #date entered but Skin rating is missing, so output what we have
                    print("Progress Update: Data for " + str(count) + " days has been stripped from Sheets...")
                    return DATA
                if str(row[1]) != "":
                    FOODS = [str(row[1])]
                else:
                    FOODS = []
                if str(row[2]) != "":
                    EXT =[str(row[2])]
                else:
                    EXT =[]
                if str(row[5]) != "":
                    location = str(row[5])
                else:
                    location = home
            else:
                if str(row[1]) != "":
                    FOODS.append(str(row[1]))
                if str(row[2]) != "":
                    EXT.append(str(row[2]))
        DATA.append([DATE,OUT,FOODS,EXT,POLLEN,POLLUTION,DEW_POINT,TEMP,SKIN_RATING,location])
        count+=1
        print("Progress Update: Data for " + str(count) + " days has been stripped from Sheets...")
        return DATA

def UpdateCompiledData(stripped_data, ID):
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('sheets', 'v4', credentials=creds)

#data to be entered and where it is to be placed are defined
    data = [{'range': 'Sheet1!A2:I','values': stripped_data}]
    body = {'valueInputOption': "USER_ENTERED",'data': data}
#data is inserted
    result = service.spreadsheets().values().batchUpdate(
    spreadsheetId = ID, body=body).execute()
    print("Progress Update: Main database has been updated with new food, medicine/external and skin rating data " + "[" +'{0} cells of data written'.format(result.get('totalUpdatedCells'))+ "]...")

if __name__ == '__main__':
    main()
