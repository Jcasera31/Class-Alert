"""
PDF parsing utility for extracting schedule data from COR (Certificate of Registration) PDFs
"""

import re
from PyPDF2 import PdfReader
from io import BytesIO


def extract_text_from_pdf(file_path):
    """
    Extract all text from a PDF file
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text as string
    """
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None


def parse_schedule_from_text(text):
    """
    Parse schedule entries from COR text in SNSU format
    Handles multi-line course entries properly
    
    Args:
        text: Extracted text from PDF
        
    Returns:
        List of dictionaries with schedule data
    """
    if not text:
        return []
    
    schedules = []
    
    # Extract semester and academic year
    semester = ""
    academic_year = ""
    sem_match = re.search(r'(\d+(?:st|nd|rd|th)\s+Semester),?\s+(?:AY\s+)?(\d{4}\s*-\s*\d{4})', text, re.IGNORECASE)
    if sem_match:
        semester = sem_match.group(1).strip()
        academic_year = sem_match.group(2).strip().replace(' ', '')
    
    # Split by lines and reconstruct multi-line course entries
    lines = text.split('\n')
    
    # Find course entries starting from the table header
    table_start_idx = -1
    for idx, line in enumerate(lines):
        if 'Code' in line and 'Course' in line:
            table_start_idx = idx + 1
            break
    
    if table_start_idx == -1:
        return []
    
    # Reconstruct full course entries (some span multiple lines)
    course_entries = []
    current_entry = ""
    
    for i in range(table_start_idx, len(lines)):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Check if this starts a new course entry (starts with digits like "1049")
        if re.match(r'^\d{4}\s+BSCS', line):
            # Save previous entry if exists
            if current_entry:
                course_entries.append(current_entry)
            current_entry = line
        else:
            # Continue building current entry if we're in one
            if current_entry:
                current_entry += " " + line
            # Stop when we hit "Total Units"
            if 'Total Units' in line:
                if current_entry:
                    course_entries.append(current_entry)
                break
    
    # If there's a last entry still in progress
    if current_entry and 'Total Units' not in current_entry:
        course_entries.append(current_entry)
    
    # Parse each course entry
    for entry in course_entries:
        # Extract course name/code
        course_match = re.search(r'(CS\s+\d+[A-Z]?-[^[]+?)(?:\[|$)', entry)
        if not course_match:
            continue
        
        course_name = course_match.group(1).strip()
        # Clean up multi-line course names
        course_name = re.sub(r'\s+', ' ', course_name)
        
        # Extract all day brackets and time brackets
        # The pattern in COR is: [Days]; [Days][Time]; or [Days][Time]
        
        # Find all segments separated by semicolons (each represents one schedule)
        segments = entry.split(';')
        
        processed_schedules = []
        
        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue
            
            # Extract all bracketed items in this segment
            brackets = re.findall(r'\[([^\]]+)\]', segment)
            
            if not brackets:
                continue
            
            # Separate days, times, and other info
            days_str = None
            time_str = None
            
            for bracket in brackets:
                # Check if it's a day bracket (contains M, T, W, Th, F, S, Su)
                if re.search(r'[MWTF]', bracket) and not ':' in bracket:
                    days_str = bracket
                # Check if it's a time bracket (contains colon for time)
                elif ':' in bracket and ('PM' in bracket.upper() or 'AM' in bracket.upper()):
                    time_str = bracket
            
            # Only add if we have BOTH days AND time (skip entries with missing info)
            if days_str and time_str:
                days_formatted = convert_day_abbreviations(days_str)
                
                if days_formatted:
                    processed_schedules.append({
                        'subject': course_name,
                        'days': days_formatted,
                        'time': time_str.strip(),
                        'semester': semester,
                        'academic_year': academic_year
                    })
        
        # Add processed schedules, avoiding duplicates
        for sched in processed_schedules:
            if sched not in schedules:
                schedules.append(sched)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_schedules = []
    for sched in schedules:
        key = (sched['subject'], sched['days'], sched['time'])
        if key not in seen:
            seen.add(key)
            unique_schedules.append(sched)
    
    return unique_schedules


def convert_day_abbreviations(day_str):
    """
    Convert day abbreviations to full day names
    M -> Monday, T -> Tuesday, W -> Wednesday, Th -> Thursday, F -> Friday
    
    Args:
        day_str: String like "M,W" or "T,Th"
        
    Returns:
        Formatted string like "Mon, Wed" or "Tue, Thu"
    """
    day_map = {
        'M': 'Mon',
        'T': 'Tue',
        'W': 'Wed',
        'Th': 'Thu',
        'F': 'Fri',
        'S': 'Sat',
        'Su': 'Sun'
    }
    
    # Split by comma and process each day
    days = [d.strip() for d in day_str.split(',')]
    converted = []
    
    i = 0
    while i < len(days):
        day = days[i].strip()
        # Check if it's a two-letter abbreviation (like "Th")
        if i + 1 < len(days) and len(day) == 1 and days[i+1].strip() == 'h':
            full_day = day_map.get('Th', 'Thu')
            converted.append(full_day)
            i += 2
        elif day in day_map:
            converted.append(day_map[day])
            i += 1
        else:
            i += 1
    
    return ', '.join(converted) if converted else ""


def parse_cor_pdf(file_path):
    """
    Main function to parse a COR PDF and extract schedule data
    
    Args:
        file_path: Path to the COR PDF file
        
    Returns:
        List of schedule dictionaries or None if parsing fails
    """
    # Extract text from PDF
    text = extract_text_from_pdf(file_path)
    
    if text is None:
        return None
    
    # Parse schedule from text
    schedules = parse_schedule_from_text(text)
    
    return schedules
