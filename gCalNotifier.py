from events_mdi_window import MDIWindow

from get_events_thread import Get_Events

from globals import app_globals

from system_tray import app_system_tray

from signal_hanlder import set_signal_handlers

# Main
if __name__ == "__main__":    
    g_globals = app_globals()

    set_signal_handlers(g_globals.logger)

    # Start a thread to look for events to display
    start_time = None
    end_time = None
    
    #start_time='2023-10-31T12:30:00-07:00' 
    #end_time='2023-10-31T13:00:00-07:00'

    get_events_object = Get_Events(g_globals, start_time, end_time)

    use_mdi = False

    if (use_mdi):
        g_mdi_window = MDIWindow(g_globals)
    else:
        g_mdi_window = None

    sys_tray = app_system_tray(g_globals, use_mdi, g_mdi_window, get_events_object)

    g_globals.app.exec_()