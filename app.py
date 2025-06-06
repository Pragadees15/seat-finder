#!/usr/bin/env python3
"""
SRM Exam Seat Finder Web Application
Modern Flask backend with beautiful frontend - ULTRA SPEED Optimized
Deployment Ready Version

Copyright 2025 Pragadees15

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import json
import os
from datetime import datetime
import hashlib
import io
import base64
from http_scraper import SRMPlaywrightScraper, MultiVenueScraper
import time
import uuid
import concurrent.futures
from functools import partial
from export_utils import ExamExportUtils
from concurrent.futures import ThreadPoolExecutor, as_completed
import gc
import urllib.parse
import logging
import sys
from serverless_session import session_manager

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Serverless Configuration
class ServerlessConfig:
    """Optimized configuration for serverless deployment"""
    
    def __init__(self):
        # Detect if running in serverless environment
        self.is_serverless = os.environ.get('SERVERLESS', '0') == '1' or \
                           os.environ.get('VERCEL', '0') == '1' or \
                           os.environ.get('AWS_LAMBDA_FUNCTION_NAME') is not None
        
        self.config = self._generate_serverless_config()
        
        # Log the detected configuration
        print(f"🚀 Serverless Configuration:")
        print(f"   Environment: {'Serverless' if self.is_serverless else 'Traditional'}")
        print(f"   Max Workers: {self.config['max_workers']}")
        print(f"   Parallel Search: {self.config['enable_parallel_search']}")
        print(f"   Session Timeout: {self.config['session_timeout']}s")
    
    def _generate_serverless_config(self):
        """Generate optimized configuration for serverless deployment"""
        if self.is_serverless:
            return {
                "max_workers": 8,  # Aggressive parallel processing for Vercel
                "max_concurrent_searches": 5,
                "enable_parallel_search": True,
                "venue_batch_size": 2,
                "session_timeout": 300,  # 5 minutes
                "description": "Vercel Parallel Optimized"
            }
        else:
            # Development/local configuration
            return {
                "max_workers": 6,
                "max_concurrent_searches": 3,
                "enable_parallel_search": True,
                "venue_batch_size": 1,
                "session_timeout": 300,
                "description": "Development Parallel Mode"
            }

# Initialize serverless config
scaling_config = ServerlessConfig()

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

# Production configuration with dynamic scaling
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', '0') == '1'
app.config['TESTING'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Dynamic timeout based on scaling tier
app.config['PERMANENT_SESSION_LIFETIME'] = scaling_config.config['session_timeout']

# Configure logging for production
if not app.debug:
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    app.logger.setLevel(logging.INFO)
    app.logger.info('SRM Exam Finder startup')

# Cache busting for static files
# Generate a unique version when the server starts
CACHE_BUST_VERSION = str(int(datetime.now().timestamp()))

@app.context_processor
def inject_cache_bust():
    """Inject cache busting version for static files"""
    def versioned_url_for(endpoint, **values):
        if endpoint == 'static':
            filename = values.get('filename', '')
            if filename:
                # Add cache busting parameter - changes every server restart
                values['v'] = CACHE_BUST_VERSION
        return app.url_for(endpoint, **values)
    
    return dict(versioned_url_for=versioned_url_for)

# Initialize export utilities
export_utils = ExamExportUtils()

class UltraFastSeatFinderAPI:
    """Serverless-optimized API class for Vercel deployment"""
    
    def __init__(self):
        # Get serverless configuration
        self.scaling_config = scaling_config.config
        
        # Core search configuration
        self.search_timeout = False
        
        # Multi-venue configuration
        self.venues = ["main", "tp", "tp2", "bio", "ub"]
        self.venue_names = {
            "main": "Main Campus",
            "tp": "Tech Park", 
            "bio": "Biotech and Architecture",
            "ub": "University Building",
            "tp2": "Tech Park 2"
        }
        
        # Parallel processing configuration
        self.enable_parallel_search = self.scaling_config['enable_parallel_search']
        self.max_workers = self.scaling_config['max_workers']
        
        print(f"⚡ Serverless API initialized: {self.scaling_config['description']}")
    
    def _format_results(self, matches):
        """Format raw matches to standardized result format"""
        formatted_results = []
        for match in matches:
            formatted_results.append({
                'room_number': match['room_number'],
                'seat_number': match['seat_number'],
                'session': match['session'],
                'session_name': 'Forenoon' if match['session'] == 'FN' else 'Afternoon',
                'date': match['date'],
                'department': match['department'],
                'registration_number': match['registration_number'],
                'venue_code': match.get('venue_code', 'main'),
                'venue_name': match.get('venue_name', 'Main Campus')
            })
        return formatted_results
    
# Old search methods removed for serverless compatibility

    def update_realistic_progress(self, session_id, message, progress):
        """Update progress with realistic increments using serverless session manager"""
        session_data = session_manager.get_session(session_id)
        if not session_data:
            return
            
        current_status = session_data.get('status', 'starting')
        current_progress = session_data.get('progress', 0)
        
        if current_status in ['completed', 'error']:
            return
        
        if progress > current_progress:
            session_manager.update_session(session_id, {
                'status': 'searching' if progress < 100 else 'completed',
                'message': message,
                'progress': min(100, progress)
            })

    def _search_venue_session_parallel(self, venue, session, roll_number, date, session_id):
        """Search a single venue-session combination (for parallel processing)"""
        venue_name = self.venue_names.get(venue, venue)
        session_name = "Forenoon" if session == "FN" else "Afternoon"
        
        try:
            # Create scraper instance for this venue-session combination
            from http_scraper import SRMPlaywrightScraper
            scraper = SRMPlaywrightScraper(headless=True, venue=venue)
            venue_session_data = scraper.scrape_seating_data_fast(date, session)
            
            # Search for student in this venue-session data
            venue_session_matches = []
            for entry in venue_session_data:
                if roll_number.lower() in entry.get('registration_number', '').lower():
                    entry['venue_code'] = venue
                    entry['venue_name'] = venue_name
                    venue_session_matches.append(entry)
            
            # Clean up scraper immediately to free memory
            scraper.close_browser()
            scraper = None
            gc.collect()  # Force garbage collection
            
            return {
                'venue': venue,
                'session': session,
                'venue_name': venue_name,
                'session_name': session_name,
                'matches': venue_session_matches,
                'success': True
            }
            
        except Exception as venue_error:
            print(f"⚠️ Error searching {venue_name} - {session_name}: {venue_error}")
            return {
                'venue': venue,
                'session': session,
                'venue_name': venue_name,
                'session_name': session_name,
                'matches': [],
                'success': False,
                'error': str(venue_error)
            }

    def find_student_seat_serverless(self, roll_number, date, session_id):
        """ULTRA-FAST parallel search method optimized for Vercel serverless"""
        start_time = time.time()
        
        try:
            self.update_realistic_progress(session_id, "🚀 Initializing parallel search...", 5)
            
            all_matches = []
            all_venues = ["main", "tp", "tp2", "bio", "ub"]
            all_sessions = ["FN", "AN"]
            
            # Create all venue-session combinations for parallel processing
            search_tasks = []
            for venue in all_venues:
                for session in all_sessions:
                    search_tasks.append((venue, session))
            
            total_tasks = len(search_tasks)
            self.update_realistic_progress(session_id, f"⚡ Starting {total_tasks} parallel searches...", 10)
            
            # Use ThreadPoolExecutor for parallel processing
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks for parallel execution
                future_to_task = {}
                for venue, session in search_tasks:
                    future = executor.submit(
                        self._search_venue_session_parallel,
                        venue, session, roll_number, date, session_id
                    )
                    future_to_task[future] = (venue, session)
                
                # Process completed tasks as they finish
                completed_tasks = 0
                for future in as_completed(future_to_task):
                    completed_tasks += 1
                    venue, session = future_to_task[future]
                    
                    try:
                        result = future.result()
                        
                        # Calculate progress (10% start + 80% for searches + 10% for completion)
                        search_progress = 10 + int((completed_tasks / total_tasks) * 80)
                        
                        if result['success'] and result['matches']:
                            all_matches.extend(result['matches'])
                            self.update_realistic_progress(
                                session_id,
                                f"✅ Found {len(result['matches'])} result(s) in {result['venue_name']} - {result['session_name']}!",
                                search_progress
                            )
                        else:
                            self.update_realistic_progress(
                                session_id,
                                f"⚡ Searched {result['venue_name']} - {result['session_name']} ({completed_tasks}/{total_tasks})",
                                search_progress
                            )
                            
                    except Exception as e:
                        print(f"⚠️ Task failed for {venue}-{session}: {e}")
                        continue
            
            search_time = time.time() - start_time
            formatted_results = self._format_results(all_matches)
            
            final_message = f'⚡ Found {len(formatted_results)} exam(s) in {search_time:.1f}s using parallel search!'
            
            # Update session with final results
            session_manager.update_session(session_id, {
                'status': 'completed',
                'message': final_message,
                'progress': 100,
                'results': formatted_results,
                'search_time': search_time
            })
            
            print(f"🚀 Parallel search completed: {len(formatted_results)} results in {search_time:.1f}s")
            return formatted_results
                
        except Exception as e:
            print(f"❌ Parallel search failed: {e}")
            session_manager.update_session(session_id, {
                'status': 'error',
                'message': 'Search failed. Please try again.',
                'progress': 0,
                'results': []
            })
            return []

    def set_timeout(self):
        """Set timeout flag to stop search"""
        self.search_timeout = True

# Initialize optimized API
ultra_fast_seat_finder = UltraFastSeatFinderAPI()

# No background monitoring needed in serverless

@app.route('/')
def index():
    """Main page"""
    response = app.make_response(render_template('index.html'))
    # Add cache control headers to ensure fresh content
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files (fallback for Vercel)"""
    from flask import send_from_directory
    return send_from_directory('static', filename)

@app.route('/api/clear-sessions', methods=['POST'])
def clear_sessions():
    """Clear all sessions when user clicks Search Again button"""
    try:
        session_manager.clear_all_sessions()
        return jsonify({
            'success': True,
            'message': 'All sessions cleared successfully'
        })
    except Exception as e:
        app.logger.error(f"Session clear error: {e}")
        return jsonify({
            'success': False,
            'message': 'Error clearing sessions'
        }), 500

@app.route('/api/search', methods=['POST'])
def search_seat():
    """API endpoint for serverless student seat search"""
    try:
        data = request.get_json()
        roll_number = data.get('rollNumber', '').strip()
        date = data.get('date', '').strip()
        
        if not roll_number or not date:
            return jsonify({
                'success': False,
                'message': 'Roll number and date are required'
            }), 400
        
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d/%m/%Y")
        except ValueError:
            try:
                datetime.strptime(date, "%d/%m/%Y")
                formatted_date = date
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid date format'
                }), 400
        
        if not roll_number or len(roll_number) < 10:
            return jsonify({
                'success': False,
                'message': 'Invalid roll number format'
            }), 400
        
        date_safe = formatted_date.replace('/', '-')
        session_id = f"{roll_number}_{date_safe}_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        
        # Create session with initial data
        created_session_id = session_manager.create_session({
            'status': 'searching',
            'message': 'Search started - finding your exam details...',
            'progress': 0,
            'results': [],
            'roll_number': roll_number,
            'date': formatted_date
        })
        
        # Use the created session ID
        session_id = created_session_id
        
        app.logger.info(f"New serverless search session: {session_id}")
        
        # Perform synchronous search (no threading in serverless)
        try:
            # Use sequential search optimized for serverless
            result = ultra_fast_seat_finder.find_student_seat_serverless(roll_number, formatted_date, session_id)
            
            return jsonify({
                'success': True,
                'sessionId': session_id,
                'message': 'Search completed',
                'results': result
            })
            
        except Exception as search_error:
            app.logger.error(f"Search failed for {session_id}: {search_error}")
            session_manager.update_session(session_id, {
                'status': 'error',
                'message': 'Search failed. Please try again.',
                'progress': 0,
                'results': []
            })
            
            return jsonify({
                'success': False,
                'sessionId': session_id,
                'message': 'Search failed. Please try again.'
            }), 500
        
    except Exception as e:
        app.logger.error(f"Search endpoint error: {e}")
        return jsonify({
            'success': False,
            'message': 'Search failed. Please try again.'
        }), 500

@app.route('/api/progress/<session_id>')
def get_progress(session_id):
    """Get scraping progress using serverless session manager"""
    session_data = session_manager.get_session(session_id)
    
    if not session_data:
        return jsonify({
            'status': 'not_found',
            'message': 'Session not found. Please start a new search.',
            'progress': 0
        }), 404
    
    return jsonify(session_data)

# Memory management not needed in serverless

@app.route('/api/export/<session_id>/options')
def get_export_options(session_id):
    """Get all available export options for a session"""
    session_data = session_manager.get_session(session_id)
    
    if not session_data:
        app.logger.warning(f"Export options requested for missing session: {session_id}")
        return jsonify({'error': 'Session not found. Please search again to generate fresh results.'}), 404
    
    app.logger.info(f"Export options loaded for session: {session_id}")
    
    if session_data.get('status') != 'completed' or 'results' not in session_data:
        return jsonify({'error': 'No results available'}), 400
    
    results = session_data['results']
    if not results:
        return jsonify({'error': 'No exam seats found'}), 400
    
    try:
        first_result = results[0]
        
        # Create WhatsApp message - handle single vs multiple exams
        if len(results) == 1:
            # Single exam - include venue information
            whatsapp_message = f"🎓 SRM Exam Details\n\n📝 Registration: {first_result['registration_number']}\n🏢 Room: {first_result['room_number']}\n💺 Seat: {first_result['seat_number']}\n📅 Date: {first_result['date']}\n⏰ Session: {first_result['session_name']}\n🏫 Venue: {first_result['venue_name']}\n🎯 Department: {first_result['department']}\n\n✨ Generated by SRM Seat Finder"
        else:
            # Multiple exams - include all rooms and sessions
            whatsapp_message = f"🎓 SRM Exam Schedule\n\n📝 Registration: {first_result['registration_number']}\n🎯 Department: {first_result['department']}\n\n"
            
            for i, result in enumerate(results, 1):
                whatsapp_message += f"📋 Exam {i}:\n"
                whatsapp_message += f"📅 Date: {result['date']}\n"
                whatsapp_message += f"⏰ Session: {result['session_name']} ({result['session']})\n"
                whatsapp_message += f"🏢 Room: {result['room_number']}\n"
                whatsapp_message += f"💺 Seat: {result['seat_number']}\n"
                whatsapp_message += f"🏫 Venue: {result['venue_name']}\n\n"
            
            whatsapp_message += "✨ Generated by SRM Seat Finder"
        
        whatsapp_url = f"https://wa.me/?text={urllib.parse.quote(whatsapp_message)}"
        
        # Simplified export options
        export_options = {
            'available_formats': [
                {
                    'type': 'whatsapp',
                    'name': '💬 WhatsApp Message',
                    'description': 'Share exam details via WhatsApp',
                    'url': whatsapp_url,
                    'icon': '📱',
                    'external': True
                },
                {
                    'type': 'pdf',
                    'name': '📄 PDF Document',
                    'description': 'Download as PDF file',
                    'url': f'/api/export/{session_id}/pdf',
                    'icon': '📋'
                }
            ]
        }
        
        return jsonify(export_options)
        
    except Exception as e:
        app.logger.error(f"Export options error for session {session_id}: {e}")
        return jsonify({'error': f'Error generating export options: {str(e)}'}), 500

@app.route('/api/sessions/extend/<session_id>', methods=['POST'])
def extend_session(session_id):
    """Extend session timeout in serverless environment"""
    session_data = session_manager.get_session(session_id)
    
    if not session_data:
        app.logger.warning(f"Session extension failed - session not found: {session_id}")
        return jsonify({'error': 'Session not found. Please search again.'}), 404
    
    # Extend session timeout
    session_manager.extend_session(session_id)
    app.logger.info(f"Session extended: {session_id}")
    
    return jsonify({
        'success': True,
        'message': 'Session extended successfully',
        'session_id': session_id
    })

@app.route('/api/export/<session_id>/pdf')
def export_pdf(session_id):
    """Export exam details as a PDF report"""
    session_data = session_manager.get_session(session_id)
    
    if not session_data:
        app.logger.warning(f"PDF export requested for missing session: {session_id}")
        return jsonify({'error': 'Session not found. Please search again to generate fresh results.'}), 404
    
    app.logger.info(f"PDF export started for session: {session_id}")
    
    if session_data.get('status') != 'completed' or 'results' not in session_data:
        return jsonify({'error': 'No results available'}), 400
    
    results = session_data['results']
    if not results:
        return jsonify({'error': 'No exam seats found'}), 400
    
    try:
        # Try to generate PDF using export utils
        try:
            if len(results) == 1:
                # Single exam - use exam card PDF generation
                pdf_data = export_utils.generate_exam_card_pdf(results[0])
                
                if pdf_data:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"exam_document_{timestamp}.pdf"
                    
                    pdf_buffer = io.BytesIO(pdf_data)
                    pdf_buffer.seek(0)
                    
                    return send_file(
                        pdf_buffer,
                        mimetype='application/pdf',
                        as_attachment=True,
                        download_name=filename
                    )
            else:
                # Multiple exams - generate PDF directly
                pdf_data = export_utils.generate_comprehensive_exam_document_pdf(results)
                
                if pdf_data:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"exam_schedule_{timestamp}.pdf"
                    
                    pdf_buffer = io.BytesIO(pdf_data)
                    pdf_buffer.seek(0)
                    
                    return send_file(
                        pdf_buffer,
                        mimetype='application/pdf',
                        as_attachment=True,
                        download_name=filename
                    )
                    
        except Exception as e:
            print(f"⚠️ Export utils PDF generation failed: {e}")
            pass
        
        # Fallback: Generate text-based PDF - handle single vs multiple exams
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)
        width, height = letter
        
        first_result = results[0]
        
        if len(results) == 1:
            # Single exam - keep existing format unchanged
            c.setFont("Helvetica-Bold", 20)
            c.drawString(50, height - 50, "SRM EXAM SEAT ALLOCATION")
            
            c.setFont("Helvetica", 12)
            y_position = height - 100
            line_height = 20
            
            exam_details = [
                f"Registration Number: {first_result['registration_number']}",
                f"Department: {first_result['department']}",
                f"Exam Date: {first_result['date']}",
                f"Session: {first_result['session_name']} ({first_result['session']})",
                f"Room Number: {first_result['room_number']}",
                f"Seat Number: {first_result['seat_number']}",
                f"Venue: {first_result['venue_name']}",
                "",
                f"Generated: {datetime.now().strftime('%d %B %Y at %H:%M')}",
                "Powered by SRM Seat Finder"
            ]
            
            for detail in exam_details:
                c.drawString(50, y_position, detail)
                y_position -= line_height
        else:
            # Multiple exams - comprehensive schedule
            c.setFont("Helvetica-Bold", 20)
            c.drawString(50, height - 50, "SRM EXAM SCHEDULE")
            
            c.setFont("Helvetica", 12)
            y_position = height - 100
            line_height = 20
            
            # Header information
            header_details = [
                f"Registration Number: {first_result['registration_number']}",
                f"Department: {first_result['department']}",
                f"Total Exams: {len(results)}",
                ""
            ]
            
            for detail in header_details:
                c.drawString(50, y_position, detail)
                y_position -= line_height
            
            # Each exam details
            for i, result in enumerate(results, 1):
                # Check if we need a new page
                if y_position < 150:  # Leave space for footer
                    c.showPage()
                    y_position = height - 50
                
                c.setFont("Helvetica-Bold", 14)
                c.drawString(50, y_position, f"EXAM {i}:")
                y_position -= line_height + 5
                
                c.setFont("Helvetica", 12)
                exam_details = [
                    f"Date: {result['date']}",
                    f"Session: {result['session_name']} ({result['session']})",
                    f"Room Number: {result['room_number']}",
                    f"Seat Number: {result['seat_number']}",
                    f"Venue: {result['venue_name']}",
                    ""
                ]
                
                for detail in exam_details:
                    c.drawString(70, y_position, detail)
                    y_position -= line_height
            
            # Footer
            if y_position < 100:
                c.showPage()
                y_position = height - 50
            
            y_position -= 10
            c.setFont("Helvetica", 10)
            c.drawString(50, y_position, f"Generated: {datetime.now().strftime('%d %B %Y at %H:%M')}")
            y_position -= 15
            c.drawString(50, y_position, "Powered by SRM Seat Finder")
        
        c.save()
        pdf_buffer.seek(0)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exam_details_{timestamp}.pdf"
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        app.logger.error(f"PDF generation error: {e}")
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500

@app.route('/api/health')
def health_check():
    """Serverless health check endpoint"""
    try:
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'message': '⚡ SRM Serverless Seat Finder API',
            'version': '4.0.0-serverless',
            'environment': {
                'deployment': 'serverless',
                'is_serverless': scaling_config.is_serverless,
                'description': scaling_config.config['description']
            },
            'sessions': {
                'active_sessions': session_manager.get_session_count(),
                'session_storage': 'Redis' if session_manager.redis_client else 'Memory'
            },
            'features': {
                'pdf_export': True,
                'whatsapp_sharing': True,
                'multi_venue_search': True,
                'comprehensive_search': True,
                'serverless_optimized': True,
                'session_persistence': True
            }
        }
        
        return jsonify(health_data), 200
        
    except Exception as e:
        app.logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500

@app.after_request
def add_cache_headers(response):
    """Add appropriate cache headers based on content type"""
    if request.endpoint == 'static':
        # Static files: cache for 1 hour but allow revalidation
        response.headers['Cache-Control'] = 'public, max-age=3600, must-revalidate'
    elif request.endpoint in ['index']:
        # HTML pages: no cache
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    elif request.path.startswith('/api/'):
        # API responses: no cache
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    return response

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Local development server
    # Create templates and static directories if they don't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('static/images', exist_ok=True)
    
    # Local development port
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 