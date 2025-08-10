from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
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
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'port': int(os.getenv('DB_PORT', 3306))
}

def get_db_connection():
    return pymysql.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        port=DB_CONFIG['port'],
        cursorclass=pymysql.cursors.DictCursor
    )

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
                personal_info['name'],
                personal_info['gender'],
                personal_info['age'],
                personal_info['city'],
                personal_info['email'],
                personal_info.get('phone', ''),
                personal_info['occupation'],
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5501, debug=True)