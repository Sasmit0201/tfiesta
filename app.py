from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURATION ---
app.config['SECRET_KEY'] = 'hackathon-secret-key-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    github_url = db.Column(db.String(200), nullable=True)
    projects = db.Column(db.Text, nullable=True)  # JSON string or comma-separated
    digilocker_id = db.Column(db.String(100), nullable=True)
    skills = db.Column(db.String(200), nullable=True)
    soft_skills_score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    applications = db.relationship('Application', backref='student', lazy=True)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    skills = db.Column(db.String(200), nullable=False)
    applications = db.relationship('Application', backref='job', lazy=True)
    ratings = db.relationship('CompanyRating', backref='company_job', lazy=True)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=True)
    status = db.Column(db.String(20), default='Pending') 
    feedback = db.Column(db.Text, nullable=True)  # Stores rejection reason (mandatory for rejection)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    auto_rejected = db.Column(db.Boolean, default=False)  # True if auto-rejected due to skills
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CompanyRating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    feedback = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SoftSkillsTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(300), nullable=False)
    option_b = db.Column(db.String(300), nullable=False)
    option_c = db.Column(db.String(300), nullable=False)
    option_d = db.Column(db.String(300), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)  # 'A', 'B', 'C', or 'D'
    explanation = db.Column(db.Text, nullable=True)

class TestResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=True)
    test_id = db.Column(db.Integer, db.ForeignKey('soft_skills_test.id'), nullable=False)
    answer = db.Column(db.String(1), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Auto-create DB tables
with app.app_context():
    db.create_all()
    # Initialize soft skills test questions if not exists
    if SoftSkillsTest.query.count() == 0:
        questions = [
            SoftSkillsTest(
                question="During a team meeting, a colleague strongly disagrees with your proposal. How do you respond?",
                option_a="Defend your idea aggressively and refuse to compromise",
                option_b="Listen to their concerns, ask clarifying questions, and find common ground",
                option_c="Ignore their input and proceed with your original plan",
                option_d="Complain to your manager about the colleague",
                correct_answer="B",
                explanation="Effective communication and collaboration require active listening and seeking win-win solutions."
            ),
            SoftSkillsTest(
                question="You have a tight deadline, but a teammate asks for help with their urgent task. What do you do?",
                option_a="Refuse immediately, explaining you're too busy",
                option_b="Assess both priorities, offer partial assistance or suggest alternatives",
                option_c="Drop your work completely and help them",
                option_d="Ignore their request",
                correct_answer="B",
                explanation="Balancing your commitments while being a supportive team member shows good prioritization skills."
            ),
            SoftSkillsTest(
                question="Your manager gives you negative feedback about your recent work. Your response?",
                option_a="Get defensive and make excuses",
                option_b="Listen carefully, ask for specific examples, and create an action plan to improve",
                option_c="Avoid the manager afterward",
                option_d="Blame your teammates",
                correct_answer="B",
                explanation="Receiving feedback constructively and taking action demonstrates growth mindset and professionalism."
            ),
            SoftSkillsTest(
                question="You notice a critical error in a project just before the deadline. What's your approach?",
                option_a="Hide it and hope no one notices",
                option_b="Immediately inform your team, assess impact, and propose solutions",
                option_c="Blame someone else",
                option_d="Wait until after the deadline to mention it",
                correct_answer="B",
                explanation="Taking ownership, communicating transparently, and problem-solving demonstrates integrity and accountability."
            ),
            SoftSkillsTest(
                question="Multiple stakeholders request conflicting changes to a project. How do you handle this?",
                option_a="Choose one stakeholder's request randomly",
                option_b="Facilitate a discussion to understand priorities, constraints, and find alignment",
                option_c="Implement all requests without discussing trade-offs",
                option_d="Ignore all requests",
                correct_answer="B",
                explanation="Stakeholder management requires negotiation, clear communication, and finding balanced solutions."
            )
        ]
        db.session.add_all(questions)
        db.session.commit()

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

# --- RECRUITER ROUTES ---
@app.route('/recruiter/dashboard')
def recruiter_dashboard():
    # Show newest jobs first
    jobs = Job.query.order_by(Job.id.desc()).all()
    # Show newest applications first
    applications = Application.query.order_by(Application.id.desc()).all()
    students = Student.query.all()
    return render_template('recruiter.html', jobs=jobs, applications=applications, students=students)

@app.route('/recruiter/post_job', methods=['POST'])
def post_job():
    try:
        new_job = Job(
            title=request.form['title'], 
            company_name=request.form['company'], 
            description=request.form['description'],
            skills=request.form['skills']
        )
        db.session.add(new_job)
        db.session.commit()
        flash('Job Posted Successfully!', 'success')
    except:
        flash('Error posting job. Try again.', 'error')
    return redirect(url_for('recruiter_dashboard'))

@app.route('/recruiter/accept/<int:app_id>')
def accept_application(app_id):
    application = Application.query.get(app_id)
    if application:
        application.status = 'Accepted'
        application.feedback = "Welcome to the team!"
        db.session.commit()
        flash(f'Candidate Accepted!', 'success')
    return redirect(url_for('recruiter_dashboard'))

@app.route('/recruiter/reject/<int:app_id>', methods=['POST'])
def reject_application(app_id):
    reason = request.form.get('reason')
    if not reason or reason.strip() == '':
        flash('Feedback reason is mandatory for rejection!', 'error')
        return redirect(url_for('recruiter_dashboard'))
    
    application = Application.query.get(app_id)
    if application:
        application.status = 'Rejected'
        application.feedback = reason  # Save the mandatory reason (instant feedback)
        db.session.commit()
        flash('Candidate Rejected. Feedback sent instantly.', 'error')
    return redirect(url_for('recruiter_dashboard'))

@app.route('/recruiter/view_student/<int:student_id>')
def view_student_profile(student_id):
    student = Student.query.get_or_404(student_id)
    applications = Application.query.filter_by(student_id=student_id).all()
    return render_template('student_profile.html', student=student, applications=applications)

# --- STUDENT ROUTES ---
@app.route('/student/dashboard', methods=['GET', 'POST'])
def student_dashboard():
    jobs = Job.query.order_by(Job.id.desc()).all()
    recommended_jobs = []
    my_skills = ""

    # Get student applications
    student_name = request.args.get('name') or request.form.get('student_name')
    student = None
    if student_name:
        student = Student.query.filter_by(name=student_name).first()
    
    my_applications = Application.query.order_by(Application.id.desc()).all()
    if student:
        my_applications = Application.query.filter_by(student_id=student.id).order_by(Application.id.desc()).all()

    # Recommendation Logic
    if request.method == 'POST':
        if 'student_skills' in request.form:
            my_skills = request.form.get('student_skills', '').lower()
            my_skill_list = [s.strip() for s in my_skills.split(',')]
            
            for job in jobs:
                job_skills = [s.strip().lower() for s in job.skills.split(',')]
                # If any skill matches, recommend the job
                if any(skill in job_skills for skill in my_skill_list) and my_skills != "":
                    recommended_jobs.append(job.id)

    return render_template('student.html', jobs=jobs, recommended=recommended_jobs, my_skills=my_skills, my_applications=my_applications, student=student)

@app.route('/student/profile', methods=['GET', 'POST'])
def student_profile():
    student_name = request.form.get('name') or request.args.get('name')
    student = None
    if student_name:
        student = Student.query.filter_by(name=student_name).first()
        if not student and request.method == 'POST':
            # Create new student profile
            student = Student(
                name=student_name,
                github_url=request.form.get('github_url', ''),
                projects=request.form.get('projects', ''),
                digilocker_id=request.form.get('digilocker_id', ''),
                skills=request.form.get('skills', '')
            )
            db.session.add(student)
            db.session.commit()
            flash('Profile created successfully!', 'success')
        elif request.method == 'POST' and student:
            # Update existing profile
            student.github_url = request.form.get('github_url', student.github_url)
            student.projects = request.form.get('projects', student.projects)
            student.digilocker_id = request.form.get('digilocker_id', student.digilocker_id)
            student.skills = request.form.get('skills', student.skills)
            db.session.commit()
            flash('Profile updated successfully!', 'success')
    
    return render_template('student_profile_form.html', student=student)

@app.route('/student/apply/<int:job_id>', methods=['POST'])
def apply_for_job(job_id):
    name = request.form.get('student_name')
    if not name:
        flash('Please enter your name!', 'error')
        return redirect(url_for('student_dashboard'))
    
    # Get or create student
    student = Student.query.filter_by(name=name).first()
    if not student:
        flash('Please create your profile first!', 'error')
        return redirect(url_for('student_profile', name=name))
    
    job = Job.query.get_or_404(job_id)
    
    # Automated rejection based on skillset
    student_skills = [s.strip().lower() for s in (student.skills or '').split(',') if s.strip()]
    job_skills = [s.strip().lower() for s in job.skills.split(',') if s.strip()]
    
    # Check if student has at least one required skill
    has_required_skill = any(skill in job_skills for skill in student_skills) if student_skills else False
    
    new_app = Application(job_id=job_id, student_name=name, student_id=student.id)
    
    if not has_required_skill and student_skills:  # Auto-reject if skills don't match
        new_app.status = 'Rejected'
        new_app.auto_rejected = True
        new_app.feedback = f"Your skills ({', '.join(student_skills)}) do not match the required skills ({', '.join(job_skills)})."
        db.session.add(new_app)
        db.session.commit()
        flash('Application submitted but automatically rejected due to skills mismatch. See feedback below.', 'error')
    else:
        db.session.add(new_app)
        db.session.commit()
        flash('Application Submitted!', 'success')
    
    return redirect(url_for('student_dashboard', name=name))

@app.route('/student/soft_skills_test', methods=['GET', 'POST'])
def soft_skills_test():
    student_name = request.args.get('name') or request.form.get('student_name')
    if not student_name:
        flash('Please enter your name to take the test!', 'error')
        return redirect(url_for('student_dashboard'))
    
    student = Student.query.filter_by(name=student_name).first()
    if not student:
        flash('Please create your profile first!', 'error')
        return redirect(url_for('student_profile', name=student_name))
    
    if request.method == 'POST':
        # Process test answers
        questions = SoftSkillsTest.query.all()
        correct_count = 0
        total_questions = len(questions)
        
        for question in questions:
            answer_key = f'answer_{question.id}'
            student_answer = request.form.get(answer_key)
            if student_answer and student_answer.upper() == question.correct_answer.upper():
                correct_count += 1
                is_correct = True
            else:
                is_correct = False
            
            # Save response
            response = TestResponse(
                student_name=student_name,
                student_id=student.id,
                test_id=question.id,
                answer=student_answer or '',
                is_correct=is_correct
            )
            db.session.add(response)
        
        # Calculate score (percentage)
        score = (correct_count / total_questions * 100) if total_questions > 0 else 0
        student.soft_skills_score = score
        db.session.commit()
        
        flash(f'Test completed! Your score: {score:.1f}% ({correct_count}/{total_questions})', 'success')
        return redirect(url_for('student_dashboard', name=student_name))
    
    # GET request - show test
    questions = SoftSkillsTest.query.all()
    return render_template('soft_skills_test.html', questions=questions, student_name=student_name)

@app.route('/student/rate_company', methods=['POST'])
def rate_company():
    student_name = request.form.get('student_name')
    company_name = request.form.get('company_name')
    job_id = request.form.get('job_id', type=int)
    rating = request.form.get('rating', type=int)
    feedback = request.form.get('feedback', '')
    
    if not all([student_name, company_name, job_id, rating]):
        flash('All fields are required!', 'error')
        return redirect(url_for('student_dashboard', name=student_name))
    
    if rating < 1 or rating > 5:
        flash('Rating must be between 1 and 5!', 'error')
        return redirect(url_for('student_dashboard', name=student_name))
    
    rating_obj = CompanyRating(
        student_name=student_name,
        company_name=company_name,
        job_id=job_id,
        rating=rating,
        feedback=feedback
    )
    db.session.add(rating_obj)
    db.session.commit()
    flash('Thank you for your feedback!', 'success')
    return redirect(url_for('student_dashboard', name=student_name))

@app.route('/company_ratings')
def company_ratings():
    ratings = CompanyRating.query.order_by(CompanyRating.created_at.desc()).all()
    # Calculate average ratings per company
    company_stats = {}
    for rating in ratings:
        if rating.company_name not in company_stats:
            company_stats[rating.company_name] = {'total': 0, 'count': 0, 'ratings': []}
        company_stats[rating.company_name]['total'] += rating.rating
        company_stats[rating.company_name]['count'] += 1
        company_stats[rating.company_name]['ratings'].append(rating)
    
    for company in company_stats:
        company_stats[company]['average'] = company_stats[company]['total'] / company_stats[company]['count']
    
    return render_template('company_ratings.html', company_stats=company_stats)

if __name__ == '__main__':
    app.run(debug=True)