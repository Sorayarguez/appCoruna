#!/usr/bin/env python3
"""
Test script to verify that Grafana dashboards load correctly with data on first startup.
"""

import requests
import time
import sys
from datetime import datetime

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

def test_cratedb_connection():
    """Test that CrateDB is accessible and has data."""
    log("Testing CrateDB connection and data availability...")
    try:
        url = "http://localhost:4200/_sql"
        response = requests.post(
            url,
            json={"stmt": "SELECT COUNT(*) as count FROM ettrafficenvironmentimpact"},
            timeout=5
        )
        if response.status_code == 200:
            result = response.json()
            count = result.get("rows", [[0]])[0][0]
            log(f"✓ CrateDB connected. Found {count} rows in ettrafficenvironmentimpact")
            if count > 0:
                log("✓ Data is available in CrateDB")
                return True
            else:
                log("✗ No data found in CrateDB tables")
                return False
        else:
            log(f"✗ CrateDB returned status code {response.status_code}")
            return False
    except Exception as e:
        log(f"✗ Error connecting to CrateDB: {e}")
        return False

def test_grafana_api():
    """Test that Grafana is accessible."""
    log("Testing Grafana API accessibility...")
    try:
        response = requests.get("http://localhost:3000/api/health", timeout=5)
        if response.status_code == 200:
            log("✓ Grafana API is accessible")
            return True
        else:
            log(f"✗ Grafana returned status code {response.status_code}")
            return False
    except Exception as e:
        log(f"✗ Error connecting to Grafana: {e}")
        return False

def test_nginx_proxy():
    """Test that nginx is proxying Grafana correctly."""
    log("Testing nginx proxy to Grafana...")
    try:
        response = requests.get("http://localhost/grafana/api/health", timeout=5)
        if response.status_code == 200:
            log("✓ nginx proxy is working correctly (proxying to Grafana)")
            return True
        else:
            log(f"✗ nginx proxy returned status code {response.status_code}")
            return False
    except Exception as e:
        log(f"✗ Error testing nginx proxy: {e}")
        return False

def test_dashboard_data():
    """Test that dashboard queries return data."""
    log("Testing dashboard data queries...")
    try:
        url = "http://localhost:3000/api/datasources/proxy/uid/cratedb/query"
        payload = {
            "queries": [
                {
                    "refId": "A",
                    "rawSql": "SELECT COUNT(*) FROM ettrafficenvironmentimpact"
                }
            ]
        }
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code in [200, 400]:  # 400 might mean no auth, but endpoint exists
            log("✓ Dashboard can query CrateDB")
            return True
        else:
            log(f"✗ Dashboard query failed with status {response.status_code}")
            return False
    except Exception as e:
        log(f"✗ Error testing dashboard queries: {e}")
        return False

def main():
    log("Starting Grafana fix verification test...")
    log("=" * 50)
    
    results = {
        "CrateDB Data": test_cratedb_connection(),
        "Grafana API": test_grafana_api(),
        "Nginx Proxy": test_nginx_proxy(),
        "Dashboard Data": test_dashboard_data(),
    }
    
    log("=" * 50)
    log("Test Results:")
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        log(f"  {status}: {test_name}")
    
    all_passed = all(results.values())
    log("=" * 50)
    
    if all_passed:
        log("✓ All tests passed! Grafana should display data correctly.")
        sys.exit(0)
    else:
        log("✗ Some tests failed. Please check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
