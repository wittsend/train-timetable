import time as t

VERB_NONE   = 0
VERB_ERR    = 1
VERB_WARN   = 2
VERB_INFO   = 3
VERB_DEBUG  = 4

verbosityDescTable = {
    0:  "No messages.",
    1:  "Error messages.",
    2:  "Warning messages.",
    3:  "Information messages.",
    4:  "Debug messages.",
}

class Post:
    def __init__(self, className:str, instanceName:str, verbosity:int) -> None:
        if(verbosity<VERB_NONE): verbosity=VERB_NONE
        if(verbosity>VERB_DEBUG): verbosity=VERB_DEBUG
        self.verbosity=verbosity
        self.className = className
        self.instanceName = instanceName
        self.info("Logging initialised. Verbosity Level: {0}, {1}"\
            .format(self.verbosity, verbosityDescTable[self.verbosity]))

    def _postMessage(self, className:str, instanceName:str, msg:str):
        tmNow = t.time()
        timeNow = t.localtime(tmNow)
        tm_msec = tmNow - int(tmNow)

        timeStr = "{0:2d}-{1:2d}-{2:2d} {3:2d}:{4:2d}:{5:2.3f}"\
            .format(timeNow.tm_mday, timeNow.tm_mon,timeNow.tm_year,\
                timeNow.tm_hour, timeNow.tm_min, timeNow.tm_sec + tm_msec)

        if(self.instanceName != ""):
            output = "{0} {1}[{2}]:\t{3}".format(timeStr, className, instanceName, msg)
        else:
            output = "{0} {1}:\t{2}".format(timeStr, className, msg)

        print(output)

        return

    def error(self, msg:str):
        if(self.verbosity>0):
            self._postMessage(self.className, self.instanceName, "[ERR] " + str(msg))
        return

    def warning(self, msg:str):
        if(self.verbosity>1):
            self._postMessage(self.className, self.instanceName, "[WRN] " + str(msg))
        return

    def info(self, msg:str):
        if(self.verbosity>2):
            self._postMessage(self.className, self.instanceName, "[INF] " + str(msg))
        return

    def debug(self, msg:str):
        if(self.verbosity>3):
            self._postMessage(self.className, self.instanceName, "[DBG] " + str(msg))
        return

    def setVerbosity(self, verb:int):
        if verb != self.verbosity:
            self._postMessage('POST', self.className, 'Verbosity level changing from {} to {}'\
                .format(self.verbosity, verb))
            self.verbosity = verb