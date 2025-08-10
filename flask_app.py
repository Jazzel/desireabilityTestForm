from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
import pymysql
import logging
import traceback
from datetime import datetime
from dotenv import load_dotenv
import os
import io
import csv

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Database configuration for PythonAnywhere MySQL
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'junoform.mysql.pythonanywhere-services.com'),
    'user': os.getenv('DB_USER', 'junoform'),
    'password': os.getenv('DB_PASSWORD', '4d7CDntp6rZ6Xud'),
    'database': os.getenv('DB_NAME', 'junoform$default'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'charset': 'utf8mb4'
}

def get_db_connection():
    """Get MySQL database connection"""
    return pymysql.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        port=DB_CONFIG['port'],
        charset=DB_CONFIG['charset'],
        cursorclass=pymysql.cursors.DictCursor
    )

def init_database():
    """Initialize the MySQL database and create tables if they don't exist"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS desirability_form_responses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(255),
                gender VARCHAR(50),
                age INT,
                city VARCHAR(100),
                email VARCHAR(255),
                phone VARCHAR(20),
                occupation VARCHAR(255),
                frustration_no_buddies INT DEFAULT 0,
                frustration_social_rut INT DEFAULT 0,
                frustration_starting_convos INT DEFAULT 0,
                frustration_similar_interests INT DEFAULT 0,
                frustration_short_notice INT DEFAULT 0,
                frustration_isolated_new_place INT DEFAULT 0,
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
        cursor.close()
        conn.close()
        logger.info("Database table initialized successfully")
        
    except pymysql.Error as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

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
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                datetime.now()
            ))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Form submitted successfully',
            'submission_id': cursor.lastrowid
        })
        
    except pymysql.Error as e:
        logger.error(f"MySQL Error [{e.args[0]}]: {e.args[1]}")
        return jsonify({
            'success': False,
            'error': f"Database error: {e.args[1]}"
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
            base_query += " WHERE email LIKE %s"
            params.append(f"%{email_filter}%")
            
        base_query += " ORDER BY submission_date DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(base_query, params)
        results = cursor.fetchall()
        
        # Get total count for pagination info
        count_query = "SELECT COUNT(*) as total FROM desirability_form_responses"
        count_params = []
        if email_filter:
            count_query += " WHERE email LIKE %s"
            count_params.append(f"%{email_filter}%")
            
        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()['total']
        
        return jsonify({
            'success': True,
            'data': results,
            'pagination': {
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'count': len(results)
            }
        })
        
    except pymysql.Error as e:
        logger.error(f"MySQL Error: {str(e)}")
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
            WHERE id = %s
        """, (response_id,))
        
        result = cursor.fetchone()
        
        if result:
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Response not found'
            }), 404
            
    except pymysql.Error as e:
        logger.error(f"MySQL Error: {str(e)}")
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
                'gender_distribution': gender_stats,
                'age_statistics': age_stats if age_stats else {},
                'top_cities': city_stats,
                'average_frustration_scores': frustration_stats if frustration_stats else {}
            }
        })
        
    except pymysql.Error as e:
        logger.error(f"MySQL Error: {str(e)}")
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

@app.route('/api/data/export', methods=['GET'])
def export_data():
    """Export all data in CSV or JSON format for PowerBI"""
    conn = None
    cursor = None
    try:
        format_type = request.args.get('format', 'json').lower()
        api_key = request.args.get('api_key', '')
        
        # Optional: Add simple API key authentication
        # expected_key = os.getenv('API_KEY', 'your-secret-key')
        # if api_key != expected_key:
        #     return jsonify({'error': 'Invalid API key'}), 401
        
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
            ORDER BY submission_date DESC
        """)
        
        results = cursor.fetchall()
        
        if format_type == 'csv':
            output = io.StringIO()
            if results:
                # Get column names from the first row
                fieldnames = list(results[0].keys())
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                
                for row in results:
                    writer.writerow(row)
            
            response = Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment; filename=form_responses.csv'}
            )
            return response
        
        else:  # JSON format (default)
            return jsonify({
                'success': True,
                'data': results,
                'total_records': len(results),
                'export_date': datetime.now().isoformat()
            })
            
    except pymysql.Error as e:
        logger.error(f"MySQL Error: {str(e)}")
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

@app.route('/api/data/powerbi', methods=['GET'])
def powerbi_endpoint():
    """Specialized endpoint for PowerBI with flattened data structure"""
    conn = None
    cursor = None
    try:
        api_key = request.args.get('api_key', '')
        
        # Optional: Add API key authentication
        # expected_key = os.getenv('API_KEY', 'your-secret-key')
        # if api_key != expected_key:
        #     return jsonify({'error': 'Invalid API key'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all data with flattened structure for PowerBI
        cursor.execute("""
            SELECT 
                id,
                full_name,
                gender,
                age,
                city,
                email,
                occupation,
                frustration_no_buddies as frustration_score_no_buddies,
                frustration_social_rut as frustration_score_social_rut,
                frustration_starting_convos as frustration_score_starting_conversations,
                frustration_similar_interests as frustration_score_similar_interests,
                frustration_short_notice as frustration_score_short_notice,
                frustration_isolated_new_place as frustration_score_isolated_new_place,
                weekend_options,
                meeting_feeling,
                vibe_selections,
                last_new_thing,
                meeting_blocker,
                safe_fun_option,
                platform_likelihood,
                challenges,
                features,
                safety,
                scenarios,
                DATE(submission_date) as submission_date,
                TIME(submission_date) as submission_time
            FROM desirability_form_responses
            ORDER BY submission_date DESC
        """)
        
        results = cursor.fetchall()
        
        # Return in PowerBI-friendly format
        return jsonify({
            'value': results  # PowerBI expects data in 'value' field for OData-like format
        })
            
    except pymysql.Error as e:
        logger.error(f"MySQL Error: {str(e)}")
        return jsonify({
            'error': f"Database error: {str(e)}"
        }), 500
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            'error': str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/init-db', methods=['POST'])
def init_db_route():
    """Manual database initialization endpoint"""
    try:
        init_database()
        return jsonify({
            'success': True,
            'message': 'Database initialized successfully',
            'database_host': DB_CONFIG['host'],
            'database_name': DB_CONFIG['database']
        })
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Enhanced health check endpoint with database info"""
    try:
        # Test database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Test if table exists
        cursor.execute("""
            SELECT COUNT(*) as table_count 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = 'desirability_form_responses'
        """, (DB_CONFIG['database'],))
        
        table_result = cursor.fetchone()
        table_exists = table_result['table_count'] > 0
        
        # Get record count if table exists
        record_count = 0
        if table_exists:
            cursor.execute("SELECT COUNT(*) as count FROM desirability_form_responses")
            record_count = cursor.fetchone()['count']
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'database': {
                'host': DB_CONFIG['host'],
                'database': DB_CONFIG['database'],
                'connection': 'successful',
                'table_exists': table_exists,
                'record_count': record_count
            }
        })
        
    except pymysql.Error as e:
        return jsonify({
            'status': 'error',
            'database': {
                'host': DB_CONFIG['host'],
                'database': DB_CONFIG['database'],
                'connection': 'failed',
                'error': f"MySQL Error: {str(e)}"
            }
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Initialize database on startup
    try:
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    
    # Use environment PORT for production deployment
    port = int(os.getenv('PORT', 5501))
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)

# Initialize database when imported (for WSGI servers like gunicorn)
try:
    init_database()
except Exception as e:
    logger.error(f"Failed to initialize database on import: {e}")