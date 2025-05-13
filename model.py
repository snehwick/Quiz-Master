from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db=SQLAlchemy() #initialize db here

class User(db.Model, UserMixin):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(45),unique=True,nullable=False)
    email=db.Column(db.String(100),unique=True,nullable=False)
    password=db.Column(db.String(50),nullable=False)
    full_name=db.Column(db.String(100),nullable=False)
    qualification=db.Column(db.String(75))
    dob=db.Column(db.Date)
    role=db.Column(db.String(20),nullable=False)

    def is_admin(self):
        return self.role == 'admin'



class Subject(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    subject_name=db.Column(db.String(50),nullable=False)
    description=db.Column(db.Text)

class Chapter(db.Model):
    id= db.Column(db.Integer,primary_key=True)
    subject_id=db.Column(db.Integer,db.ForeignKey('subject.id'),nullable=False)
    name=db.Column(db.String(50),nullable=False)
    description= db.Column(db.Text)
    subject = db.relationship('Subject', backref=db.backref('chapters', lazy=True))

class Quiz(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100), nullable=False)
    chapter_id=db.Column(db.Integer,db.ForeignKey('chapter.id'),nullable=False)
    quiz_date=db.Column(db.DateTime,default=datetime.utcnow)
    time_duration=db.Column(db.String(5)) # HH:MM format
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    remarks=db.Column(db.Text)
    chapter=db.relationship('Chapter', backref=db.backref('quizzes',lazy=True))

    def is_available(self):
        # Convert current time to naive datetime for comparison
        now = datetime.now()  # Use local time instead of UTC
        # Make start_time and end_time naive by removing tzinfo
        start = self.start_time.replace(tzinfo=None)
        end = self.end_time.replace(tzinfo=None)
        return start <= now <= end
    



class Question(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    quiz_id=db.Column(db.Integer,db.ForeignKey('quiz.id'),nullable=False)
    quiz_question=db.Column(db.Text,nullable=False)
    option1=db.Column(db.String(200),nullable=False)
    option2=db.Column(db.String(200),nullable=False)
    option3=db.Column(db.String(200),nullable=False)
    option4=db.Column(db.String(200),nullable=False)
    correct_choice=db.Column(db.Integer,nullable=False)
    
    quiz = db.relationship('Quiz',backref=db.backref('questions',lazy=True))


class Score(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    quiz_id=db.Column(db.Integer,db.ForeignKey('quiz.id'),nullable=False)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    timestamp=db.Column(db.DateTime,default=datetime.utcnow)
    total_score=db.Column(db.Integer,nullable=False)

    user=db.relationship('User', backref=db.backref('scores',lazy=True))
    quiz=db.relationship('Quiz', backref=db.backref('scores',cascade='all, delete-orphan',lazy=True))

    



