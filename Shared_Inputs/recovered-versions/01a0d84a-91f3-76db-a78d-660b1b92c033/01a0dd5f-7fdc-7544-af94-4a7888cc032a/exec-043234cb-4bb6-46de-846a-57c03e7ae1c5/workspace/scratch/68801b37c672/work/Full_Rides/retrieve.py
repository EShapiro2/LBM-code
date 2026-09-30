"""Retrieve all NYC yellow taxi rides picked up during the experiment's hour."""
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

BASE = 'https://data.cityofnewyork.us/resource/2yzn-sicd.json'
WHERE = "pickup_datetime >= '2015-01-15T08:00:00' AND pickup_datetime < '2015-01-15T09:00:00'"

def query(params):
    with urlopen(BASE + '?' + urlencode(params), timeout=180) as response:
        return json.load(response)

if __name__ == '__main__':
    count = int(query({'$select': 'count(*)', '$where': WHERE})[0]['count'])
    rows = query({'$where': WHERE, '$limit': max(count + 1, 50000),
                  '$order': 'pickup_datetime,pickup_longitude,pickup_latitude,dropoff_datetime'})
    assert len(rows) == count, (len(rows), count)
    destination = Path(__file__).parent / 'rides_2015-01-15_0800_0900.json'
    destination.write_text(json.dumps(rows))
    print(f'Saved {count} complete source records to {destination}')
