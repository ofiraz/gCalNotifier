import json
import os

DB_FILE_NAME = "per_event_setting_db.json"

class Per_Event_Setting_DB():
    def load_db_file_into_memory(self):
        if not os.path.exists(DB_FILE_NAME):
            return {}  # Return empty dict if file does not exist

        with open(DB_FILE_NAME, 'r', encoding='utf-8') as infile:
            try:
                return json.load(infile)
            except json.JSONDecodeError:
                print(f"{DB_FILE_NAME} is empty or malformed")
                return {}  # Return empty dict if file is empty or malformed

    def update_db_file(self):
        with open(DB_FILE_NAME, 'w', encoding='utf-8') as outfile:
            json.dump(self.settings_db_in_memory, outfile, ensure_ascii=False, indent=4)  # Pretty print with indentation

    def __init__(self):
        self.settings_db_in_memory = self.load_db_file_into_memory()

    def get_event_setting(self, event_name, setting_name, default_value):
        # Let's first look if the event exists
        event_entry = self.settings_db_in_memory.get(event_name, None)
        if (event_entry):
            # The event exists - look for the setting
            setting_value = event_entry.get(setting_name, default_value)

            return setting_value
        
        else:
            # The event does not exist - return the default value
            return default_value
        
    def set_event_setting(self, event_name, setting_name, value_for_setting):
        # Let's first look if the event exists
        event_entry = self.settings_db_in_memory.get(event_name, None)
        if (not event_entry):
            # The event does not exist - let's create it
            self.settings_db_in_memory[event_name] = {}
            event_entry = self.settings_db_in_memory[event_name]

        event_entry[setting_name] = value_for_setting

        # Write the json from the memory to the file
        self.update_db_file()

# if __name__ == "__main__":
#     events_setting_db = per_event_setting_db()

#     print(events_setting_db.get_event_setting("test1", "os_notifications1", False))
#     events_setting_db.set_event_setting("test1", "os_notificatio4", False)
#     print(events_setting_db.get_event_setting("test1", "os_notifications1", False))
#     events_setting_db.set_event_setting("test2", "something else2", True)
#     print(events_setting_db.get_event_setting("test2", "something else2", False))
#     print(events_setting_db.get_event_setting("test2", "something else3", False))

