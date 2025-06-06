#!/usr/bin/env python3
"""
Ultra-Fast HTTP-based SRM Exam Seating Arrangement Scraper
Direct HTTP requests with session management - 10x faster than Playwright

Copyright 2025 Pragadees15
"""

import requests
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime
from typing import List, Dict, Optional
import concurrent.futures
import threading
import urllib.parse
import re

class SRMHTTPScraper:
    def __init__(self, venue: str = "main"):
        """Initialize the HTTP-based scraper."""
        # Define venue URLs
        self.venue_urls = {
            "main": "https://examcell.srmist.edu.in/main/seating/bench/get_datewise_report.php",
            "tp": "https://examcell.srmist.edu.in/tp/seating/bench/get_datewise_report.php",
            "bio": "https://examcell.srmist.edu.in/bio/seating/bench/get_datewise_report.php",
            "ub": "https://examcell.srmist.edu.in/ub/seating/bench/get_datewise_report.php",
            "tp2": "https://examcell.srmist.edu.in/tp2/bench/get_datewise_report.php"
        }
        
        # Venue display names
        self.venue_names = {
            "main": "Main Campus",
            "tp": "Tech Park",
            "bio": "Biotech and Architecture",
            "ub": "University Building",
            "tp2": "Tech Park 2"
        }
        
        self.venue = venue
        self.base_url = self.venue_urls.get(venue, self.venue_urls["main"])
        self.venue_name = self.venue_names.get(venue, "Main Campus")
        
        # Create session with connection pooling
        self.session = requests.Session()
        
        # Set headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        })
        
        # Configure session for speed
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=20,
            pool_maxsize=20,
            max_retries=2,
            pool_block=False
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # Set timeouts
        self.timeout = (10, 30)  # connection timeout, read timeout
    
    def scrape_seating_data_fast(self, date: str, session_type: str) -> List[Dict]:
        """Ultra-fast HTTP-based scraping using direct POST requests."""
        try:
            start_time = time.time()
            print(f"🚀 HTTP Scraping {self.venue_name} - {date} {session_type}")
            
            # First, get the initial page to establish session and get any CSRF tokens
            try:
                initial_response = self.session.get(self.base_url, timeout=self.timeout)
                initial_response.raise_for_status()
            except Exception as e:
                print(f"❌ Failed to load initial page for {self.venue_name}: {e}")
                return []
            
            # Parse initial page to extract form action and any hidden fields
            initial_soup = BeautifulSoup(initial_response.text, 'html.parser')
            
            # Find the form and its action URL
            form = initial_soup.find('form')
            form_action = 'fetch_data.php'  # Default action from the HTML
            if form and form.get('action'):
                form_action = form.get('action')
            
            # Construct the full URL for form submission
            if not form_action.startswith('http'):
                form_url = self.base_url.rsplit('/', 1)[0] + '/' + form_action.lstrip('/')
            else:
                form_url = form_action
            
            # Optional: Debug form action URL (comment out for production)
            # print(f"🔧 Form action URL: {form_url}")
            
            # Prepare form data (note: field name is 'dated' not 'datepicker')
            form_data = {
                'dated': date,
                'session': session_type,
                'submit': 'Submit'
            }
            
            # Look for any hidden fields in the form
            if form:
                hidden_inputs = form.find_all('input', type='hidden')
                for hidden_input in hidden_inputs:
                    name = hidden_input.get('name')
                    value = hidden_input.get('value', '')
                    if name:
                        form_data[name] = value
            
            # Add referer header
            self.session.headers.update({
                'Referer': self.base_url,
                'Origin': self.base_url.rsplit('/', 1)[0]
            })
            
            print(f"⚡ Initial page loaded in {time.time() - start_time:.2f}s")
            
            # Submit the form with POST request to the correct form action URL
            try:
                response = self.session.post(
                    form_url,
                    data=form_data,
                    timeout=self.timeout,
                    allow_redirects=True
                )
                response.raise_for_status()
                
                print(f"✅ Form submitted in {time.time() - start_time:.2f}s")
                
            except Exception as e:
                print(f"❌ Form submission failed for {self.venue_name}: {e}")
                return []
            
            # Parse the response
            if not response.text:
                print(f"⚠️ Empty response from {self.venue_name}")
                return []
            
            # Check for common "no data" indicators
            response_text_lower = response.text.lower()
            if any(indicator in response_text_lower for indicator in ['no records found', 'no data', 'no results']):
                print(f"📝 No records found for {self.venue_name}")
                return []
            
            # Optional: Debug response information (comment out for production)
            # print(f"🔧 Response length: {len(response.text)} chars")
            # if '.content-and-table' in response.text:
            #     print(f"🔧 Found .content-and-table in response")
            # if 'maintable' in response.text:
            #     print(f"🔧 Found maintable in response")
            # if 'datessesinfo' in response.text:
            #     print(f"🔧 Found datessesinfo in response")
            
            # Parse HTML and extract data
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Optional: Debug HTML saving (comment out for production)
            # debug_filename = f"debug_{self.venue}_{date.replace('/', '-')}_{session_type}.html"
            # try:
            #     with open(debug_filename, 'w', encoding='utf-8') as f:
            #         f.write(response.text)
            #     print(f"🔧 Debug HTML saved to {debug_filename}")
            # except:
            #     pass
            
            seating_data = self._extract_seating_data_http(soup, date, session_type)
            
            extraction_time = time.time() - start_time
            print(f"🎯 Extracted {len(seating_data)} records from {self.venue_name} in {extraction_time:.2f}s")
            
            return seating_data
            
        except Exception as e:
            print(f"❌ HTTP scraping failed for {self.venue_name}: {e}")
            return []
    
    def _extract_seating_data_http(self, soup: BeautifulSoup, date: str, session_type: str) -> List[Dict]:
        """Extract seating data from BeautifulSoup object - matches Playwright scraper logic."""
        seating_data = []
        
        try:
            # Strategy 1: Look for .content-and-table divs (exact match to Playwright scraper)
            content_divs = soup.find_all('div', class_='content-and-table')
            
            if content_divs:
                print(f"📊 Found {len(content_divs)} content-and-table divs")
                # Use the same extraction logic as Playwright scraper
                seating_data = self._extract_seating_data_ultra_fast_http(soup, date, session_type)
            else:
                # Fallback: try to find any tables (same as Playwright)
                print(f"🔄 No content-and-table divs found, trying fallback extraction...")
                seating_data = self._extract_seating_data_fallback_http(soup, date, session_type)
            
        except Exception as e:
            print(f"❌ Data extraction error: {e}")
        
        return seating_data
    
    def _extract_seating_data_ultra_fast_http(self, soup: BeautifulSoup, date: str, session_type: str) -> List[Dict]:
        """Ultra-fast data extraction matching Playwright scraper logic exactly."""
        seating_data = []
        
        # Fast content div finding
        content_divs = soup.find_all('div', class_='content-and-table')
        if not content_divs:
            return []
        
        # Pre-calculate common values for performance
        current_time = datetime.now().isoformat()
        venue_code = self.venue
        venue_name = self.venue_name
        
        for div in content_divs:
            # Ultra-fast room info extraction (same as Playwright)
            room_info = self._extract_room_info_ultra_fast_http(div)
            if not room_info:
                continue
                
            # Fast table finding (looking for table with id='maintable')
            table = div.find('table', id='maintable')
            if not table:
                # If no maintable, try any table in the div
                table = div.find('table')
                if not table:
                    continue
                
            # Ultra-fast table data extraction
            tbody = table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')[1:]  # Skip header, get all rows at once
            else:
                # If no tbody, get rows directly from table and skip header
                all_rows = table.find_all('tr')
                rows = all_rows[1:] if len(all_rows) > 1 else []
            
            # Pre-extract room details for batch processing
            room_number = room_info['room_number']
            exam_date = room_info['exam_date']
            exam_session = room_info['session']
            
            # Optional: Debug row processing (comment out for production)
            # print(f"🔧 Processing {len(rows)} rows for room {room_number}")
            
            # Batch process all rows for maximum speed
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 6:
                    # Ultra-fast text extraction using get_text with strip
                    cell_texts = [cell.get_text(strip=True) for cell in cells[:6]]
                    
                    # First student (left side)
                    if cell_texts[0] and cell_texts[1] and cell_texts[2]:
                        seating_data.append({
                            'date': date,
                            'session': session_type,
                            'room_number': room_number,
                            'exam_date': exam_date,
                            'exam_session': exam_session,
                            'department': cell_texts[0],
                            'seat_number': cell_texts[1],
                            'registration_number': cell_texts[2],
                            'venue_code': venue_code,
                            'venue_name': venue_name,
                            'extracted_at': current_time
                        })
                    
                    # Second student (right side)
                    if cell_texts[3] and cell_texts[4] and cell_texts[5]:
                        seating_data.append({
                            'date': date,
                            'session': session_type,
                            'room_number': room_number,
                            'exam_date': exam_date,
                            'exam_session': exam_session,
                            'department': cell_texts[3],
                            'seat_number': cell_texts[4],
                            'registration_number': cell_texts[5],
                            'venue_code': venue_code,
                            'venue_name': venue_name,
                            'extracted_at': current_time
                        })
        
        return seating_data
    
    def _extract_room_info_ultra_fast_http(self, div) -> Dict:
        """Ultra-fast room information extraction matching Playwright scraper exactly."""
        try:
            date_session_div = div.find('div', id='datessesinfo')
            if not date_session_div:
                return None
                
            h4 = date_session_div.find('h4')
            if not h4:
                return None
                
            h4_text = h4.get_text(strip=True)
            
            # Ultra-fast string parsing without regex for common patterns
            room_number = "Unknown"
            exam_date = "Unknown"
            session = "Unknown"
            
            # Fast room number extraction
            room_idx = h4_text.find('ROOM NO:')
            if room_idx != -1:
                room_part = h4_text[room_idx + 8:room_idx + 20].strip()
                space_idx = room_part.find(' ')
                room_number = room_part[:space_idx] if space_idx != -1 else room_part
            
            # Fast date extraction
            date_idx = h4_text.find('DATE : ')
            if date_idx != -1:
                date_part = h4_text[date_idx + 7:date_idx + 20].strip()
                space_idx = date_part.find(' ')
                exam_date = date_part[:space_idx] if space_idx != -1 else date_part
            
            # Fast session extraction
            session_idx = h4_text.find('SESSION : ')
            if session_idx != -1:
                session_part = h4_text[session_idx + 10:session_idx + 20].strip()
                space_idx = session_part.find(' ')
                session = session_part[:space_idx] if space_idx != -1 else session_part
            
            return {
                'room_number': room_number,
                'exam_date': exam_date,
                'session': session
            }
        except Exception:
            return None
    
    def _extract_seating_data_fallback_http(self, soup: BeautifulSoup, date: str, session_type: str) -> List[Dict]:
        """Fallback extraction method matching Playwright scraper logic."""
        seating_data = []
        
        # Pre-calculate common values
        current_time = datetime.now().isoformat()
        venue_code = self.venue
        venue_name = self.venue_name
        
        # Find any tables in the page
        tables = soup.find_all('table')
        print(f"🔍 Fallback: Found {len(tables)} tables")
        
        for table in tables:
            # Try to find data rows
            tbody = table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
            else:
                rows = table.find_all('tr')
            
            if len(rows) <= 1:  # Skip if no data rows
                continue
                
            print(f"🔍 Processing table with {len(rows)} rows")
            
            # Try to extract room info from nearby elements
            room_number = "Unknown"
            exam_date = date
            exam_session = session_type
            
            # Look for room info in surrounding text
            table_parent = table.parent
            if table_parent:
                parent_text = table_parent.get_text()
                if 'ROOM' in parent_text.upper():
                    room_match = parent_text.upper().find('ROOM')
                    if room_match != -1:
                        room_part = parent_text[room_match:room_match+20]
                        room_nums = re.findall(r'ROOM\s*(?:NO)?:?\s*([A-Z0-9]+)', room_part.upper())
                        if room_nums:
                            room_number = room_nums[0]
            
            # Process data rows (skip header)
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:
                    cell_texts = [cell.get_text(strip=True) for cell in cells]
                    
                    # Try different column arrangements
                    if len(cells) >= 6:
                        # Standard 6-column format
                        if cell_texts[0] and cell_texts[1] and cell_texts[2]:
                            seating_data.append({
                                'date': date,
                                'session': session_type,
                                'room_number': room_number,
                                'exam_date': exam_date,
                                'exam_session': exam_session,
                                'department': cell_texts[0],
                                'seat_number': cell_texts[1],
                                'registration_number': cell_texts[2],
                                'venue_code': venue_code,
                                'venue_name': venue_name,
                                'extracted_at': current_time
                            })
                        
                        if cell_texts[3] and cell_texts[4] and cell_texts[5]:
                            seating_data.append({
                                'date': date,
                                'session': session_type,
                                'room_number': room_number,
                                'exam_date': exam_date,
                                'exam_session': exam_session,
                                'department': cell_texts[3],
                                'seat_number': cell_texts[4],
                                'registration_number': cell_texts[5],
                                'venue_code': venue_code,
                                'venue_name': venue_name,
                                'extracted_at': current_time
                            })
                    elif len(cells) >= 3:
                        # Simple 3-column format
                        if cell_texts[0] and cell_texts[1] and cell_texts[2]:
                            seating_data.append({
                                'date': date,
                                'session': session_type,
                                'room_number': room_number,
                                'exam_date': exam_date,
                                'exam_session': exam_session,
                                'department': cell_texts[0],
                                'seat_number': cell_texts[1],
                                'registration_number': cell_texts[2],
                                'venue_code': venue_code,
                                'venue_name': venue_name,
                                'extracted_at': current_time
                            })
        
        print(f"🔍 Fallback extraction found {len(seating_data)} records")
        return seating_data
    
    def _extract_room_data_http(self, div, date: str, session_type: str) -> List[Dict]:
        """Extract data from a content-and-table div"""
        room_data = []
        
        try:
            # Extract room information
            room_info = {'room_number': 'Unknown', 'department': 'Unknown'}
            
            # Look for room number in h3, h4, or strong tags
            for tag in div.find_all(['h3', 'h4', 'strong', 'b']):
                text = tag.get_text(strip=True)
                if text and any(keyword in text.upper() for keyword in ['ROOM', 'HALL', 'LAB']):
                    # Extract room number using regex
                    room_match = re.search(r'([A-Z]+\d+|[A-Z]+-\d+|\d+[A-Z]*)', text)
                    if room_match:
                        room_info['room_number'] = room_match.group(1)
                    
                    # Extract department if present
                    if 'CSE' in text.upper():
                        room_info['department'] = 'Computer Science Engineering'
                    elif 'ECE' in text.upper():
                        room_info['department'] = 'Electronics and Communication Engineering'
                    elif 'MECH' in text.upper():
                        room_info['department'] = 'Mechanical Engineering'
                    elif 'CIVIL' in text.upper():
                        room_info['department'] = 'Civil Engineering'
                    elif 'EEE' in text.upper():
                        room_info['department'] = 'Electrical and Electronics Engineering'
                    break
            
            # Find the table within this div
            table = div.find('table')
            if table:
                room_data.extend(self._extract_table_data_http(table, date, session_type, room_info))
        
        except Exception as e:
            print(f"❌ Room data extraction error: {e}")
        
        return room_data
    
    def _extract_table_data_http(self, table, date: str, session_type: str, room_info: Dict = None) -> List[Dict]:
        """Extract data from a table element"""
        table_data = []
        
        if not room_info:
            room_info = {'room_number': 'Unknown', 'department': 'Unknown'}
        
        try:
            rows = table.find_all('tr')
            headers = []
            
            # Find header row
            for row in rows:
                cells = row.find_all(['th', 'td'])
                if cells and any(cell.get_text(strip=True).upper() in ['SEAT', 'REGISTRATION', 'ROLL', 'REG'] 
                               for cell in cells):
                    headers = [cell.get_text(strip=True).upper() for cell in cells]
                    break
            
            # If no clear headers, assume standard format
            if not headers:
                headers = ['SEAT_NO', 'REGISTRATION_NUMBER', 'NAME']
            
            # Extract data rows
            for row in rows[1:] if headers else rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    row_data = {
                        'seat_number': 'Unknown',
                        'registration_number': '',
                        'student_name': '',
                        'room_number': room_info['room_number'],
                        'department': room_info['department'],
                        'date': date,
                        'session': session_type
                    }
                    
                    for i, cell in enumerate(cells):
                        cell_text = cell.get_text(strip=True)
                        
                        if i < len(headers):
                            header = headers[i]
                            
                            if 'SEAT' in header:
                                row_data['seat_number'] = cell_text
                            elif any(keyword in header for keyword in ['REGISTRATION', 'REG', 'ROLL']):
                                row_data['registration_number'] = cell_text
                            elif 'NAME' in header:
                                row_data['student_name'] = cell_text
                        else:
                            # Fallback: try to identify by content pattern
                            if re.match(r'^[A-Z]{2}\d{13}$', cell_text):  # Registration number pattern
                                row_data['registration_number'] = cell_text
                            elif cell_text.isdigit() or re.match(r'^\d+[A-Z]*$', cell_text):  # Seat number pattern
                                row_data['seat_number'] = cell_text
                            elif len(cell_text) > 10 and cell_text.replace(' ', '').isalpha():  # Name pattern
                                row_data['student_name'] = cell_text
                    
                    # Only add if we have essential data
                    if row_data['registration_number'] and row_data['seat_number'] != 'Unknown':
                        table_data.append(row_data)
        
        except Exception as e:
            print(f"❌ Table extraction error: {e}")
        
        return table_data
    
    def _extract_fallback_data_http(self, soup: BeautifulSoup, date: str, session_type: str) -> List[Dict]:
        """Fallback extraction method for non-standard formats"""
        fallback_data = []
        
        try:
            # Look for any text patterns that might contain seating data
            text_content = soup.get_text()
            lines = text_content.split('\n')
            
            current_room = 'Unknown'
            current_dept = 'Unknown'
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check for room information
                if any(keyword in line.upper() for keyword in ['ROOM', 'HALL', 'LAB']):
                    room_match = re.search(r'([A-Z]+\d+|[A-Z]+-\d+|\d+[A-Z]*)', line)
                    if room_match:
                        current_room = room_match.group(1)
                
                # Look for registration number patterns
                reg_matches = re.findall(r'[A-Z]{2}\d{13}', line)
                for reg_number in reg_matches:
                    # Try to find associated seat number
                    seat_match = re.search(r'\b(\d+[A-Z]*|\d+)\b', line)
                    seat_number = seat_match.group(1) if seat_match else 'Unknown'
                    
                    fallback_data.append({
                        'seat_number': seat_number,
                        'registration_number': reg_number,
                        'student_name': '',
                        'room_number': current_room,
                        'department': current_dept,
                        'date': date,
                        'session': session_type
                    })
        
        except Exception as e:
            print(f"❌ Fallback extraction error: {e}")
        
        return fallback_data
    
    def close_session(self):
        """Close the HTTP session"""
        if self.session:
            self.session.close()

# Backward compatibility wrapper to replace Playwright scraper
class SRMPlaywrightScraper:
    """Backward compatibility wrapper that uses HTTP scraper instead of Playwright"""
    
    def __init__(self, headless: bool = True, venue: str = "main"):
        """Initialize with HTTP scraper backend"""
        self.http_scraper = SRMHTTPScraper(venue=venue)
        self.venue = venue
    
    def scrape_seating_data_fast(self, date: str, session_type: str) -> List[Dict]:
        """Scrape using HTTP backend"""
        return self.http_scraper.scrape_seating_data_fast(date, session_type)
    
    def scrape_seating_data(self, date: str, session_type: str) -> List[Dict]:
        """Scrape using HTTP backend (alias for compatibility)"""
        return self.http_scraper.scrape_seating_data_fast(date, session_type)
    
    def close_browser(self):
        """Close HTTP session (alias for close_session for backward compatibility)"""
        self.http_scraper.close_session()
    
    def close_session(self):
        """Close HTTP session"""
        self.http_scraper.close_session()

class MultiVenueScraper:
    """HTTP-based multi-venue scraper with parallel processing"""
    
    def __init__(self, headless: bool = True):
        """Initialize the multi-venue HTTP scraper"""
        self.venues = ["main", "tp", "tp2", "bio", "ub"]
        self.venue_names = {
            "main": "Main Campus",
            "tp": "Tech Park", 
            "bio": "Biotech and Architecture",
            "ub": "University Building",
            "tp2": "Tech Park 2"
        }
    
    def search_all_venues_parallel(self, date: str, session_type: str, roll_number: str = None) -> Dict:
        """Search all venues in parallel using HTTP requests."""
        start_time = time.time()
        results = {}
        
        # Use ThreadPoolExecutor for parallel HTTP requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Submit tasks for all venues
            future_to_venue = {
                executor.submit(self._scrape_venue_http, venue, date, session_type): venue
                for venue in self.venues
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_venue, timeout=60):
                venue = future_to_venue[future]
                try:
                    venue_data = future.result()
                    results[venue] = venue_data
                    
                    if venue_data:
                        print(f"✅ {self.venue_names[venue]}: {len(venue_data)} records")
                    else:
                        print(f"📝 {self.venue_names[venue]}: No data")
                        
                except Exception as e:
                    print(f"❌ {self.venue_names[venue]} failed: {e}")
                    results[venue] = []
        
        total_time = time.time() - start_time
        total_records = sum(len(data) for data in results.values())
        
        print(f"🎯 Total: {total_records} records from {len(self.venues)} venues in {total_time:.2f}s")
        
        # Filter by roll number if specified
        if roll_number:
            filtered_results = {}
            for venue, data in results.items():
                filtered_data = [
                    record for record in data
                    if roll_number.lower() in record.get('registration_number', '').lower()
                ]
                filtered_results[venue] = filtered_data
            return filtered_results
        
        return results
    
    def _scrape_venue_http(self, venue: str, date: str, session_type: str) -> List[Dict]:
        """Scrape a single venue using HTTP requests"""
        try:
            scraper = SRMHTTPScraper(venue=venue)
            data = scraper.scrape_seating_data_fast(date, session_type)
            scraper.close_session()
            return data
        except Exception as e:
            print(f"❌ HTTP scraping failed for {venue}: {e}")
            return []

def main():
    """Test the HTTP scraper"""
    print("🚀 Testing SRM HTTP Scraper")
    
    # Test single venue
    scraper = SRMHTTPScraper(venue="main")
    test_date = "28/05/2025"
    test_session = "FN"
    
    print(f"\n📊 Testing single venue: Main Campus")
    results = scraper.scrape_seating_data_fast(test_date, test_session)
    print(f"Results: {len(results)} records found")
    
    scraper.close_session()

if __name__ == "__main__":
    main() 
 