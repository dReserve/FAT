import fatstack as fs

try:
    fs.start()
except SystemExit:
    # When command line parsing exits, like in the case of --help.
    import os
    os._exit(os.EX_OK)
