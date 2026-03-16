import http.client
import json

def test(path):
    print(f"Testing {path}...")
    try:
        # Preflight
        conn = http.client.HTTPConnection("127.0.0.1", 8000, timeout=5)
        headers = {
            "Origin": "http://localhost:8080",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization"
        }
        conn.request("OPTIONS", path, headers=headers)
        res = conn.getresponse()
        print(f"Preflight Status: {res.status}")
        for k, v in res.getheaders():
            if "access-control" in k.lower():
                print(f"  {k}: {v}")
        conn.read() # consume body
        conn.close()
        
        # GET
        conn = http.client.HTTPConnection("127.0.0.1", 8000, timeout=5)
        conn.request("GET", path, headers={"Origin": "http://localhost:8080"})
        res = conn.getresponse()
        print(f"GET Status: {res.status}")
        for k, v in res.getheaders():
            if "access-control" in k.lower():
                print(f"  {k}: {v}")
        body = res.read().decode()
        print(f"Body: {body[:100]}...")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 20)

test("/")
test("/health")
test("/api/categories")
test("/api/users/profile")
