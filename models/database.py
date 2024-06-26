from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
import datetime
db = SQLAlchemy()

class Equipment(db.Model): 
    __tablename__ = 'equipment'
    equip_id = db.Column(db.Integer, primary_key=True)
    equip_type = db.Column(db.String(50), nullable=False)
    equip_unique_key = db.Column(db.String(50), nullable=False, unique=True)
    is_available = db.Column(db.Boolean, default=True)
    is_pending = db.Column(db.Boolean, default=False)


class Pending(db.Model):
    __tablename__ = 'pending'
    pending_id = db.Column(db.Integer, primary_key=True)
    equip_type = db.Column(db.String(50))
    equip_unique_key = db.Column(db.String(50), nullable=False)
    student_number = db.Column(db.String(20), unique=True, nullable=False)
    student_name = db.Column(db.String(50), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    requested_end_date = db.Column(db.Date)


class Borrowed(db.Model):
    __tablename__ = 'borrowed'
    borrow_id = db.Column(db.Integer, primary_key=True)
    is_claimed = db.Column(db.Boolean, default=False)
    is_returned = db.Column(db.Boolean, default=False)
    penalty = db.Column(db.Boolean, default=False)
    pending_id = db.Column(db.Integer, db.ForeignKey('pending.pending_id'), nullable=False)
    
    @classmethod
    def violator_checker(cls):
        all_items = cls.query.all()
        current_date = datetime.datetime.now().date()
        for i in all_items:
            current_pending = Pending.query.filter_by(pending_id=i.pending_id).first()
            check_current = Violators.query.filter_by(borrow_id=i.borrow_id).first()
            if check_current:
                continue
            if current_pending.requested_end_date < current_date:
                i.penalty = 1
                new_violator = Violators(
                                        borrow_id=i.borrow_id,
                                        student_number=current_pending.student_number,
                                        equip_unique_key=current_pending.equip_unique_key
                                        )
                db.session.add(new_violator)
                db.session.commit()
            pass


class Violators(db.Model):
    __tablename__ = 'violators'
    violator_id = db.Column(db.Integer, primary_key=True)
    borrow_id = db.Column(db.Integer)
    student_number = db.Column(db.String(50))
    equip_unique_key = db.Column(db.String(50))

class Student(db.Model):
    __tablename__ = 'student'
    student_id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String(20), unique=True, nullable=False)
    student_section = db.Column(db.String(10))
    student_department = db.Column(db.String(45), nullable=False)
    student_year = db.Column(db.String(10), nullable=False)
    student_email_address = db.Column(db.String(45), nullable=False)
    student_firstname = db.Column(db.String(50), nullable=False)
    student_surname = db.Column(db.String(50), nullable=False)
    requested_item=db.Column(db.String(50), nullable=True)
    student_password=db.Column(db.String(255), nullable=False)
    status=db.Column(db.String(15))
    account_status=db.Column(db.Boolean, default=False)
    

class Admin(db.Model):
    __tablename__ = 'admin'
    admin_id = db.Column(db.Integer, primary_key=True)
    admin_username = db.Column(db.String(50), nullable=False, unique=True)
    admin_password = db.Column(db.String(255), nullable=False)
    admin_email_address = db.Column(db.String(45), nullable=False)
    admin_firstname = db.Column(db.String(45), nullable=False)
    admin_surname = db.Column(db.String(45), nullable=False)

    def save(self):
        self.admin_password=generate_password_hash(self.admin_password)
        db.session.add(self)
        db.session.commit()

    @classmethod
    def check_login(cls, username, password):
        admin_obj = cls.query.filter_by(admin_username=username).first()
        return admin_obj and check_password_hash((admin_obj.admin_password), str(password))
    

class Completed(db.Model):
    __tablename__ = 'completed'
    completed_id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String(20), nullable=False)
    student_department = db.Column(db.String(45), nullable=False)
    student_name = db.Column(db.String(100), nullable=False)
    equip_type = db.Column(db.String(50), nullable=False)
    equip_unique_key = db.Column(db.String(50), nullable=False)
