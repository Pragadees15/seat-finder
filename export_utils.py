#!/usr/bin/env python3
"""
Enhanced Export Utilities for SRM Exam Seat Finder
PDF generation for exam seat allocations

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

import io
import base64
import json
import urllib.parse
from datetime import datetime, timedelta

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors as reportlab_colors
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import tempfile
import os



class ExamExportUtils:
    """Enhanced export utilities for PDF generation"""
    
    def __init__(self):
        self.colors = {
            'primary': '#007AFF',
            'success': '#34C759', 
            'warning': '#FF9500',
            'danger': '#FF3B30',
            'background': '#F2F2F7',
            'card_bg': '#FFFFFF',
            'text_primary': '#000000',
            'text_secondary': '#3C3C43'
        }
        
        # Premium color palette for PDF
        self.pdf_colors = {
            'navy': reportlab_colors.HexColor('#0D1B2A'),
            'blue': reportlab_colors.HexColor('#1B4B73'),
            'green': reportlab_colors.HexColor('#2E8B57'),
            'gold': reportlab_colors.HexColor('#FFD700'),
            'light_gray': reportlab_colors.HexColor('#F8FAFC'),
            'dark_gray': reportlab_colors.HexColor('#2D3748'),
            'medium_gray': reportlab_colors.HexColor('#4A5568'),
            'border': reportlab_colors.HexColor('#E1E5E9'),
        }
    
    def generate_exam_card_pdf(self, seat_info):
        """Generate a premium PDF exam card"""
        try:
            # Create PDF in memory
            buffer = io.BytesIO()
            
            # Use A4 size for professional documents
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=20*mm,
                leftMargin=20*mm,
                topMargin=20*mm,
                bottomMargin=20*mm,
                title="SRM Exam Seat Allocation",
                author="SRM Exam Seat Finder"
            )
            
            # Create custom styles
            styles = getSampleStyleSheet()
            
            # Header styles
            header_style = ParagraphStyle(
                'CustomHeader',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=self.pdf_colors['navy'],
                fontName='Helvetica-Bold'
            )
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading2'],
                fontSize=18,
                spaceAfter=20,
                alignment=TA_CENTER,
                textColor=self.pdf_colors['blue'],
                fontName='Helvetica-Bold'
            )
            
            section_style = ParagraphStyle(
                'SectionHeader',
                parent=styles['Heading3'],
                fontSize=16,
                spaceBefore=20,
                spaceAfter=10,
                textColor=self.pdf_colors['navy'],
                fontName='Helvetica-Bold',
                backColor=self.pdf_colors['light_gray'],
                borderPadding=8,
                leftIndent=10
            )
            
            label_style = ParagraphStyle(
                'Label',
                parent=styles['Normal'],
                fontSize=12,
                textColor=self.pdf_colors['medium_gray'],
                fontName='Helvetica-Bold',
                spaceAfter=5
            )
            
            value_style = ParagraphStyle(
                'Value',
                parent=styles['Normal'],
                fontSize=14,
                textColor=self.pdf_colors['dark_gray'],
                fontName='Helvetica',
                spaceAfter=15
            )
            
            highlight_style = ParagraphStyle(
                'Highlight',
                parent=styles['Normal'],
                fontSize=16,
                textColor=reportlab_colors.white,
                fontName='Helvetica-Bold',
                backColor=self.pdf_colors['green'],
                borderPadding=10,
                alignment=TA_CENTER,
                spaceAfter=15
            )
            
            # Build the document content
            story = []
            
            # Header Section
            story.append(Paragraph("SRM INSTITUTE OF SCIENCE AND TECHNOLOGY", header_style))
            story.append(Paragraph("EXAMINATION SEAT ALLOCATION", title_style))
            
            # Academic Year Badge
            academic_year = Paragraph(
                "ACADEMIC YEAR 2024-2025",
                ParagraphStyle(
                    'AcademicYear',
                    parent=styles['Normal'],
                    fontSize=12,
                    alignment=TA_CENTER,
                    textColor=self.pdf_colors['navy'],
                    fontName='Helvetica-Bold',
                    backColor=self.pdf_colors['gold'],
                    borderPadding=8,
                    spaceAfter=30
                )
            )
            story.append(academic_year)
            story.append(Spacer(1, 20))
            
            # Student Information Section
            story.append(Paragraph("📋 STUDENT INFORMATION", section_style))
            
            # Create a table for student information to ensure proper layout
            student_data = [
                ['Registration Number:', seat_info['registration_number']],
                ['Department:', seat_info['department']]
            ]
            
            student_table = Table(student_data, colWidths=[150, 250])
            student_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (0, 0), (0, -1), self.pdf_colors['medium_gray']),
                ('TEXTCOLOR', (1, 0), (1, -1), self.pdf_colors['dark_gray']),
                ('PADDING', (0, 0), (-1, -1), 12),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, self.pdf_colors['border']),
                # Highlight registration number
                ('BACKGROUND', (1, 0), (1, 0), self.pdf_colors['green']),
                ('TEXTCOLOR', (1, 0), (1, 0), reportlab_colors.white),
                ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (1, 0), (1, 0), 14),
                # Keep normal background for department
                ('BACKGROUND', (1, 1), (1, 1), reportlab_colors.white),
            ]))
            
            story.append(student_table)
            story.append(Spacer(1, 20))
            
            # Examination Details Section
            story.append(Paragraph("🎓 EXAMINATION DETAILS", section_style))
            
            # Create a table for examination details
            exam_data = [
                ['📅 Examination Date:', seat_info['date']],
                ['⏰ Session:', f"{seat_info['session_name']} ({seat_info['session']})"],
                ['🏫 Venue:', seat_info.get('venue_name', 'Main Campus')],
                ['🏢 Room Number:', seat_info['room_number']],
                ['💺 Seat Number:', seat_info['seat_number']]
            ]
            
            exam_table = Table(exam_data, colWidths=[150, 200])
            exam_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (0, 0), (0, -1), self.pdf_colors['medium_gray']),
                ('TEXTCOLOR', (1, 0), (1, -1), self.pdf_colors['dark_gray']),
                ('PADDING', (0, 0), (-1, -1), 12),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, self.pdf_colors['border']),
                # Highlight venue in blue
                ('BACKGROUND', (1, 2), (1, 2), self.pdf_colors['blue']),
                ('TEXTCOLOR', (1, 2), (1, 2), reportlab_colors.white),
                ('FONTNAME', (1, 2), (1, 2), 'Helvetica-Bold'),
                # Highlight room and seat numbers in green (adjusted row indices)
                ('BACKGROUND', (1, 3), (1, 4), self.pdf_colors['green']),
                ('TEXTCOLOR', (1, 3), (1, 4), reportlab_colors.white),
                ('FONTNAME', (1, 3), (1, 4), 'Helvetica-Bold'),
                ('FONTSIZE', (1, 3), (1, 4), 14),
            ]))
            
            story.append(exam_table)
            story.append(Spacer(1, 30))
            
            # Timing Information
            story.append(Paragraph("⏰ EXAMINATION SCHEDULE", section_style))
            
            if seat_info['session'] == 'FN':
                timing_text = "🌅 Forenoon Session: 10:00 AM - 01:00 PM"
            else:
                timing_text = "🌇 Afternoon Session: 02:00 PM - 05:00 PM"
            
            timing_info = [
                [timing_text],
                ['⏳ Duration: 3 Hours'],
                ['📝 Instructions: Report 30 minutes before exam time']
            ]
            
            timing_table = Table(timing_info, colWidths=[400])
            timing_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('TEXTCOLOR', (0, 0), (-1, -1), self.pdf_colors['blue']),
                ('PADDING', (0, 0), (-1, -1), 15),
                ('BACKGROUND', (0, 0), (-1, -1), self.pdf_colors['light_gray']),
                ('GRID', (0, 0), (-1, -1), 1, self.pdf_colors['border']),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(timing_table)
            story.append(Spacer(1, 40))
            
            # Important Instructions Section
            story.append(Paragraph("📋 IMPORTANT INSTRUCTIONS", section_style))
            
            instructions_data = [
                ['✅ Arrival Time:', 'Report 30 minutes before exam time'],
                ['🆔 Required Documents:', 'Valid ID card and Hall Ticket'],
                ['📱 Mobile Phones:', 'Not allowed inside examination hall'],
                ['📝 Writing Materials:', 'Bring your own pen and pencil'],
                ['⏰ Entry Guidelines:', 'Late entry not permitted after exam starts']
            ]
            
            instructions_table = Table(instructions_data, colWidths=[150, 250])
            instructions_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('TEXTCOLOR', (0, 0), (0, -1), self.pdf_colors['navy']),
                ('TEXTCOLOR', (1, 0), (1, -1), self.pdf_colors['dark_gray']),
                ('PADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, self.pdf_colors['border']),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 0), (-1, -1), reportlab_colors.white),
            ]))
            
            story.append(instructions_table)
            story.append(Spacer(1, 30))
            

            
            # Enhanced Footer Information with proper spacing
            story.append(Spacer(1, 20))
            
            # Add divider line
            divider_table = Table([[''] * 5], colWidths=[100, 100, 100, 100, 100])
            divider_table.setStyle(TableStyle([
                ('LINEABOVE', (0, 0), (-1, 0), 2, self.pdf_colors['border']),
            ]))
            story.append(divider_table)
            story.append(Spacer(1, 15))
            
            # Enhanced footer with better formatting
            current_time = datetime.now()
            footer_data = [
                ['📅 Generated:', current_time.strftime('%d %B %Y at %H:%M')],
                ['🏢 Source:', 'SRM Exam Seat Finder - Official Portal'],
                ['⚠️ Note:', 'Computer-generated document. No signature required.'],
                ['📋 Reference:', f"SRM-SEAT-{seat_info['registration_number'][-6:]}-{current_time.strftime('%Y%m%d')}"]
            ]
            
            footer_table = Table(footer_data, colWidths=[120, 280])
            footer_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 0), (0, -1), self.pdf_colors['medium_gray']),
                ('TEXTCOLOR', (1, 0), (1, -1), self.pdf_colors['dark_gray']),
                ('PADDING', (0, 0), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            
            story.append(footer_table)
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            
            print("✅ Generated premium PDF exam card")
            return buffer.getvalue()
            
        except Exception as e:
            print(f"❌ Error generating PDF exam card: {e}")
            import traceback
            traceback.print_exc()
            return None
    

    




    def generate_comprehensive_exam_document(self, exam_list):
        """Generate comprehensive PDF document for multiple exams"""
        try:
            # Create PDF in memory
            buffer = io.BytesIO()
            
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=20*mm,
                leftMargin=20*mm,
                topMargin=20*mm,
                bottomMargin=20*mm,
                title="SRM Comprehensive Exam Schedule",
                author="SRM Exam Seat Finder"
            )
            
            styles = getSampleStyleSheet()
            
            # Custom styles
            main_title = ParagraphStyle(
                'MainTitle',
                parent=styles['Title'],
                fontSize=20,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=self.pdf_colors['navy'],
                fontName='Helvetica-Bold'
            )
            
            section_header = ParagraphStyle(
                'SectionHeader',
                parent=styles['Heading2'],
                fontSize=14,
                spaceBefore=20,
                spaceAfter=10,
                textColor=self.pdf_colors['navy'],
                fontName='Helvetica-Bold',
                backColor=self.pdf_colors['light_gray'],
                borderPadding=8
            )
            
            story = []
            
            # Main Header
            story.append(Paragraph("SRM INSTITUTE - COMPREHENSIVE EXAMINATION SCHEDULE", main_title))
            story.append(Paragraph(f"Complete Examination Schedule - {len(exam_list)} Sessions", 
                                 ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=12, 
                                              alignment=TA_CENTER, textColor=self.pdf_colors['blue'],
                                              spaceAfter=30)))
            
            # Student Information
            first_exam = exam_list[0]
            story.append(Paragraph("👤 STUDENT INFORMATION", section_header))
            
            student_data = [
                ['Registration Number:', first_exam['registration_number']],
                ['Department:', first_exam['department']],
                ['Academic Year:', '2024-2025']
            ]
            
            student_table = Table(student_data, colWidths=[120, 200])
            student_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (0, 0), (0, -1), self.pdf_colors['medium_gray']),
                ('TEXTCOLOR', (1, 0), (1, -1), self.pdf_colors['dark_gray']),
                ('PADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (1, 0), (1, 0), self.pdf_colors['green']),
                ('TEXTCOLOR', (1, 0), (1, 0), reportlab_colors.white),
                ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ]))
            
            story.append(student_table)
            story.append(Spacer(1, 30))
            
            # Examination Schedule Table
            story.append(Paragraph("📋 EXAMINATION SCHEDULE", section_header))
            
            # Table headers
            table_data = [['Date', 'Session', 'Room', 'Seat', 'Time']]
            
            # Table rows
            for exam in exam_list:
                session_time = "10:00 AM - 01:00 PM" if exam['session'] == 'FN' else "02:00 PM - 05:00 PM"
                table_data.append([
                    exam['date'],
                    f"{exam['session_name']} ({exam['session']})",
                    exam['room_number'],
                    exam['seat_number'],
                    session_time
                ])
            
            # Create table
            schedule_table = Table(table_data, colWidths=[80, 100, 60, 60, 100])
            schedule_table.setStyle(TableStyle([
                # Header styling
                ('BACKGROUND', (0, 0), (-1, 0), self.pdf_colors['navy']),
                ('TEXTCOLOR', (0, 0), (-1, 0), reportlab_colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                
                # Data styling
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('TEXTCOLOR', (0, 1), (-1, -1), self.pdf_colors['dark_gray']),
                ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                
                # Grid and padding
                ('GRID', (0, 0), (-1, -1), 1, self.pdf_colors['border']),
                ('PADDING', (0, 0), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                
                # Highlight room and seat columns
                ('BACKGROUND', (2, 1), (2, -1), self.pdf_colors['green']),
                ('BACKGROUND', (3, 1), (3, -1), self.pdf_colors['blue']),
                ('TEXTCOLOR', (2, 1), (3, -1), reportlab_colors.white),
                ('FONTNAME', (2, 1), (3, -1), 'Helvetica-Bold'),
                
                # Alternating row colors
                *[('BACKGROUND', (0, i), (1, i), self.pdf_colors['light_gray']) 
                  for i in range(2, len(table_data), 2)],
                *[('BACKGROUND', (4, i), (4, i), self.pdf_colors['light_gray']) 
                  for i in range(2, len(table_data), 2)],
            ]))
            
            story.append(schedule_table)
            story.append(Spacer(1, 30))
            
            # Summary Section
            summary_data = [
                [f"📊 Total Examinations: {len(exam_list)}"],
                [f"⏱️ Duration: 3 hours each"],
                [f"📅 Academic Year: 2024-2025"],
                [f"📄 Generated: {datetime.now().strftime('%d %B %Y at %H:%M')}"]
            ]
            
            summary_table = Table(summary_data, colWidths=[400])
            summary_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('TEXTCOLOR', (0, 0), (-1, -1), self.pdf_colors['blue']),
                ('PADDING', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (0, 0), (-1, -1), self.pdf_colors['light_gray']),
                ('GRID', (0, 0), (-1, -1), 1, self.pdf_colors['border']),
            ]))
            
            story.append(summary_table)
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            
            print("✅ Generated comprehensive PDF exam schedule")
            
            # Return PDF data
            return buffer.getvalue()
            
        except Exception as e:
            print(f"❌ Error generating comprehensive exam document: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_comprehensive_exam_document_pdf(self, exam_list):
        """Generate comprehensive PDF document for multiple exams - returns PDF data directly"""
        try:
            # Create PDF in memory
            buffer = io.BytesIO()
            
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=20*mm,
                leftMargin=20*mm,
                topMargin=20*mm,
                bottomMargin=20*mm,
                title="SRM Comprehensive Exam Schedule",
                author="SRM Exam Seat Finder"
            )
            
            styles = getSampleStyleSheet()
            
            # Custom styles
            main_title = ParagraphStyle(
                'MainTitle',
                parent=styles['Title'],
                fontSize=20,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=self.pdf_colors['navy'],
                fontName='Helvetica-Bold'
            )
            
            section_header = ParagraphStyle(
                'SectionHeader',
                parent=styles['Heading2'],
                fontSize=14,
                spaceBefore=20,
                spaceAfter=10,
                textColor=self.pdf_colors['navy'],
                fontName='Helvetica-Bold',
                backColor=self.pdf_colors['light_gray'],
                borderPadding=8
            )
            
            story = []
            
            # Main Header
            story.append(Paragraph("SRM INSTITUTE - COMPREHENSIVE EXAMINATION SCHEDULE", main_title))
            story.append(Paragraph(f"Complete Examination Schedule - {len(exam_list)} Sessions", 
                                 ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=12, 
                                              alignment=TA_CENTER, textColor=self.pdf_colors['blue'],
                                              spaceAfter=30)))
            
            # Student Information
            first_exam = exam_list[0]
            story.append(Paragraph("👤 STUDENT INFORMATION", section_header))
            
            student_data = [
                ['Registration Number:', first_exam['registration_number']],
                ['Department:', first_exam['department']],
                ['Academic Year:', '2024-2025']
            ]
            
            student_table = Table(student_data, colWidths=[120, 200])
            student_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (0, 0), (0, -1), self.pdf_colors['medium_gray']),
                ('TEXTCOLOR', (1, 0), (1, -1), self.pdf_colors['dark_gray']),
                ('PADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (1, 0), (1, 0), self.pdf_colors['green']),
                ('TEXTCOLOR', (1, 0), (1, 0), reportlab_colors.white),
                ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ]))
            
            story.append(student_table)
            story.append(Spacer(1, 30))
            
            # Examination Schedule Table
            story.append(Paragraph("📋 EXAMINATION SCHEDULE", section_header))
            
            # Table headers
            table_data = [['Date', 'Session', 'Venue', 'Room', 'Seat', 'Time']]
            
            # Table rows
            for exam in exam_list:
                session_time = "10:00 AM - 01:00 PM" if exam['session'] == 'FN' else "02:00 PM - 05:00 PM"
                table_data.append([
                    exam['date'],
                    f"{exam['session_name']} ({exam['session']})",
                    exam.get('venue_name', 'Main Campus'),
                    exam['room_number'],
                    exam['seat_number'],
                    session_time
                ])
            
            # Create table
            schedule_table = Table(table_data, colWidths=[65, 80, 85, 50, 50, 90])
            schedule_table.setStyle(TableStyle([
                # Header styling
                ('BACKGROUND', (0, 0), (-1, 0), self.pdf_colors['navy']),
                ('TEXTCOLOR', (0, 0), (-1, 0), reportlab_colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                
                # Data styling
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TEXTCOLOR', (0, 1), (-1, -1), self.pdf_colors['dark_gray']),
                ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                
                # Grid and padding
                ('GRID', (0, 0), (-1, -1), 1, self.pdf_colors['border']),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                
                # Highlight venue column in blue
                ('BACKGROUND', (2, 1), (2, -1), self.pdf_colors['blue']),
                ('TEXTCOLOR', (2, 1), (2, -1), reportlab_colors.white),
                ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
                
                # Highlight room and seat columns in green
                ('BACKGROUND', (3, 1), (3, -1), self.pdf_colors['green']),
                ('BACKGROUND', (4, 1), (4, -1), self.pdf_colors['green']),
                ('TEXTCOLOR', (3, 1), (4, -1), reportlab_colors.white),
                ('FONTNAME', (3, 1), (4, -1), 'Helvetica-Bold'),
                
                # Alternating row colors for date, session and time columns
                *[('BACKGROUND', (0, i), (1, i), self.pdf_colors['light_gray']) 
                  for i in range(2, len(table_data), 2)],
                *[('BACKGROUND', (5, i), (5, i), self.pdf_colors['light_gray']) 
                  for i in range(2, len(table_data), 2)],
            ]))
            
            story.append(schedule_table)
            story.append(Spacer(1, 30))
            
            # Summary Section
            summary_data = [
                [f"📊 Total Examinations: {len(exam_list)}"],
                [f"⏱️ Duration: 3 hours each"],
                [f"📅 Academic Year: 2024-2025"],
                [f"📄 Generated: {datetime.now().strftime('%d %B %Y at %H:%M')}"]
            ]
            
            summary_table = Table(summary_data, colWidths=[400])
            summary_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('TEXTCOLOR', (0, 0), (-1, -1), self.pdf_colors['blue']),
                ('PADDING', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (0, 0), (-1, -1), self.pdf_colors['light_gray']),
                ('GRID', (0, 0), (-1, -1), 1, self.pdf_colors['border']),
            ]))
            
            story.append(summary_table)
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            
            print("✅ Generated comprehensive PDF exam schedule (PDF format)")
            
            # Return PDF data directly instead of converting to PNG
            return buffer.getvalue()
            
        except Exception as e:
            print(f"❌ Error generating comprehensive exam document PDF: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def create_whatsapp_message(self, seat_info):
        """Create a formatted WhatsApp message"""
        try:
            message = f"""🎓 *SRM EXAM SEAT DETAILS*

📋 *Student Information:*
Registration: {seat_info['registration_number']}

🏛️ *Exam Details:*
📅 Date: {seat_info['date']}
⏰ Session: {seat_info['session_name']} ({seat_info['session']})
🏢 Department: {seat_info['department']}

🎯 *SEAT INFORMATION:*
🏫 Venue: *{seat_info.get('venue_name', 'Main Campus')}*
🏢 Room Number: *{seat_info['room_number']}*
💺 Seat Number: *{seat_info['seat_number']}*

⏰ Don't forget your exam! Good luck! 🍀

_Generated by SRM Exam Seat Finder_"""
            
            return message
            
        except Exception as e:
            print(f"Error creating WhatsApp message: {e}")
            return None
    
    def generate_whatsapp_url(self, message, phone_number=None):
        """Generate WhatsApp sharing URL"""
        try:
            encoded_message = urllib.parse.quote(message)
            
            if phone_number:
                # Send to specific number
                url = f"https://wa.me/{phone_number}?text={encoded_message}"
            else:
                # Open WhatsApp to choose contact
                url = f"https://wa.me/?text={encoded_message}"
            
            return url
            
        except Exception as e:
            print(f"Error generating WhatsApp URL: {e}")
            return None
    

    
    def create_pdf_report(self, seat_info_list):
        """Create a comprehensive PDF report - REMOVED"""
        return None
    

    
    def pdf_to_base64(self, pdf_data):
        """Convert PDF data to base64 string"""
        try:
            pdf_base64 = base64.b64encode(pdf_data).decode()
            return f"data:application/pdf;base64,{pdf_base64}"
        except Exception as e:
            print(f"Error converting PDF to base64: {e}")
            return None 