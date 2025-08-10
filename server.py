from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import logging
import traceback
from datetime import datetime
from dotenv import load_dotenv
import os

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Database configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', 'desirability_form.db')

def init_database():
    """Initialize the SQLite database and create tables if they don't exist"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS desirability_form_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            gender TEXT,
            age INTEGER,
            city TEXT,
            email TEXT,
            phone TEXT,
            occupation TEXT,
            frustration_no_buddies INTEGER DEFAULT 0,
            frustration_social_rut INTEGER DEFAULT 0,
            frustration_starting_convos INTEGER DEFAULT 0,
            frustration_similar_interests INTEGER DEFAULT 0,
            frustration_short_notice INTEGER DEFAULT 0,
            frustration_isolated_new_place INTEGER DEFAULT 0,
            weekend_options TEXT,
            meeting_feeling TEXT,
            vibe_selections TEXT,
            last_new_thing TEXT,
            meeting_blocker TEXT,
            safe_fun_option TEXT,
            platform_likelihood TEXT,
            challenges TEXT,
            features TEXT,
            safety TEXT,
            scenarios TEXT,
            submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {DATABASE_PATH}")

def get_db_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # This allows dict-like access to rows
    return conn

def get_answers(form_data, response_name):
    """Safely extract answers for a response group"""
    try:
        # Navigate through the response structure: responses > group name > answers
        group_data = form_data.get('responses', {}).get(response_name, {})
        answers = group_data.get('answers', [])
        return ','.join(str(item['value']) for item in answers)
    except (KeyError, TypeError):
        logger.warning(f"Missing answers for {response_name}")
        return ''

@app.route('/')
def index():
    """Serve the main index.html page"""
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def handle_form_submission():
    conn = None
    cursor = None
    try:
        form_data = request.get_json()
        logger.info("Form submission received")
        
        # Log incoming data for debugging
        logger.debug(f"Full submission data: {form_data}")
        
        # Required personal info validation
        required_fields = ['name', 'gender', 'age', 'city', 'email', 'occupation']
        personal_info = form_data.get('personalInfo', {})
        
        # missing_fields = [f for f in required_fields if f not in personal_info or not personal_info[f]]
        # if missing_fields:
        #     return jsonify({
        #         'success': False,
        #         'error': f'Missing required fields: {", ".join(missing_fields)}'
        #     }), 400

        # Process frustration ratings
        frustrations = form_data.get('responses', {}).get('frustrations', {}).get('ratings', [])
        frustration_values = {
            "No event buddies": 0,
            "Stuck in a social rut": 0,
            "Struggling with starting conversations": 0,
            "Difficulty finding people with similar interests": 0,
            "No plans on short notice": 0,
            "Feeling isolated in a new place": 0
        }
        
        for item in frustrations:
            title = item.get('title', '')
            if title in frustration_values:
                frustration_values[title] = int(item.get('value', 0))

        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert data
        cursor.execute("""
            INSERT INTO desirability_form_responses (
                full_name, gender, age, city, email, phone, occupation,
                frustration_no_buddies, frustration_social_rut,
                frustration_starting_convos, frustration_similar_interests,
                frustration_short_notice, frustration_isolated_new_place,
                weekend_options, meeting_feeling, vibe_selections,
                last_new_thing, meeting_blocker, safe_fun_option,
                platform_likelihood, challenges, features, safety, scenarios,
                submission_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                personal_info.get('name', ''),
                personal_info.get('gender', ''),
                personal_info.get('age', 0),
                personal_info.get('city', ''),
                personal_info.get('email', ''),
                personal_info.get('phone', ''),
                personal_info.get('occupation', ''),
                frustration_values["No event buddies"],
                frustration_values["Stuck in a social rut"],
                frustration_values["Struggling with starting conversations"],
                frustration_values["Difficulty finding people with similar interests"],
                frustration_values["No plans on short notice"],
                frustration_values["Feeling isolated in a new place"],
                # Get answers for each response group
                get_answers(form_data, 'weekend'),
                get_answers(form_data, 'meeting'),
                get_answers(form_data, 'vibe'),
                get_answers(form_data, 'new_things'),
                get_answers(form_data, 'blockers'),
                get_answers(form_data, 'safe_fun'),
                get_answers(form_data, 'platform'),
                get_answers(form_data, 'challenges'),
                get_answers(form_data, 'features'),
                get_answers(form_data, 'safety'),
                get_answers(form_data, 'scenarios'),
                datetime.now().isoformat()
            ))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Form submitted successfully',
            'submission_id': cursor.lastrowid
        })
        
    except sqlite3.Error as e:
        logger.error(f"SQLite Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Database error: {str(e)}"
        }), 500
    except Exception as e:
        logger.error(f"Error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/answers', methods=['GET'])
def get_answers_route():
    """Get all form responses from database"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get query parameters for filtering/pagination
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        email_filter = request.args.get('email', '')
        
        # Build query with optional email filter
        base_query = """
            SELECT id, full_name, gender, age, city, email, phone, occupation,
                   frustration_no_buddies, frustration_social_rut,
                   frustration_starting_convos, frustration_similar_interests,
                   frustration_short_notice, frustration_isolated_new_place,
                   weekend_options, meeting_feeling, vibe_selections,
                   last_new_thing, meeting_blocker, safe_fun_option,
                   platform_likelihood, challenges, features, safety, scenarios,
                   submission_date
            FROM desirability_form_responses
        """
        
        params = []
        if email_filter:
            base_query += " WHERE email LIKE ?"
            params.append(f"%{email_filter}%")
            
        base_query += " ORDER BY submission_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(base_query, params)
        results = cursor.fetchall()
        
        # Convert sqlite3.Row objects to dictionaries
        responses = []
        for row in results:
            response_dict = dict(row)
            responses.append(response_dict)
        
        # Get total count for pagination info
        count_query = "SELECT COUNT(*) as total FROM desirability_form_responses"
        count_params = []
        if email_filter:
            count_query += " WHERE email LIKE ?"
            count_params.append(f"%{email_filter}%")
            
        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()['total']
        
        return jsonify({
            'success': True,
            'data': responses,
            'pagination': {
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'count': len(responses)
            }
        })
        
    except sqlite3.Error as e:
        logger.error(f"SQLite Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Database error: {str(e)}"
        }), 500
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/answers/<int:response_id>', methods=['GET'])
def get_single_answer(response_id):
    """Get a specific form response by ID"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, full_name, gender, age, city, email, phone, occupation,
                   frustration_no_buddies, frustration_social_rut,
                   frustration_starting_convos, frustration_similar_interests,
                   frustration_short_notice, frustration_isolated_new_place,
                   weekend_options, meeting_feeling, vibe_selections,
                   last_new_thing, meeting_blocker, safe_fun_option,
                   platform_likelihood, challenges, features, safety, scenarios,
                   submission_date
            FROM desirability_form_responses
            WHERE id = ?
        """, (response_id,))
        
        result = cursor.fetchone()
        
        if result:
            response_dict = dict(result)
            return jsonify({
                'success': True,
                'data': response_dict
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Response not found'
            }), 404
            
    except sqlite3.Error as e:
        logger.error(f"SQLite Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Database error: {str(e)}"
        }), 500
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/answers/summary', methods=['GET'])
def get_answers_summary():
    """Get summary statistics of form responses"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get basic counts
        cursor.execute("SELECT COUNT(*) as total FROM desirability_form_responses")
        total_responses = cursor.fetchone()['total']
        
        # Get gender distribution
        cursor.execute("""
            SELECT gender, COUNT(*) as count 
            FROM desirability_form_responses 
            WHERE gender IS NOT NULL AND gender != ''
            GROUP BY gender
        """)
        gender_stats = cursor.fetchall()
        
        # Get age statistics
        cursor.execute("""
            SELECT 
                AVG(age) as avg_age,
                MIN(age) as min_age,
                MAX(age) as max_age
            FROM desirability_form_responses 
            WHERE age > 0
        """)
        age_stats = cursor.fetchone()
        
        # Get top cities
        cursor.execute("""
            SELECT city, COUNT(*) as count 
            FROM desirability_form_responses 
            WHERE city IS NOT NULL AND city != ''
            GROUP BY city 
            ORDER BY count DESC 
            LIMIT 10
        """)
        city_stats = cursor.fetchall()
        
        # Get average frustration scores
        cursor.execute("""
            SELECT 
                AVG(frustration_no_buddies) as avg_no_buddies,
                AVG(frustration_social_rut) as avg_social_rut,
                AVG(frustration_starting_convos) as avg_starting_convos,
                AVG(frustration_similar_interests) as avg_similar_interests,
                AVG(frustration_short_notice) as avg_short_notice,
                AVG(frustration_isolated_new_place) as avg_isolated_new_place
            FROM desirability_form_responses
        """)
        frustration_stats = cursor.fetchone()
        
        return jsonify({
            'success': True,
            'summary': {
                'total_responses': total_responses,
                'gender_distribution': [dict(row) for row in gender_stats],
                'age_statistics': dict(age_stats) if age_stats else {},
                'top_cities': [dict(row) for row in city_stats],
                'average_frustration_scores': dict(frustration_stats) if frustration_stats else {}
            }
        })
        
    except sqlite3.Error as e:
        logger.error(f"SQLite Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Database error: {str(e)}"
        }), 500
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({'status': 'healthy', 'database': DATABASE_PATH})

if __name__ == '__main__':
    # Initialize database on startup
    init_database()
    app.run(host='0.0.0.0', port=5501, debug=True)