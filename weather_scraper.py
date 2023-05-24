import argparse #creates command-line interfaces
import requests #library used to make http requests easier ***MANDATORY
import csv #allows us to read and write csv files ***MANDATORY
import lxml.html as lh #used for parsing and manipulating HTML and XML documents. ideal for web scraping ***MANDATORY
import unicodedata #
import re
from datetime import date, datetime, timedelta #Imports the date class, which represents a date (year, month, and day) in Python. timedelta is used for arithmetic operations on datetimes

###Classes (removes the need of util, and parser files)

##Utils
class Utils:
    session = requests.Session()
    weather_station_url = None

    def __init__(self, session, weather_station_url):
        self.session = session
        self.weather_station_url = weather_station_url
        
    @classmethod
    def date_range_generator(cls, start, end = date.today()):
        for i in range(int ((end - start).days) + 1):
            yield start + timedelta(i)

    @classmethod
    def date_url_generator(cls, weather_station_url, start_date, end_date = date.today()):
        date_range = Utils.date_range_generator(start_date, end_date)
        for date in date_range:
            date_string = date.strftime("%Y-%m-%d")
            url = f'{weather_station_url}/table/{date_string}/{date_string}/daily'
            yield date_string, url
    
    @classmethod
    def date_url_array(cls, date_url_gen):
        date_url_arr = []
        for url in date_url_gen:
            date_url_arr.append(url)
        return date_url_arr

    @classmethod
    def fetch_data_table(cls, url):
        """
            Fetches a weather data url and checks if there are data entries for that date
        """
        html_string = cls.session.get(url)
        doc = lh.fromstring(html_string.content)
        data_table = doc.xpath('//*[@id="main-page-content"]/div/div/div/lib-history/div[2]/lib-history-table/div/div/div/table/tbody/tr')
        if data_table != []:
            return True
        else:
            return False

    @classmethod
    def first_data_url(cls, date_arr, low, high):

        if(high >= low):
            mid = low + (high - low) // 2
            print(f"low is {low} - {date_arr[low]}")
            print(f"high is {high} - {date_arr[high]}")
            print(f"mid is {mid} - {date_arr[mid]}")
            print(f"----//----")

            date_string_1 = date_arr[mid].strftime("%Y-%m-%d")
            date_string_2 = date_arr[mid - 1].strftime("%Y-%m-%d")
            url_1 = f'{Utils.weather_station_url}/table/{date_string_1}/{date_string_1}/daily'
            url_2 = f'{Utils.weather_station_url}/table/{date_string_2}/{date_string_2}/daily'
            data_1 = Utils.fetch_data_table(url_1)
            data_2 = Utils.fetch_data_table(url_2)

            if((data_1 and not data_2)):
                # result found, return result
                print(f'First date found! {date_arr[mid]}')
                print(url_1)
                return date_arr[mid]
            elif(data_1 == True):
                return Utils.first_data_url(date_arr, low, (mid - 1))
            elif(data_1 == False):
                return Utils.first_data_url(date_arr, (mid + 1), high)
        
        print(f'\nFirst date not found!')
        return -1


    @classmethod
    def find_first_data_entry(cls, weather_station_url, start_date):
        """
            Given a station URL, finds the first date_url where data exists.
        """
        Utils.weather_station_url = weather_station_url
        date_gen = Utils.date_range_generator(start_date)
        date_arr = Utils.date_url_array(date_gen)

        n = len(date_arr)

        print("\n** Initializing binary search to find the first date with data **")
        first_date_with_data = Utils.first_data_url(date_arr, 0, n - 1)
        return first_date_with_data
##end utils

##Parser
class Parser:
    @staticmethod
    def format_key(key: str) -> str:
        # Replace white space and delete dots
        return key.replace(' ', '_').replace('.', '')

    @staticmethod
    def parse_html_table(date_string: str, history_table: list) -> dict:

        table_rows = [tr for tr in history_table[0].xpath('//tr') if len(tr) == 12]
        headers_list = []
        data_rows = []

        # set Table Headers
        for header in table_rows[0]:
            headers_list.append(header.text)

        for tr in table_rows[1:]:
            row_dict = {}
            for i, td in enumerate(tr.getchildren()):
                td_content = unicodedata.normalize("NFKD", td.text_content())

                # set date and time in the first 2 columns
                if i == 0:
                    date = datetime.strptime(date_string, "%Y-%m-%d")
                    time = datetime.strptime(td_content, "%I:%M %p")
                    row_dict['Date'] = date.strftime('%Y/%m/%d')
                    row_dict['Time'] = time.strftime('%I:%M %p')
                else:
                    row_dict[Parser.format_key(headers_list[i])] = td_content

            data_rows.append(row_dict)
        
        return data_rows
##end parser

##unitconverer
class ConvertToSystem:
    supported_systems = ["metric", "imperial"]
    round_to_decimals = 2
    extract_numbers_pattern = "\d*\.\d+|\d+"

    def __init__(self, system: str):
        if system not in self.supported_systems:
            raise ValueError('unit system not supported')
        else:
            self.system = system

    def temperature(self, temp_string: str):
        try:
            fahrenheit = float(re.findall(self.extract_numbers_pattern, temp_string)[0]) if temp_string else 'NA'
            if self.system == "metric":
                celsius = (fahrenheit - 32) * 5/9
                return round(celsius, self.round_to_decimals)
            else:
                return fahrenheit

        except Exception as e:
            print(f'{e}! probably caused by an empty row in the data')
            return 'NA'
            
    def dew_point(self, dew_point_string: str):
        try:
            fahrenheit = float(re.findall(self.extract_numbers_pattern, dew_point_string)[0]) if dew_point_string else 'NA'
            if self.system == "metric":
                celsius = (fahrenheit - 32) * 5/9
                return round(celsius, self.round_to_decimals)
            else:
                return fahrenheit
            
        except Exception as e:
            print(f'{e}! probably caused by an empty row in the data')
            return 'NA'

    def humidity(self, humidity_string: str):
        try:
            humidity = float(re.findall(self.extract_numbers_pattern, humidity_string)[0]) if humidity_string else 'NA'
            return humidity
        
        except Exception as e:
            print(f'{e}! probably caused by an empty row in the data')
            return 'NA'

    def speed(self, speed_string: str):
        try:
            mph = float(re.findall(self.extract_numbers_pattern, speed_string)[0]) if speed_string else 'NA'
            if self.system == "metric":
                kmh = mph * 1.609
                return round(kmh, self.round_to_decimals)
            else:
                return mph

        except Exception as e:
            print(f'{e}! probably caused by an empty row in the data')
            return 'NA'

    def pressure(self, pressure_string: str):
        try:
            inhg = float(re.findall(self.extract_numbers_pattern, pressure_string)[0]) if pressure_string else 'NA'
            if self.system == "metric":
                hpa = inhg * 33.86389
                return round(hpa, self.round_to_decimals)
            else:
                return inhg
                
        except Exception as e:
            print(f'{e}! probably caused by an empty row in the data')
            return 'NA'
    
    def precipitation(self, precip_string: str):
        try:
            inches = float(re.findall(self.extract_numbers_pattern, precip_string)[0]) if precip_string else 'NA'
            if self.system == "metric":
                mm = inches * 25.4
                return round(mm, self.round_to_decimals)
            else:
                return inches
                
        except Exception as e:
            print(f'{e}! probably caused by an empty row in the data')
            return 'NA'

    def uv(self, uv_string: str):
        try:
            measure = float(re.findall(self.extract_numbers_pattern, uv_string)[0]) if uv_string else 'NA'
            return measure
            
        except Exception as e:
            print(f'{e}! probably caused by an empty row in the data')
            return 'NA'

    def solar(self, solar_string: str):
        try:
            measure = float(re.findall(self.extract_numbers_pattern, solar_string)[0]) if solar_string else 'NA'
            return measure
            
        except Exception as e:
            print(f'{e}! probably caused by an empty row in the data')
            return 'NA'

    def clean_and_convert(self, dict_list: list):
        converted_dict_list = []
        for dict in dict_list:
            converted_dict = {}
            for key, value in dict.items():
                if key == 'Date':
                    converted_dict['Date'] = value
                if key == 'Time':
                    converted_dict['Time'] = value
                if key ==  'Temperature':
                    converted_dict['Temperature'] = self.temperature(value)
                if key ==  'Dew_Point':
                    converted_dict['Dew_Point'] = self.dew_point(value)
                if key ==  'Humidity':
                    converted_dict['Humidity'] = self.humidity(value)
                if key ==  'Wind':
                    converted_dict['Wind'] = value
                if key ==  'Speed':
                    converted_dict['Speed'] = self.speed(value)
                if key ==  'Gust':
                    converted_dict['Gust'] = self.speed(value)
                if key ==  'Pressure':
                    converted_dict['Pressure'] = self.pressure(value)
                if key ==  'Precip_Rate':
                    converted_dict['Precip_Rate'] = self.precipitation(value)
                if key ==  'Precip_Accum':
                    converted_dict['Precip_Accum'] = self.precipitation(value)
                if key ==  'UV':
                    converted_dict['UV'] = self.uv(value)
                if key ==  'Solar':
                    converted_dict['Solar'] = self.solar(value)

            converted_dict_list.append(converted_dict)

        return converted_dict_list
##end unit converter





# Define command line arguments
parser = argparse.ArgumentParser(description='Process start and end dates.')
parser.add_argument('--start_date', type=str, help='Start date in YYYY-MM-DD format')
parser.add_argument('--end_date', type=str, help='End date in YYYY-MM-DD format')

args = parser.parse_args()

# Convert command line arguments to date format. Sets default values if not specified
if args.start_date:
    START_DATE = datetime.strptime(args.start_date, '%Y-%m-%d').date()
else:
    START_DATE = date.today() - timedelta(days=1)

if args.end_date:
    END_DATE = datetime.strptime(args.end_date, '%Y-%m-%d').date()
else:
    END_DATE = date.today()



# set to "metric" or "imperial"
UNIT_SYSTEM = "metric"
# UNIT_SYSTEM = "imperial"

# Automatically find first date where data is logged
FIND_FIRST_DATE = False

#Reads in one weather station 
URLS = ['https://www.wunderground.com/dashboard/pws/KTNKNOXV761']



def scrap_station(weather_station_url): #

    session = requests.Session()
    timeout = 5
    global START_DATE
    global END_DATE
    global UNIT_SYSTEM
    global FIND_FIRST_DATE

#    if FIND_FIRST_DATE:
#        # find first date
#        first_date_with_data = Utils.find_first_data_entry(weather_station_url=weather_station_url, start_date=START_DATE)
#        # if first date found
#        if(first_date_with_data != -1):
#            START_DATE = first_date_with_data
    url_gen = Utils.date_url_generator(weather_station_url, START_DATE, END_DATE)
    station_name = weather_station_url.split('/')[-1]
    file_name = f'{station_name}_2023.csv'

    with open(file_name, 'a+', newline='') as csvfile:
        fieldnames = ['Date', 'Time',	'Temperature',	'Dew_Point',	'Humidity',	'Wind',	'Speed',	'Gust',	'Pressure',	'Precip_Rate',	'Precip_Accum',	'UV',   'Solar']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write the correct headers to the CSV file
        if UNIT_SYSTEM == "metric":
            # 12:04 AM	24.4 C	18.3 C	69 %	SW	0.0 km/h	0.0 km/h	1,013.88 hPa	0.00 mm	0.00 mm	0	0 w/m²
            writer.writerow({'Date': 'Date', 'Time': 'Time',	'Temperature': 'Temperature_C',	'Dew_Point': 'Dew_Point_C',	'Humidity': 'Humidity_%',	'Wind': 'Wind',	'Speed': 'Speed_kmh',	'Gust': 'Gust_kmh',	'Pressure': 'Pressure_hPa',	'Precip_Rate': 'Precip_Rate_mm',	'Precip_Accum': 'Precip_Accum_mm',	'UV': 'UV',   'Solar': 'Solar_w/m2'})
        elif UNIT_SYSTEM == "imperial":
            # 12:04 AM	75.9 F	65.0 F	69 %	SW	0.0 mph	0.0 mph	29.94 in	0.00 in	0.00 in	0	0 w/m²
            writer.writerow({'Date': 'Date', 'Time': 'Time',	'Temperature': 'Temperature_F',	'Dew_Point': 'Dew_Point_F',	'Humidity': 'Humidity_%',	'Wind': 'Wind',	'Speed': 'Speed_mph',	'Gust': 'Gust_mph',	'Pressure': 'Pressure_in',	'Precip_Rate': 'Precip_Rate_in',	'Precip_Accum': 'Precip_Accum_in',	'UV': 'UV',   'Solar': 'Solar_w/m2'})
        else:
            raise Exception("please set 'unit_system' to either \"metric\" or \"imperial\"! ")

        for date_string, url in url_gen:
            try:
                print(f'🌞 🌨 ⛈ from {url}')
                history_table = False
                while not history_table:
                    html_string = session.get(url, timeout=timeout)
                    doc = lh.fromstring(html_string.content)
                    history_table = doc.xpath('//*[@id="main-page-content"]/div/div/div/lib-history/div[2]/lib-history-table/div/div/div/table/tbody')
                    if not history_table:
                        print("refreshing session")
                        session = requests.Session()


                # parse html table rows
                data_rows = Parser.parse_html_table(date_string, history_table)

                # convert to metric system
                converter = ConvertToSystem(UNIT_SYSTEM)
                data_to_write = converter.clean_and_convert(data_rows)
                    
                print(f'Saving {len(data_to_write)} rows')
                writer.writerows(data_to_write)
            except Exception as e:
                print(e)



for url in URLS: #this is what makes it repeat through all the stations
    url = url.strip()
    print(url)
    scrap_station(url)