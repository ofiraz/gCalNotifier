import datetime
import tzlocal

def get_now_datetime():
    return(datetime.datetime.now().astimezone())

def format_date_for_api(date_value):
    #Printing in this format 2023-10-31T12:30:00-07:00
    return date_value.strftime('%Y-%m-%dT%H:%M:%S%z')

def get_time_now_and_one_day_ahead():
    tz = tzlocal.get_localzone()
    now = datetime.datetime.now(tz)
    one_day_ahead = now + datetime.timedelta(days=1)

    return(
        format_date_for_api(now),
        format_date_for_api(one_day_ahead))