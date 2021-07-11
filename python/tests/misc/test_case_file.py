#import logging
#import logging as log
#from logging import info
#from logging import warning as w
#from logging import log as l


#name = input("Enter your name: ")

#aa = "Info"
#bb = "ff"

#def ff():
#    a = f"func infot {aa}"
#    return a
#def fff():
#    a = "aa"
#    return a

# Check if all calls are collected

#logging.warn("tt")
#log.warn("I warn you")
#w('test')
#info("test")
#log.exception("I warn you " + "asfasd" + "asd")
#log.warning("aa {}".format("asd"))
#log.warning("aa %s %s", "asd", "a")
#log.warning("I warn you %s", aa)
#log.info(fff())
#log.warning(aa)
#log.warning("%s %s %s", aa, "as", bb, exc_info="")

# Check log level inference

#level = log.DEBUG
#def get_level():
#    return log.DEBUG
#log.log(log.DEBUG, "test")
#log.log(level, "test")
#log.log(1, "test")

# Check things that need to be inferred
#aa = "aaa"
#def ll():
#    return aa
#log.warning("first part" + "second part" + "third part")

# Check string concat with +
#log.warning(ll())

# Check JoinedStr
#log.warning(f"asdasdf {aa} as as")
#log.warning(f"asdasdf {name} as as")

# Check .format()
#log.warning("{} test {}".format(aa, fff()))
#log.warning("{} test {}".format(name, ff()))

# Check old formatting
#log.warning('%as aa %s' % (aa, fff()))
#log.warning('%s aa %s' % (name, ff()))

#a2 = logging.getLogger('aa')
#a2.debug('A debug message')

#import logging

#i_w = input("Enter your name: ")
#def w_f():
#    return "W"
#w = "W"
#logging.warning("Warning " + "W" + " W")
#logging.warning("Warning " + w_f() + " " + w)
#logging.warning("Warning " + i_w)

#import logging

#i_w = input("Enter your name: ")

#logging.warning("Warning %s %d", "W", 5)
#logging.warning("Warning %s %s", "W", i_w)
#logging.warning("%s %s %s", "Warning", "W", "W", exc_info="")

#import logging

#level = logging.WARNING
#def get_level():
#    return logging.WARNING
#logging.log(logging.WARNING, "Warning")
#logging.log(level, "Warning")
#logging.log(get_level(), "Warning")
#logging.log(10, "Debug")

#import logging

#i_w = input("Enter your name: ")
#w = "W"

#logging.warning(f"{w}")
#logging.warning(f"Warning {w}")
#logging.warning(f"Warning {i_w}")

import logging

i_w = input("Enter your name: ")
w = "W"

logging.warning("%s" % ("Warning"))
logging.warning("Warning %s %d" % (w, 5))
logging.warning("Warning %s %%" % (w, i_w))

#from oslo_log import log as logging
#log = logging.getLogger(__name__)
#log.error('No APIs were started. '
#           'Check the enabled_apis config option.')


