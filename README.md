# gCalNotifier
A Python program to grpahically display notifications about coming meetings in one or more Google calendars.

# Deployment
* Clone the repository.
* Python 3.x.
* Optional - create a Python virtual env:

```
python3 -m venv <path>/gCalNotifier
source bin/activate
```
* Install the following Python modules:

```
pip3 install pyqt5`
pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib`
pip3 install validators`
```
* Contact me to get the `app_credentials.json` file, and locate it in the directory from which you will run the application.

# Configuration
Edit the file gCalNotifier.json in the directory from which you will run the application.

The format of the file is:
```
{
    "google accounts": 
    [
        "ofiraz@gmail.com",
        "<account 2>",
        ...
        "<account n>
    ],
    "log level":<log level for the log file>, 
    "refresh frequency":<refresh frequency in seconds>
}
```

The `log level` parameter is optional. The value should be numeric according to [this table](https://docs.python.org/3/library/logging.html#logging-levels). The default value is 20 (`INFO`)


The `refresh frequency` is optional. The default value is 30 seconds.

# Allowing connection from Google to the application
There is a need to allow the application to access the Google accounts that are set in the configuration file.
This is required on the first access to each account, as well as periodically based on the token length defined by Google.

When such is needed, the application (as a result of calling the Google interface) will open your browser and ask for permission.
The permission is for a read-only access to te Calendar of that Google account.
If more than one account is configured, the standard output of the application displays the relevant Google account for which the permission is needed.
Follow the directions in the browser to provide the needed access.

# Credits
All icons in the application are used under permission from [Icons8](https://icons8.com)