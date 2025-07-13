from datetime import datetime, timedelta

class TimeParser:
    @staticmethod
    def parse(ts: str) -> datetime:
        ts = ts.rstrip("Z")
        try:
            return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%f") + timedelta(hours=2)
        except ValueError:
            return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S") + timedelta(hours=2)
