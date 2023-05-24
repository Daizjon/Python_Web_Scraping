# Python_Web_Scraping
Web scraping implementation that was used for a bigger project.

## This is the most recent version of the weather scrapper. Improvements include:
+ <b>One file.</b> Instead of using config.py, utils.py, parser.py, UnitConverter.py,  and weatherstation.txt we have one file that does it all with a cleaned up version of code. <br>
+ <b>Command line arguments.</b> Instead of hard coding the range of dates we can take the values at command line. <br>
+ <b>Range of dates.</b> Instead of picking a number like 5 which would display the last 5 days, users can now imput a range of days. <br>

## Example to run the code. 
Command line arguments are optional. If not specified then the default start date will be yesterday and the default end date will be today.
```python
python weather_scraper.py --start_date 2023-02-10 --end_date 2023-02-13
```  
## Can also run -h or --help
```python
python weather_scraper.py --help
```  
In order to help the user see specifications such as shown below.
```python
usage: your_script_name.py [-h] [--start_date START_DATE] [--end_date END_DATE]

Process start and end dates.

optional arguments:
  -h, --help            show this help message and exit
  --start_date START_DATE
                        Start date in YYYY-MM-DD format
  --end_date END_DATE   End date in YYYY-MM-DD format

```  
