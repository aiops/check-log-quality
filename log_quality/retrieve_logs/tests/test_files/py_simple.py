import logging as log

# Debug
log.debug("debug")

# Info log
log.info("info")

# Warning logs
log.warning("warning")
log.warn("warn")

# Error logs (includes exception)
log.error("error")
log.exception("exception")

# Critical
log.critical("critical")

# Other logging variant
log.log(log.DEBUG, "debug")
log.log(log.INFO, "info")
log.log(log.WARNING, "warning")
log.log(log.WARN, "warn")
log.log(log.ERROR, "error")
log.log(log.CRITICAL, "critical")
