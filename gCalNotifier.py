from get_events_thread import Get_Events

from globals import app_globals

from system_tray import app_system_tray

from signal_hanlder import set_signal_handlers

# Main
if __name__ == "__main__":    
    g_globals = app_globals()

    set_signal_handlers(g_globals.logger)

    # Start a thread to look for events to display
    if (g_globals.config.do_debug):
        # Need to debug a specific event
        start_time = g_globals.config.debug_start_time
        end_time = g_globals.config.debug_end_time
    
    else:
        # Not a debug mode - monitor the coming events
        start_time = None
        end_time = None
    
    g_globals.get_events_object = Get_Events(g_globals, start_time, end_time)

    sys_tray = app_system_tray(g_globals)

    g_globals.app.exec_()