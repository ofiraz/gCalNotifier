# https://stackoverflow.com/questions/2148888/python-trap-all-signals
import os
import signal

orig_handlers = {}

SIGNALS_TO_NAMES_DICT = dict((getattr(signal, n), n) \
    for n in dir(signal) if n.startswith('SIG') and '_' not in n )

def receive_signal(signum, stack):
    g_logger.info('Caught signal ' + SIGNALS_TO_NAMES_DICT[signum] + '(' + str(signum) + ')')

    if callable(orig_handlers[signum]):              # Call previous handler
        orig_handlers[signum](signum, stack)
    elif orig_handlers[signum] == signal.SIG_DFL:    # Default disposition
        signal.signal(signum, signal.SIG_DFL)
        os.kill(os.getpid(), signum)
                                          # else SIG_IGN - do nothing
def set_signal_handlers(logger):
    global g_logger

    g_logger = logger

    uncatchable = ['SIG_DFL','SIGSTOP','SIGKILL']
    for i in [x for x in dir(signal) if x.startswith("SIG")]:
        if not i in uncatchable:
            signum = getattr(signal,i)
            orig_handlers[signum] = signal.signal(signum,receive_signal)
