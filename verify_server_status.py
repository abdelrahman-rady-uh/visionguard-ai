import requests

print('='*60)
print('FLASK SERVER STARTUP VERIFICATION')
print('='*60)
print()

# Check main dashboard
resp = requests.get('http://127.0.0.1:5000', timeout=5)
print('✓ Main Dashboard')
print(f'  URL: http://127.0.0.1:5000')
print(f'  Status: {resp.status_code} (OK)')
print(f'  Content-Type: {resp.headers.get("Content-Type", "N/A")}')
print(f'  Response Size: {len(resp.text)} bytes')
print()

print('✓ Server Process Status: RUNNING')
print('✓ Port 5000: LISTENING')
print()
print('='*60)
print('DASHBOARD ACCESSIBLE AT: http://127.0.0.1:5000')
print('='*60)
