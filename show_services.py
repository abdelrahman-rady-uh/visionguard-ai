import json
with open('response_dump.json', 'r') as f:
    resp = json.load(f)
    
print('=== SERVICES STATUS ===\n')
analyses = resp.get('data', {}).get('analyses', {})

for service_name, service_data in analyses.items():
    status = service_data.get('status', 'unknown')
    print(f'{service_name}: {status}')
    if status == 'unavailable':
        summary = service_data.get('summary', 'No details')
        print(f'  Reason: {summary}')
    else:
        keys = list(service_data.keys())
        print(f'  Data keys: {keys}')
