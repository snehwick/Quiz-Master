from flask import Flask, render_template,redirect,url_for,request,flash
from model import db,User,Subject,Chapter,Quiz,Question,Score
from flask_login import LoginManager,login_user,logout_user,login_required,current_user
from datetime import datetime
from flask_migrate import Migrate
import matplotlib
matplotlib.use('Agg')  # Set the backend to non-interactive Agg
import matplotlib.pyplot as plt
import io
import base64
import re





app=Flask(__name__) #initializing the flask app
migrate = Migrate(app, db)


app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False # this will supress the warnings
app.config['SECRET_KEY']= 'snehal@123' #


db.init_app(app)


login_manager=LoginManager()
login_manager.init_app(app)
login_manager.login_view='login'





@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email=request.form['email']
        password=request.form['password']

        user= User.query.filter_by(email=email).first()

        if user and user.password == password:
            login_user(user)
            flash('Login Successfull','success')
            
            if user.is_admin():
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        
        else:
            flash('invalid email or password!','danger')
        
    return render_template('login.html')


@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        username=request.form['username']
        email=request.form['email']
        full_name=request.form['full_name']
        password=request.form['password']
        qualification=request.form['qualification']
        dob=request.form['dob']
        role=request.form['role']

        existing_user= User.query.filter_by(email=email).first()
        if existing_user:
            flash('Your email is already registered, kindly login','info')
            return redirect (url_for('login'))
        else:
            dob_date= datetime.strptime(dob,"%Y-%m-%d")
            new_user= User(username=username,email=email,password=password,full_name=full_name,qualification=qualification,dob=dob_date,role=role)
            db.session.add(new_user)
            db.session.commit()
            flash('you have been registered to our website successfully','success')
            return redirect(url_for('login'))
        
    return render_template('register.html')


@app.route('/user_dashboard',methods=['GET','POST'])
@login_required
def user_dashboard():
    if current_user.is_admin():
        flash('Admins cannot access the user dashboard')
        return redirect(url_for('admin_dashboard'))
    else:
        subjects= Subject.query.all()
        scores=Score.query.filter_by(user_id=current_user.id).all()
        return render_template('user_dashboard.html',User=current_user,subjects=subjects,scores=scores)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('you have been logged out!')
    return redirect(url_for('login'))


@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin():
        flash('you are not allowed to view this page','danger')
        return redirect(url_for('user_dashboard'))
    
    return render_template('admin_dashboard.html', admin=current_user)


@app.route('/admin_dashboard/subjects',methods=['GET','POST'])
@login_required
def manage_subjects():
    if not current_user.is_admin():
        flash('you are not allowed to visit this route','danger')
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        subject_name= request.form['subject_name']
        description= request.form['description']

        new_subject=Subject(subject_name=subject_name,description=description)
        db.session.add(new_subject)
        db.session.commit()

        flash('Subject added to the database','success')
        return redirect(url_for('manage_subjects'))
    
    subjects= Subject.query.all()
    return render_template('manage_subjects.html',subjects=subjects)


@app.route('/admin_dashboard/subjects/delete <int:subject_id>')
@login_required
def delete_subject(subject_id):
    if not current_user.is_admin():
        flash('You are not allowed to access this page','danger')
        return redirect(url_for('student_dashboard'))
    
    else:
        subject = Subject.query.get(subject_id)
        if subject:
            # First delete all scores related to quizzes in this subject's chapters
            for chapter in subject.chapters:
                for quiz in chapter.quizzes:
                    Score.query.filter_by(quiz_id=quiz.id).delete()
                    Question.query.filter_by(quiz_id=quiz.id).delete()
                    db.session.delete(quiz)
            
            # Then delete all chapters
            Chapter.query.filter_by(subject_id=subject.id).delete()
            
            # Finally delete the subject
            db.session.delete(subject)
            db.session.commit()
            flash('Subject and all related data deleted successfully','success')
            
        return redirect(url_for('manage_subjects'))


@app.route('/admin_dashboard/subjects/edit/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def edit_subject(subject_id):
    if not current_user.is_admin():
        flash("You are not authorized to access this page", 'danger')
        return redirect(url_for('user_dashboard'))
    
    subject = Subject.query.get_or_404(subject_id)
    
    if request.method == 'POST':
        subject.subject_name = request.form['subject_name']
        subject.description = request.form['description']
        
        try:
            db.session.commit()
            flash('Subject updated successfully', 'success')
            return redirect(url_for('manage_subjects'))
        except:
            db.session.rollback()
            flash('Error updating subject', 'danger')
            
    return render_template('edit_subject.html', subject=subject)


@app.route('/admin_dashboard/chapters', methods=['GET','POST'])
@login_required
def manage_chapters():
    if not current_user.is_admin():
        flash('You are not allowed to access this page','danger')
        return redirect(url_for('student_dashboard'))
    
    else:
        subjects= Subject.query.all()

        if request.method=='POST':
            name=request.form['name']
            description=request.form['description']
            subject_id=request.form['subject_id']

            new_chapter=Chapter(name=name,description=description,subject_id=subject_id)
            db.session.add(new_chapter)
            db.session.commit()


            flash('Chapter Added','success')
            return redirect(url_for('manage_chapters'))
        
        chapters=Chapter.query.all()
        return render_template('manage_chapters.html',chapters=chapters, subjects=subjects)


@app.route('/admin_dashboard/chapters/edit<int:chapter_id>',methods=['GET','POST'])
@login_required
def edit_chapter(chapter_id):
    if not current_user.is_admin():
        flash("You are not allowed to crawl on this route")
        return redirect(url_for('user_dashboard'))
    else:
        chapter= Chapter.query.get_or_404(chapter_id)
        subjects= Subject.query.all()

        if request.method=='POST':
            chapter.name=request.form['name']
            chapter.description=request.form['description']
            chapter.subject_id=request.form['subject_id']

            db.session.commit()
            flash('chapter updated')
            return redirect(url_for('manage_chapters'))
        
        return render_template('edit_chapter.html',chapter=chapter,subjects=subjects)

    
@app.route('/admin_dashboard/chapters/delete<int:chapter_id>',methods=['GET','POST'])
@login_required
def delete_chapter(chapter_id):
    if not current_user.is_admin():
        flash("Unauthorized action!", "danger")
        return redirect(url_for('user_dashboard'))
    else:
        chapter= Chapter.query.get(chapter_id)
        if chapter:
            for quiz in chapter.quizzes:
                Score.query.filter_by(quiz_id=quiz.id).delete()
                Question.query.filter_by(quiz_id=quiz.id).delete()
                db.session.delete(quiz)

            
            db.session.delete(chapter)
            db.session.commit()

            flash('chapter deleted')
        
        return redirect(url_for('manage_chapters'))
           
    
@app.route('/admin_dashboard/quizzes', methods=['GET', 'POST'])
@login_required
def manage_quizzes():
    if not current_user.is_admin():
        flash("You are not authorized to visit this route", 'danger')
        return redirect(url_for('user_dashboard'))
    
    chapters = Chapter.query.all()
    
    if request.method == 'POST':
        try:
            name = request.form['name']
            quiz_date = datetime.strptime(request.form['quiz_date'], "%Y-%m-%d")
            time_duration = request.form['time_duration']
            
            # Validate time_duration format
            if not re.match(r'^[0-9]{2}:[0-9]{2}$', time_duration):
                flash('Invalid time duration format. Please use HH:MM format.', 'danger')
                return redirect(url_for('manage_quizzes'))
                
            remarks = request.form['remarks']
            chapter_id = request.form['chapter_id']
            start_time = datetime.strptime(request.form['start_time'], "%Y-%m-%dT%H:%M")
            end_time = datetime.strptime(request.form['end_time'], "%Y-%m-%dT%H:%M")

            if start_time >= end_time:
                flash('End time must be after start time', 'danger')
                return redirect(url_for('manage_quizzes'))
            
            new_quiz = Quiz(
                name=name,
                quiz_date=quiz_date,
                time_duration=time_duration,
                remarks=remarks,
                chapter_id=chapter_id,
                start_time=start_time,
                end_time=end_time
            )
            db.session.add(new_quiz)
            db.session.commit()

            flash('New Quiz Created', 'success')
            return redirect(url_for('manage_quizzes'))
        except Exception as e:
            flash(f'Error creating quiz: {str(e)}', 'danger')
            return redirect(url_for('manage_quizzes'))
    
    quizzes = Quiz.query.all()
    return render_template('manage_quizzes.html', quizzes=quizzes, chapters=chapters)
    

@app.route('/admin_dashboard/quizzes/delete/<int:quiz_id>',methods=['GET','POST'])
@login_required
def delete_quiz(quiz_id):
    if not current_user.is_admin():
        flash('You cant crawl on this route','danger')
        return redirect(url_for('user_dashboard'))
    
    else:
        quiz=Quiz.query.get(quiz_id)
        if quiz:
            # First delete all scores related to this quiz
            Score.query.filter_by(quiz_id=quiz.id).delete()
            
            # Then delete all questions
            Question.query.filter_by(quiz_id=quiz.id).delete()

            # Finally delete the quiz
            db.session.delete(quiz)
            db.session.commit()

            flash('Quiz Deleted','success')
        
        return redirect(url_for('manage_quizzes'))


@app.route('/admin_dashboard/quizzes/edit/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def edit_quiz(quiz_id):
    if not current_user.is_admin():
        flash("You are not authorized to access this page", 'danger')
        return redirect(url_for('user_dashboard'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    chapters = Chapter.query.all()
    
    if request.method == 'POST':
        try:
            quiz.name = request.form['name']
            quiz.quiz_date = datetime.strptime(request.form['quiz_date'], "%Y-%m-%d")
            quiz.time_duration = request.form['time_duration']
            quiz.remarks = request.form['remarks']
            quiz.chapter_id = request.form['chapter_id']
            quiz.start_time = datetime.strptime(request.form['start_time'], "%Y-%m-%dT%H:%M")
            quiz.end_time = datetime.strptime(request.form['end_time'], "%Y-%m-%dT%H:%M")

            if quiz.start_time >= quiz.end_time:
                flash('End time must be after start time', 'danger')
                return render_template('edit_quiz.html', quiz=quiz, chapters=chapters)
            
            db.session.commit()
            flash('Quiz updated successfully', 'success')
            return redirect(url_for('manage_quizzes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating quiz: {str(e)}', 'danger')
            
    return render_template('edit_quiz.html', quiz=quiz, chapters=chapters)


@app.route('/admin_dashboard/questions/<int:quiz_id>',methods=['GET','POST'])
@login_required
def manage_questions(quiz_id):
    if not current_user.is_admin():
        flash("You are not authorized to visit this route",'danger')
        return redirect(url_for('user_dashboard'))
    
    else:
        quiz=Quiz.query.get_or_404(quiz_id)

        if request.method=='POST':
            quiz_question= request.form['quiz_question']
            option1=request.form['option1']
            option2=request.form['option2']
            option3=request.form['option3']
            option4=request.form['option4']
            correct_choice=request.form['correct_choice']

            new_question=Question(quiz_id=quiz_id,quiz_question=quiz_question,option1=option1,option2=option2,option3=option3,option4=option4,correct_choice=correct_choice)

            db.session.add(new_question)
            db.session.commit()

            flash('question added','success')
            return redirect(url_for('manage_questions',quiz_id=quiz_id))
        
        questions=Question.query.filter_by(quiz_id=quiz_id).all()
        return render_template('manage_questions.html',quiz=quiz,questions=questions)
    
    
@app.route('/admin_dashboard/questions/delete<int:question_id>/<int:quiz_id>',methods=['GET','POST'])
@login_required
def delete_question(question_id,quiz_id):
    if not current_user.is_admin():
        flash("You are not authorized to visit this route",'danger')
        return redirect(url_for('user_dashboard'))
    
    else:
        question=Question.query.get_or_404(question_id)
        if question:
            db.session.delete(question)
            db.session.commit()
            
            flash('Question Deleted','success')
            
        return redirect (url_for('manage_questions',quiz_id=quiz_id))

@app.route('/admin_dashboard/questions/edit/<int:question_id>/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def edit_question(question_id, quiz_id):
    if not current_user.is_admin():
        flash("You are not authorized to access this page", 'danger')
        return redirect(url_for('user_dashboard'))
    
    question = Question.query.get_or_404(question_id)
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if request.method == 'POST':
        try:
            question.quiz_question = request.form['quiz_question']
            question.option1 = request.form['option1']
            question.option2 = request.form['option2']
            question.option3 = request.form['option3']
            question.option4 = request.form['option4']
            question.correct_choice = int(request.form['correct_choice'])
            
            db.session.commit()
            flash('Question updated successfully', 'success')
            return redirect(url_for('manage_questions', quiz_id=quiz_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating question: {str(e)}', 'danger')
            
    return render_template('edit_question.html', question=question, quiz=quiz)
            
@app.route('/subject/<int:subject_id>')
@login_required
def view_chapters(subject_id):
    subject=Subject.query.get_or_404(subject_id)
    chapters= Chapter.query.filter_by(subject_id=subject_id).all()
    return render_template('view_chapters.html',subject=subject,chapters=chapters)


@app.route('/chapter/<int:chapter_id>')
@login_required
def view_quizzes(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
    return render_template('view_quizzes.html', 
                         chapter=chapter, 
                         quizzes=quizzes,
                         datetime=datetime)


@app.route('/quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def take_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if quiz is available
    if not quiz.is_available():
        flash('This quiz is not available at this time.', 'danger')
        return redirect(url_for('view_quizzes', chapter_id=quiz.chapter_id))
    
    # Check if user has already attempted this quiz
    existing_attempt = Score.query.filter_by(
        quiz_id=quiz_id,
        user_id=current_user.id
    ).first()
    
    if existing_attempt:
        flash('You have already attempted this quiz.', 'warning')
        return redirect(url_for('view_quizzes', chapter_id=quiz.chapter_id))

    questions = Question.query.filter_by(quiz_id=quiz_id).all()

    if request.method == 'POST':
        score = 0
        for question in questions:
            selected_option = request.form.get(f'question_{question.id}')
            if selected_option and int(selected_option) == question.correct_choice:
                score += 1

        new_score = Score(quiz_id=quiz_id, user_id=current_user.id, total_score=score)
        db.session.add(new_score)
        db.session.commit()

        flash(f'Quiz submitted! You scored {score}/{len(questions)}!', 'info')
        return redirect(url_for('user_dashboard'))
    
    return render_template('take_quiz.html', quiz=quiz, questions=questions)


@app.route('/leaderboard')
@login_required
def leaderboard():
    try:
        # Get top scores only from quizzes with valid subjects and chapters
        top_scores = (
            Score.query
            .join(Quiz, Score.quiz_id == Quiz.id)
            .join(Chapter, Quiz.chapter_id == Chapter.id)
            .join(Subject, Chapter.subject_id == Subject.id)
            .join(User, Score.user_id == User.id)
            .order_by(Score.total_score.desc())
            .limit(10)
            .all()
        )
        
        # Check if we found any scores
        if not top_scores:
            flash('No quiz scores available for the leaderboard yet!', 'info')
            
        return render_template('leaderboard.html', top_scores=top_scores)
    except Exception as e:
        flash(f'Error loading leaderboard: {str(e)}', 'danger')
        return redirect(url_for('user_dashboard'))


        
@app.route('/summary')
@login_required
def summary():
    if current_user.is_admin():
        flash('Admins cannot view personal summaries')
        return redirect(url_for('admin_dashboard'))
    
    try:
        # Get user's scores grouped by subject
        subject_scores = (
            db.session.query(
                Subject.subject_name,
                db.func.count(Score.id).label('attempts'),
                db.func.avg(Score.total_score).label('average_score')
            )
            .join(Chapter, Subject.id == Chapter.subject_id)
            .join(Quiz, Chapter.id == Quiz.chapter_id)
            .join(Score, Quiz.id == Score.quiz_id)
            .filter(Score.user_id == current_user.id)
            .group_by(Subject.subject_name)
            .all()
        )

        if not subject_scores:
            flash('No quiz attempts found. Take some quizzes to see your summary!', 'info')
            return redirect(url_for('user_dashboard'))

        # Prepare data for plotting
        subjects = [score[0] for score in subject_scores]
        attempts = [score[1] for score in subject_scores]
        averages = [round(float(score[2]), 2) for score in subject_scores]

        # Create bar chart
        plt.figure(figsize=(10, 5))
        plt.bar(subjects, averages, color='#005153')
        plt.title('Average Scores by Subject')
        plt.xlabel('Subjects')
        plt.ylabel('Average Score')
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save bar chart to bytes
        bar_bytes = io.BytesIO()
        plt.savefig(bar_bytes, format='png', bbox_inches='tight', transparent=True)
        bar_bytes.seek(0)
        bar_graph = base64.b64encode(bar_bytes.getvalue()).decode()
        plt.close()     

        # Create pie chart for attempts distribution
        plt.figure(figsize=(8, 8))
        colors = ['#005153', '#42A1A3', '#2D8C8E', '#006B6D', '#003F41']
        plt.pie(attempts, labels=subjects, autopct='%1.1f%%', colors=colors)
        plt.title('Quiz Attempts Distribution')
        plt.tight_layout()

        # Save pie chart to bytes
        pie_bytes = io.BytesIO()
        plt.savefig(pie_bytes, format='png', bbox_inches='tight', transparent=True)
        pie_bytes.seek(0)
        pie_graph = base64.b64encode(pie_bytes.getvalue()).decode()
        plt.close()

        return render_template(
            'summary.html',
            bar_graph=bar_graph,
            pie_graph=pie_graph,
            subject_scores=subject_scores
        )

    except Exception as e:
        flash(f'Error generating summary: {str(e)}', 'danger')
        return redirect(url_for('user_dashboard'))



    if not current_user.is_admin():
        flash('You are not authorized to view this page', 'danger')
        return redirect(url_for('user_dashboard'))
    
    try:
        # Get top performers for each subject
        subject_data = (
            db.session.query(
                Subject.subject_name,
                db.func.count(Score.id).label('total_attempts'),
                db.func.avg(Score.total_score).label('average_score'),
                User.username,
                db.func.max(Score.total_score).label('highest_score')
            )
            .join(Chapter, Subject.id == Chapter.subject_id)
            .join(Quiz, Chapter.id == Quiz.chapter_id)
            .join(Score, Quiz.id == Score.quiz_id)
            .join(User, Score.user_id == User.id)
            .group_by(Subject.subject_name)
            .all()
        )

        if not subject_data:
            flash('No quiz data available yet!', 'info')
            return redirect(url_for('admin_dashboard'))

        # Prepare data for plotting
        subjects = [data[0] for data in subject_data]
        avg_scores = [round(float(data[2]), 2) for data in subject_data]
        attempts = [data[1] for data in subject_data]

        # Create bar chart for average scores
        plt.figure(figsize=(10, 5))
        plt.bar(subjects, avg_scores, color='#005153')
        plt.title('Average Scores by Subject')
        plt.xlabel('Subjects')
        plt.ylabel('Average Score')
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save bar chart to bytes
        bar_bytes = io.BytesIO()
        plt.savefig(bar_bytes, format='png', bbox_inches='tight', transparent=True)
        bar_bytes.seek(0)
        bar_graph = base64.b64encode(bar_bytes.getvalue()).decode()
        plt.close()

        # Create pie chart for attempts distribution
        plt.figure(figsize=(8, 8))
        colors = ['#005153', '#42A1A3', '#2D8C8E', '#006B6D', '#003F41']
        plt.pie(attempts, labels=subjects, autopct='%1.1f%%', colors=colors)
        plt.title('Quiz Attempts Distribution')
        plt.tight_layout()

        # Save pie chart to bytes
        pie_bytes = io.BytesIO()
        plt.savefig(pie_bytes, format='png', bbox_inches='tight', transparent=True)
        pie_bytes.seek(0)
        pie_graph = base64.b64encode(pie_bytes.getvalue()).decode()
        plt.close()

        # Get top performers for each subject
        top_performers = {}
        for subject in subjects:
            top_performers[subject] = (
                db.session.query(
                    User.username,
                    Score.total_score,
                    Quiz.name.label('quiz_name')
                )
                .join(Quiz, Score.quiz_id == Quiz.id)
                .join(Chapter, Quiz.chapter_id == Chapter.id)
                .join(Subject, Chapter.subject_id == Subject.id)
                .join(User, Score.user_id == User.id)
                .filter(Subject.subject_name == subject)
                .order_by(Score.total_score.desc())
                .limit(3)
                .all()
            )

        return render_template(
            'admin_summary.html',
            bar_graph=bar_graph,
            pie_graph=pie_graph,
            subject_data=subject_data,
            top_performers=top_performers
        )

    except Exception as e:
        flash(f'Error generating summary: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))


@app.route('/admin/summary')
@login_required
def admin_summary():
    if not current_user.is_admin():
        flash('You are not authorized to view this page', 'danger')
        return redirect(url_for('user_dashboard'))
    
    try:
        # Get top performers for each subject
        subject_data = (
            db.session.query(
                Subject.subject_name,
                db.func.count(Score.id).label('total_attempts'),
                db.func.avg(Score.total_score).label('average_score'),
                db.func.max(Score.total_score).label('highest_score'),
                User.username.label('top_scorer')
            )
            .join(Chapter, Subject.id == Chapter.subject_id)
            .join(Quiz, Chapter.id == Quiz.chapter_id)
            .join(Score, Quiz.id == Score.quiz_id)
            .join(User, Score.user_id == User.id)
            .group_by(Subject.subject_name)
            .all()
        )

        if not subject_data:
            flash('No quiz data available yet!', 'info')
            return redirect(url_for('admin_dashboard'))

        # Prepare data for plotting
        subjects = [data[0] for data in subject_data]
        attempts = [data[1] for data in subject_data]
        top_scores = [data[3] for data in subject_data]
        top_scorers = [data[4] for data in subject_data]

        # Create bar chart for top scores
        plt.figure(figsize=(10, 5))
        bars = plt.bar(subjects, top_scores, color='#005153')
        
        plt.xlabel('Subjects')
        plt.ylabel('Highest Score')
        plt.xticks(rotation=45)

        # Add value labels on top of each bar
        for i, bar in enumerate(bars):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'({top_scorers[i]})',
                    ha='center', va='bottom')

        plt.tight_layout()

        # Save bar chart to bytes
        bar_bytes = io.BytesIO()
        plt.savefig(bar_bytes, format='png', bbox_inches='tight', transparent=True)
        bar_bytes.seek(0)
        bar_graph = base64.b64encode(bar_bytes.getvalue()).decode()
        plt.close()

        # Create pie chart for attempts distribution
        plt.figure(figsize=(8, 8))
        colors = ['#005153', '#42A1A3', '#2D8C8E', '#006B6D', '#003F41']
        plt.pie(attempts, labels=subjects, autopct='%1.1f%%', colors=colors)
        plt.title('Quiz Attempts Distribution')
        plt.tight_layout()

        # Save pie chart to bytes
        pie_bytes = io.BytesIO()
        plt.savefig(pie_bytes, format='png', bbox_inches='tight', transparent=True)
        pie_bytes.seek(0)
        pie_graph = base64.b64encode(pie_bytes.getvalue()).decode()
        plt.close()

        # Get top performers for each subject
        top_performers = {}
        for subject in subjects:
            top_performers[subject] = (
                db.session.query(
                    User.username,
                    Score.total_score,
                    Quiz.name.label('quiz_name')
                )
                .join(Quiz, Score.quiz_id == Quiz.id)
                .join(Chapter, Quiz.chapter_id == Chapter.id)
                .join(Subject, Chapter.subject_id == Subject.id)
                .join(User, Score.user_id == User.id)
                .filter(Subject.subject_name == subject)
                .order_by(Score.total_score.desc())
                .limit(3)
                .all()
            )

        return render_template(
            'admin_summary.html',
            bar_graph=bar_graph,
            pie_graph=pie_graph,
            subject_data=subject_data,
            top_performers=top_performers
        )

    except Exception as e:
        flash(f'Error generating summary: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))


@app.route('/admin/search')
@login_required
def admin_search():
    if not current_user.is_admin():
        flash('You are not authorized to access this page', 'danger')
        return redirect(url_for('user_dashboard'))
    
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')
    
    if not query:
        return render_template('admin_search.html', results=None)
    
    results = {
        'users': [],
        'subjects': [],
        'quizzes': [],
        'questions': []
    }
    
    if search_type in ['all', 'users']:
        users = User.query.filter(
            db.or_(
                User.username.ilike(f'%{query}%'),
                User.email.ilike(f'%{query}%'),
                User.full_name.ilike(f'%{query}%')
            )
        ).all()
        results['users'] = users
    
    if search_type in ['all', 'subjects']:
        subjects = Subject.query.filter(
            db.or_(
                Subject.subject_name.ilike(f'%{query}%'),
                Subject.description.ilike(f'%{query}%')
            )
        ).all()
        results['subjects'] = subjects
    
    if search_type in ['all', 'quizzes']:
        quizzes = Quiz.query.filter(
            db.or_(
                Quiz.name.ilike(f'%{query}%'),
                Quiz.remarks.ilike(f'%{query}%')
            )
        ).all()
        results['quizzes'] = quizzes
    
    if search_type in ['all', 'questions']:
        questions = Question.query.filter(
            Question.quiz_question.ilike(f'%{query}%')
        ).all()
        results['questions'] = questions
    
    return render_template('admin_search.html', results=results, query=query, search_type=search_type)

@app.route('/search')
@login_required
def user_search():
    if current_user.is_admin():
        return redirect(url_for('admin_search'))
    
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')
    
    if not query:
        return render_template('user_search.html', results=None)
    
    results = {
        'subjects': [],
        'quizzes': []
    }
    
    if search_type in ['all', 'subjects']:
        subjects = Subject.query.filter(
            db.or_(
                Subject.subject_name.ilike(f'%{query}%'),
                Subject.description.ilike(f'%{query}%')
            )
        ).all()
        results['subjects'] = subjects
    
    if search_type in ['all', 'quizzes']:
        quizzes = (Quiz.query
            .join(Chapter)
            .filter(
                db.or_(
                    Quiz.name.ilike(f'%{query}%'),
                    Quiz.remarks.ilike(f'%{query}%')
                )
            )
            .all())
        results['quizzes'] = quizzes
    
    return render_template('user_search.html', results=results, query=query, search_type=search_type)


with app.app_context():
    db.create_all()

    # new_sub= Subject(id=1,subject_name='maths',description='maths quiz is here')
    # db.session.add(new_sub)
    # db.session.commit()



if __name__=='__main__':
    app.run(debug=True)

