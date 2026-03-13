import urllib.request
import json
import urllib.parse

disease = urllib.parse.quote('Heart Attack')
url = f"http://127.0.0.1:5000/api/hospitals?lat=40.7128&lon=-74.0060&disease={disease}"
try:
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())
        print(json.dumps(data, indent=2))
except Exception as e:
    print(f"Error: {e}")
