"""Download the historical trip window and official Manhattan boundary."""
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
ROOT=Path(__file__).parent
TRIPS='https://data.cityofnewyork.us/resource/2yzn-sicd.json'
BOUNDARY='https://data.cityofnewyork.us/resource/gthc-hcne.json?$limit=10'
params={'$where':"pickup_datetime >= '2015-01-15T12:00:00' AND pickup_datetime < '2015-01-15T14:00:00'",'$limit':100000,'$order':'pickup_datetime,pickup_longitude,pickup_latitude,dropoff_datetime'}
if __name__=='__main__':
    url=TRIPS+'?'+urlencode(params)
    with urlopen(url,timeout=180) as f:raw=f.read()
    assert len(json.loads(raw))<params['$limit'], 'Response could be truncated'
    (ROOT/'source_rides.json').write_bytes(raw)
    (ROOT/'source_url.txt').write_text(url)
    with urlopen(BOUNDARY,timeout=120) as f:(ROOT/'borough_boundaries.json').write_bytes(f.read())
    print('Retrieved',len(json.loads(raw)),'rides')
