from flask import Flask, render_template, request, session, jsonify, abort
import os
from flask_migrate import Migrate
from dotenv import load_dotenv
from flask_restful import Api
from resource.user import ShowEquipments, Equipments,  Students, PendingItems, BorrowedItems, CompletedItems, EachStudent
from models.database import db, Student
from flask_cors import CORS
from route.admin import admin_bp 
from datetime import timedelta

load_dotenv() 
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root:@localhost:3306/case_study_2023"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)  # Example: 1 day
app.config['SESSION_PERMANENT'] = True


app.secret_key = os.getenv("SECRET_KEY") 
db.init_app(app)
migrate = Migrate(app, db)
api = Api(app)


CORS(app, supports_credentials=True, resources={r"/user/*": {"origins": ["*"]}})

api.add_resource(EachStudent, '/user/student/<string:student_number>')
api.add_resource(Students, '/user/student')
api.add_resource(CompletedItems, '/user/completed-items')
api.add_resource(BorrowedItems, '/user/borrowed-items')
api.add_resource(PendingItems, '/user/pending-items')
api.add_resource(ShowEquipments, '/user/equipments/all')
api.add_resource(Equipments, '/user/equipments/<string:unique_key>')

app.register_blueprint(admin_bp)

@app.route('/', methods=['POST', 'GET'])
def index():
    session.clear()
    return render_template('index.html')

@app.route('/user/get_current_user', methods=['POST'])
def get_current_user():
    data = request. get_json()
    check_student = Student.query.filter_by(student_number=data['args_student_number'].strip(), account_status=True).first()
    if not check_student:
        abort(409)
    response = {
        "args_student_firstname": check_student.student_firstname,
        "args_student_surname": check_student.student_surname,
        "args_student_department": check_student.student_department,
        "args_student_year": check_student.student_year,
        "args_student_section": check_student.student_section,
        "args_student_number": check_student.student_number,
        "args_student_email_address": check_student.student_email_address
    }
    return jsonify(response)

@app.route('/user/student/register', methods=['POST'])
def student_register():
    data = request.get_json()
    print(data)
    check_student = Student.query.filter_by(student_number=data['args_student_number']).first()
    if check_student:
        abort(409)
    if data['args_student_password'].strip() != data['args_student_password2'].strip():
        abort(417)
    new_student = Student(
        student_number=data['args_student_number'],
        student_section=data['args_student_section'],
        student_department=data['args_student_department'],
        student_year=data['args_student_year'],
        student_email_address=data['args_student_email_address'],
        student_firstname=data['args_student_firstname'],
        student_surname=data['args_student_surname'],
        student_password=data['args_student_password']
    )
    db.session.add(new_student)
    db.session.commit()
    return jsonify({"message": "success", "data": data})


@app.route('/user/student/login', methods=['POST'])
def student_login():
    data = request.get_json()
    print(data)
    check_student = Student.query.filter_by(student_number=data['args_student_number'].strip(),
                                            student_password=data['args_student_password'].strip()).first()
    if check_student is None:
        return jsonify({"error": "User not found"}), 404
    if check_student.account_status==False:
        return jsonify({"error": "User not verified, please wait at least 5-10 minutes then check your email for verification"}), 404
    session['logged_student_number'] = data['args_student_number']
    print(session)
    print('logged_student_number' in session)
    print(session.get('logged_student_number'))
    return jsonify(
        {
            "session": session.get('logged_student_number')
        }
            ), 218

@app.after_request
def after_request(response):
    session.permanent = True  # Ensure session is permanent
    return response

@app.route('/user/check/login', methods=['GET'])
def check_login():
    print(session)
    print('logged_student_number' in session)
    print(session.get('logged_student_number'))

    if not 'logged_student_number' in session:
        return jsonify({"error": "Not logged in"}), 409
    return jsonify({"message": "Logged in"}), 200

@app.route('/user/logout', methods=['POST'])
def logout():
    """if not 'logged_student_number' in session:
        return jsonify({"error": "not logged in"}), 405    
    """
    print(session)
    print('logged_student_number' in session)
    print(session.get('logged_student_number'))
    session.pop('logged_student_number', None)
    print(session)
    return jsonify({"message": "Logged out"}), 201



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0",port="5000",debug=True)
