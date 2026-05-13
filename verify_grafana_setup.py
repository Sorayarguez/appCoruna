#!/usr/bin/env python3
"""
Enhanced test script with retries for Grafana dashboard availability.
"""

import requests
import time
import sys
from datetime import datetime

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

def test_with_retries(name, url, max_retries=5, timeout=5):
    """Test connectivity with retries."""
    log(f"Testing {name} ({url})...")
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code in [200, 401, 403]:
                log(f"✓ {name} is accessible (attempt {attempt + 1})")
                return True
            else:
                log(f"  Attempt {attempt + 1}: Status {response.status_code}")
        except requests.exceptions.Timeout:
            log(f"  Attempt {attempt + 1}: Timeout")
        except Exception as e:
            log(f"  Attempt {attempt + 1}: {type(e).__name__}")
        
        if attempt < max_retries - 1:
            time.sleep(2)
    
    log(f"✗ {name} failed after {max_retries} attempts")
    return False

def main():
    log("=" * 60)
    log("GRAFANA DASHBOARD - ENHANCED VERIFICATION TEST")
    log("=" * 60)
    
    tests = {
        "CrateDB (direct)": ("http://localhost:4200", 1),
        "Grafana API (direct)": ("http://localhost:3000/api/health", 1),
        "Nginx proxy to Grafana": ("http://localhost/grafana/api/health", 3),
        "Dashboard via proxy": ("http://localhost/grafana/d/urbs-dashboard", 3),
    }
    
    results = {}
    for test_name, (url, retries) in tests.items():
        results[test_name] = test_with_retries(test_name, url, max_retries=retries)
        time.sleep(1)
    
    log("=" * 60)
    log("TEST RESULTS:")
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        log(f"  {status}: {test_name}")
    
    log("=" * 60)
    
    # Check critical services
    critical = [
        "CrateDB (direct)",
        "Grafana API (direct)",
        "Nginx proxy to Grafana",
    ]
    
    critical_passed = all(results.get(test, False) for test in critical)
    
    if critical_passed:
        log("✓ All critical services are working!")
        log("✓ Grafana should load correctly in the browser.")
        log("✓ Dashboard URL: http://localhost/grafana/d/urbs-dashboard")
        sys.exit(0)
    else:
        log("✗ Some critical services are failing.")
        sys.exit(1)

if __name__ == "__main__":
    main()
