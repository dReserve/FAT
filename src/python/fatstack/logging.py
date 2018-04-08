import logging, logging.handlers, os
import fatstack as fs

log = logging.getLogger(__name__)
stderr_handler = logging.StreamHandler()
mem_handler = logging.handlers.MemoryHandler(100)
final_format = '%(asctime)s %(levelname).1s %(name)s: %(message)s'


def init_bootstrap():
    stderr_formatter = logging.Formatter('%(message)s')
    stderr_handler.setFormatter(stderr_formatter)

    logging.root.addHandler(stderr_handler)
    logging.root.addHandler(mem_handler)
    logging.root.setLevel(logging.INFO)


def init_final():
    # Logs are hard wired to var/log/
    log_dir_path = os.path.join(fs.ROOT.Config.var_path, "log")
    if not os.path.isdir(log_dir_path):
        log.info("Log dir %s doesn't exists, creating it.", log_dir_path)
        os.mkdir(log_dir_path)

    log_file = os.path.join(log_dir_path, fs.ROOT.Config.log_file)
    log.info("Logging into: %s", log_file)

    file_handler = logging.FileHandler(log_file)
    final_formatter = logging.Formatter(final_format)
    file_handler.setFormatter(final_formatter)
    logging.root.addHandler(file_handler)
    mem_handler.setTarget(file_handler)
    mem_handler.flush()
    logging.root.removeHandler(logging.root.handlers[1])

    if fs.ROOT.Config.no_shell:
        stderr_handler.setFormatter(final_formatter)
    else:
        logging.root.removeHandler(stderr_handler)
