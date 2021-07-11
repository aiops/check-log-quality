import logging as log

def f(arg):
    return "arg" + arg

# Function
a = "arg_var"
log.debug("debug function", "arg1", "arg2", f())

# Nested function
a = "arg_var"
log.debug("debug nested function", "arg1", "arg2", f(f(f())))

# Multi line
a = "arg_var"
log.debug("debug multi line",
    "arg1", "arg2",
    a)

# Multiline nested function
a = "arg_var"
log.debug("debug multi line nested function", 
    "arg1", "arg2", 
    f(f(f())))

# Comment at the end
a = "arg_var"
log.debug("debug comment at end", # comment
    "arg1", "arg2", #comment
    a)             # comment

# Comment in the middle
a = "arg_var"
log.debug("debug comment in between",
#    "arg1", "arg2",
    a)
