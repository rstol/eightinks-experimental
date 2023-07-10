import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler, LoggingEventHandler


class NdaxFileEventHandler(PatternMatchingEventHandler):
    def __init__(self, patterns=None):
        super(NdaxFileEventHandler, self).__init__(patterns=patterns)
        self.logger = logging.root

    def on_created(self, event):
        self.logger.info("Created %s: %s", "file", event.src_path)

    def on_modified(self, event):
        self.logger.info("Modified %s: %s", "file", event.src_path)

    def on_closed(self, event):
        self.logger.info("Closed %s: %s", "file", event.src_path)

    def on_deleted(self, event):
        print("deleted", event.src_path)


def monitor_test_data(cycler):
    '''
    Uses the Watchdog package to monitor the data directory of a cycler for updates to raw data files.
    See the NdaxFileEventHandler and (TODO:add Biologic) classes for actual monitoring code. Monitors each cycler.
    '''
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    path = sys.argv[1] if len(sys.argv) > 1 else cycler["file_path"]
    patterns = cycler["file_patterns"]
    name = cycler["name"]
    if name == "Neware":
        event_handler = NdaxFileEventHandler(patterns=patterns)
    elif name == "Biologic":
        event_handler = LoggingEventHandler()
    else:
        raise ValueError(
            f"Event handler for cycler type {name} does not exist.")

    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    print('Observer started')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.unschedule_all()
        observer.stop()
    observer.join()


cycler_types = [
    {
        "name": "Neware",
        "file_patterns": ["*.nda", "*.ndax"],
        "file_path": "."
    },
    {
        "name": "Biologic",
        "file_patterns": ["*.mpr", "*.mpl"],
        "file_path": "."
    }
]

if __name__ == "__main__":
    for c in cycler_types:
        monitor_test_data(c)
