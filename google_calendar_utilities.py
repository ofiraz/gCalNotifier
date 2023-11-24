import os.path
import datetime
import time
import traceback


from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_calendar_list_for_account(logger, google_account):
    google_account_name = google_account["account name"]
    additional_calendars = google_account.get("additional calenadars")

    # Init the list
    calendar_list_for_account = [
        {
            'calendar name' : "Primary",
            'calendar id' : "primary"
        }
    ]
    
    # Connect to the Google Account
    creds = None
    Credentials_file = 'app_credentials.json'
    token_file = google_account_name + '_token.json'

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            logger.info("Creating a token for " + google_account_name)
            flow = InstalledAppFlow.from_client_secrets_file(
                Credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    logger.info("Printing calendars for " + google_account_name)
    page_token = None
    while True:
        calendar_list = service.calendarList().list(pageToken=page_token).execute()

        for calendar_list_entry in calendar_list['items']:
            prefix_text = "Don't include - "
            if(additional_calendars and (calendar_list_entry['summary'] in additional_calendars)):
                prefix_text = "*** Include - "
                calendar_list_entry_to_add = {
                    'calendar name' : calendar_list_entry['summary'],
                    'calendar id' : calendar_list_entry['id']
                }
                calendar_list_for_account.append(calendar_list_entry_to_add)
            logger.info(prefix_text + " " + calendar_list_entry['summary'] + " " + calendar_list_entry['id'])

        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            break

    google_account["calendar list"] = calendar_list_for_account
    logger.info("The calendar list for " + google_account_name + ":")
    logger.info(str(calendar_list_for_account))

def get_events_from_google_cal(logger, google_account, cal_id, event_id = None):    
    # Connect to the Google Account
    creds = None
    Credentials_file = 'app_credentials.json'
    token_file = google_account + '_token.json'

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            logger.info("Creating a token for " + google_account)
            flow = InstalledAppFlow.from_client_secrets_file(
                Credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    if (event_id is None):
        # Get the next 10 events
        now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
        logger.debug('Getting the upcoming 10 events')

        events_result = service.events().list(
            calendarId=cal_id, 
            timeMin=now,
            #timeMin='2023-10-31T12:30:00-07:00', 
            #timeMax='2023-10-31T13:00:00-07:00',
            maxResults=10, 
            singleEvents=True,
            orderBy='startTime').execute()

        events = events_result.get('items', [])

        return(events)

    else:
        # Get a specitic event
        raw_event = service.events().get(
        calendarId=cal_id,
        eventId=str(event_id)).execute()

        return(raw_event)

class ConnectivityIssue(Exception):
    pass

Networking_excTypes = {
    "ServerNotFoundError",
    "timeout",
    "TimeoutError",
    "ConnectionResetError",
    "TransportError",
    "SSLCertVerificationError",
    "SSLEOFError"
}

Networking_OSError_excMesg = {
    "[Errno 51] Network is unreachable",
    "[Errno 65] No route to host"
}

def get_events_from_google_cal_with_try(logger, google_account, cal_id, event_id = None):
    num_of_retries = 0
    none_networking_known_exception = False

    while True:
        try: # In progress - handling intermittent exception from the Google service
            raw_events = get_events_from_google_cal(logger, google_account, cal_id, event_id)
        except Exception as e:
            excType = str(e.__class__.__name__)
            excMesg = str(e)

            if (
                (excType in Networking_excTypes) 
                or ((excType == "OSError") and (excMesg in Networking_OSError_excMesg))
            ):
                # Exceptions that chould be intermittent due to networking issues.

                logger.debug('Networking issue with Exception type ' + excType)

            else:
                # Not a known exception

                none_networking_known_exception = True

                logger.info("Error in get_events_from_google_cal_with_try for " + google_account)
                logger.info('Exception type ' + excType)
                logger.info('Exception msg ' + excMesg)

                logger.info(traceback.format_exc())

            num_of_retries = num_of_retries + 1

            if (num_of_retries > 2):
                if (none_networking_known_exception):
                    # An unknown exception has happened
                    raise
                else:
                    # Only known connectivity issues have happend
                    logger.info('Only known connectivity issues have happend')
                    raise ConnectivityIssue()

            else:
                # Sleep for 2 seconds and retry
                time.sleep(2)
        else:
            # Getting the event was successful
            return(raw_events)

