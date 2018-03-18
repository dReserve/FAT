import time

class Time:
    "Object representing a moment in time. It's always UTC."
    def __init__(self, seconds=0):
        self.seconds = seconds

    @staticmethod
    def now():
        return Time(time.time())

    def __str__(self):
        return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(self.seconds))

    def __repr__(self):
        return "<Time seconds: {}>".format(self.seconds)
