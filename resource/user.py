from flask_restful import Resource, abort, fields, marshal_with, reqparse
from flask import request, jsonify, session
from models.database import db, Equipment, Student, Pending, Borrowed, Completed
import random
import string
import datetime

class ShowEquipments(Resource):
    def get(self):
        search_query = request.args.get('search', '').lower()
        if not search_query:
            equipment = Equipment.query.filter_by(is_available=1).order_by(Equipment.equip_type.asc()).all()
        else:
            # Adjust this query to match your database structure and search requirements
            equipment = Equipment.query.filter_by(is_available=1).filter(
                (Equipment.equip_id.ilike(f'%{search_query}%')) | 
                (Equipment.equip_type.ilike(f'%{search_query}%')) | 
                (Equipment.equip_unique_key.ilike(f'%{search_query}%'))
            ).order_by(Equipment.equip_type.asc()).all()
        equip_id = [e.equip_id for e in equipment]
        equip_type = [e.equip_type for e in equipment]
        equip_unique_key = [e.equip_unique_key for e in equipment]
        is_available = [e.is_available for e in equipment]
        is_pending = [e.is_pending for e in equipment]

        equipments = {
            "equip_id": equip_id,
            "equip_type": equip_type,
            "equip_unique_key": equip_unique_key,
            "is_available": is_available,
            "is_pending": is_pending,
        }    
        
        return equipments
    
    @staticmethod
    def generate_unique_id(length):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choices(characters, k=length))


equipment_resource_fields = {
    'equip_id' : fields.Integer,
    'equip_type': fields.String,
    'equip_unique_key': fields.String,
    'is_available': fields.Boolean,
    'is_pending': fields.Boolean
}

class Equipments(Resource):
    @marshal_with(equipment_resource_fields)
    def get(self, unique_key):
        equipment = Equipment.query.filter_by(equip_unique_key=unique_key).first()
        if not equipment:
            abort(409, message="Not Found")
        
        return equipment
    
    


post_args_student = reqparse.RequestParser()
post_args_student.add_argument("args_student_number", type=str, required=True, help="student number is required")
post_args_student.add_argument("args_student_department", type=str, required=True, help="student department is required")
post_args_student.add_argument("args_student_year", type=str, required=True, help="student year is required")
post_args_student.add_argument("args_student_section", type=str, required=True, help="student section is required")
post_args_student.add_argument("args_student_email_address", type=str, required=True, help="student email address is required")
post_args_student.add_argument("args_student_firstname", type=str, required=True, help="student firstname is required")
post_args_student.add_argument("args_student_surname", type=str, required=True, help="student surname is required")
post_args_student.add_argument("args_requested_item", type=str, required=True, help="equipment unique key is required")
post_args_student.add_argument("args_requested_end_date", type=lambda x: datetime.datetime.strptime(x, '%Y-%m-%d').date(), required=True, help="return end date is required")

student_resource_fields = {
    'student_number':  fields.String,
    'student_department': fields.String,
    'student_year': fields.String,
    'student_section':  fields.String,
    'student_email_address': fields.String,
    'student_firstname': fields.String,
    'student_surname': fields.String,
    'requested_item': fields.String,
    'args_requested_end_date': fields.String
}

class EachStudent(Resource):
    @marshal_with(student_resource_fields)
    def get(self, student_number):
        if 'admin_login' not in session:
            abort(401, message="Unauthorized")
        student = Student.query.filter_by(student_number=student_number).first()
        if not student:
            abort(409, message="Not Found")
        return student

class Students(Resource):
    @marshal_with(student_resource_fields)
    def post(self):
        args = post_args_student.parse_args()

        # Get the current date
        current_date = datetime.datetime.now().date()

        # Check if the requested end date is in the past
        if args['args_requested_end_date'] < current_date:
            return jsonify({"error": "Requested end date cannot be in the past"}), 400

        student_obj = Student.query.filter_by(student_number=args['args_student_number']).first()
        equip_obj = Equipment.query.filter_by(equip_unique_key=args['args_requested_item']).first()
        if equip_obj.is_available:
            pending_obj = Pending(
                equip_type=equip_obj.equip_type,
                equip_unique_key=equip_obj.equip_unique_key,
                student_number=student_obj.student_number,
                student_name=f"{student_obj.student_surname}, {student_obj.student_firstname}",
                is_verified=0,
                requested_end_date=args['args_requested_end_date']
            )
            student_obj.requested_item=args['args_requested_item']
            student_obj.status='requested'
            db.session.add(pending_obj)
            db.session.commit()
            print('Student added Successfully')
            return student_obj, 201
        else:       
            return {"message": "item not available"}, 418
        

class PendingItems(Resource):
    def get(self):
        pending = Pending.query.order_by(Pending.pending_id.desc()).all()
        pending_items = [{
                "pending_id": p.pending_id,
                "equip_type": p.equip_type,
                "equip_unique_key": p.equip_unique_key,
                "student_number": p.student_number,
                "student_name": p.student_name,
                "is_verified": p.is_verified,
                "requested_end_date": p.requested_end_date.isoformat()  # Convert date to string
            } for p in pending]

        return pending_items
    
class BorrowedItems(Resource):
    def get(self):
        join_condition = Borrowed.pending_id == Pending.pending_id

        # Perform the join
        joined_query = Borrowed.query.join(Pending, join_condition)

        # Specify the columns you want in the final result
        result = joined_query.with_entities(Borrowed, Pending.requested_end_date).order_by(Borrowed.borrow_id.desc()).all()

        borrowed_items = [
            {
            "borrow_id": i.borrow_id,
            "is_claimed": i.is_claimed,
            "is_returned": i.is_returned,
            "penalty": i.penalty,
            "pending_id": i.pending_id,
            "requested_end_date": x.isoformat()            
            }
         for i, x in result]


        return borrowed_items
    

class CompletedItems(Resource):
    def get(self):
        completed = Completed.query.order_by(Completed.completed_id.desc()).all()
        if 'admin_login' in session:
            completed_id = [c.completed_id for c in completed]
            student_number = [c.student_number for c in completed]
            student_department = [c.student_department for c in completed]
            student_name = [c.student_name for c in completed]
            equip_type = [c.equip_type for c in completed]
            equip_unique_key = [c.equip_unique_key for c in completed]

            completed_items = {
                "completed_id": completed_id,
                "student_number": student_number,
                "student_department": student_department,
                "student_name": student_name,
                "equip_type": equip_type,
                "equip_unique_key": equip_unique_key
            }

            return completed_items
        
        completed_id = [c.completed_id for c in completed]
        student_department = [c.student_department for c in completed]
        equip_type = [c.equip_type for c in completed]
        equip_unique_key = [c.equip_unique_key for c in completed]    

        completed_items = {
            "completed_id": completed_id,
            "student_department": student_department,
            "equip_type": equip_type,
            "equip_unique_key": equip_unique_key
        }
    
        return completed_items