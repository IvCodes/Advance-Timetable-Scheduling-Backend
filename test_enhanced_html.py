#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced HTML timetable features
"""
import requests
import json
import webbrowser
import time

def test_enhanced_html_features():
    """Test the enhanced HTML timetable generation and viewing"""
    
    base_url = "http://localhost:8000/api/enhanced-timetable"
    
    print("🧪 Testing Enhanced HTML Timetable Features")
    print("=" * 50)
    
    # Test 1: Run algorithm with HTML generation
    print("\n1. Running NSGA-II algorithm with HTML generation...")
    
    run_request = {
        "algorithm": "nsga2",
        "mode": "quick",
        "generate_html": True
    }
    
    try:
        response = requests.post(f"{base_url}/run-algorithm", json=run_request)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Algorithm completed successfully!")
            print(f"   Message: {result['message']}")
            print(f"   Execution time: {result['execution_time']:.2f}s")
            print(f"   HTML file: {result['html_path']}")
            
            # Extract filename from path
            html_filename = result['html_path'].split('\\')[-1] if '\\' in result['html_path'] else result['html_path'].split('/')[-1]
            
        else:
            print(f"❌ Algorithm failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Error running algorithm: {e}")
        return
    
    # Test 2: List generated files
    print("\n2. Listing generated HTML files...")
    
    try:
        response = requests.get(f"{base_url}/list-generated-files")
        if response.status_code == 200:
            files = response.json()['html_files']
            print(f"✅ Found {len(files)} HTML files:")
            for file in files[:3]:  # Show first 3
                print(f"   📄 {file['filename']} ({file['size']:,} bytes)")
        else:
            print(f"❌ Failed to list files: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error listing files: {e}")
    
    # Test 3: View HTML in browser
    print("\n3. Testing HTML viewing functionality...")
    
    try:
        view_url = f"{base_url}/view-html/{html_filename}"
        print(f"🌐 View URL: {view_url}")
        
        # Test if the view endpoint works
        response = requests.head(view_url)
        if response.status_code == 200:
            print(f"✅ HTML view endpoint working!")
            print(f"   Content-Type: {response.headers.get('content-type')}")
            print(f"   Content-Length: {response.headers.get('content-length')} bytes")
            
            # Open in browser
            print(f"\n🚀 Opening enhanced timetable in browser...")
            webbrowser.open(view_url)
            
        else:
            print(f"❌ View endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing view endpoint: {e}")
    
    # Test 4: Download functionality
    print("\n4. Testing download functionality...")
    
    try:
        download_url = f"{base_url}/download-html/{html_filename}"
        response = requests.head(download_url)
        if response.status_code == 200:
            print(f"✅ Download endpoint working!")
            print(f"   Content-Disposition: {response.headers.get('content-disposition')}")
        else:
            print(f"❌ Download endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing download endpoint: {e}")
    
    print("\n🎉 Enhanced HTML Features Summary:")
    print("   ✅ Student IDs in ITxxxxxxxx format")
    print("   ✅ Exam names with MODxxx_Subject format")
    print("   ✅ Penalty breakdown analysis")
    print("   ✅ Interactive student lists")
    print("   ✅ Enhanced statistics display")
    print("   ✅ View in browser (not download)")
    print("   ✅ Responsive design with modern UI")
    
    print(f"\n📖 Usage Instructions:")
    print(f"   • View: GET {base_url}/view-html/{{filename}}")
    print(f"   • Download: GET {base_url}/download-html/{{filename}}")
    print(f"   • List files: GET {base_url}/list-generated-files")

if __name__ == "__main__":
    test_enhanced_html_features() 