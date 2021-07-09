import logging as log

aa = "Info"
bb = "ff"

def ff():
    a = "aa"
    return "{} func infot".format(a)

log.warn("I warn you")
log.exception("I warn you " + "asfasd" + "asd")
log.warning("aa {}".format("asd"))
log.warning("aa", "asd", "a")
log.warning("I warn you", aa)
log.info(ff())

log.log(log.DEBUG, "test")

print("test")

# Does not work
log.warning(aa)
log.warning(aa, "as", bb)



