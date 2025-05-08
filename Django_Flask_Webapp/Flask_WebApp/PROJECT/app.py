from flask import Flask, render_template, request, redirect, url_for, session, flash ,jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a real secret key in production

# Database configuration (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = generate_password_hash(password)  # Hashing password

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)    
    title = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)



class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    education = db.Column(db.String(200))
    experience = db.Column(db.String(200))
    skills = db.Column(db.String(200))
    projects = db.Column(db.String(200))

    user = db.relationship('User', backref=db.backref('resume', uselist=False))

with app.app_context():
    db.create_all()



# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create the database and tables
with app.app_context():
    db.create_all()


# @app.route('/home')
# def home():
#     return render_template('index.html')

@app.route('/')
def home():
    user_name = session.get('user_name')  
    return render_template('index.html')

# Find Jobs page
@app.route('/find_jobs')
def find_jobs():
    jobs = Job.query.all()
    return render_template('jobs.html',jobs=jobs)

# Companies page
@app.route('/companies')
def companies():
    # Fetch all jobs from the database
    jobs = Job.query.all()
    return render_template('companies.html', jobs=jobs)   # Ensure lowercase filename

# Resources page
@app.route('/resources')
def resources():
    return render_template('resources.html')

# Post a Job page
@app.route('/post_job')
@login_required
def post_job():
    return render_template('post-job.html')

@app.route('/post', methods=['POST'])
def post():
    if request.method == 'POST':
        title = request.form.get('job_title')
        company = request.form.get('company_name')
        location = request.form.get('location')
        description = request.form.get('job_description')

        # Create a new job entry
        new_job = Job(title=title, company=company, location=location, description=description)
        db.session.add(new_job)
        db.session.commit()

    return redirect(url_for('post_job'))

# Resume Tips page
@app.route('/resources/resume-tips')
def resume_tips():
    return render_template('resume_writing_tips.html')

# Interview Preparation page
@app.route('/resources/interview-prep')
def interview_prep():
    return render_template('interview_prep.html')

# Career Growth page
@app.route('/resources/career-growth')
def career_growth():
    return render_template('growth.html')


@app.route('/user_profile')
@login_required
def user_profile():
    # Fetch the resume data for the current user
    resume = get_resume_for_user(current_user.id)
    return render_template('user_profile.html', current_user=current_user, resume=resume)


@app.route('/about')
def about():
    return render_template('about.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            session['user_name'] = user.name
            session.modified = True  # Ensure session changes are saved
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')


# Registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')     
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if the email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered', 'error')
            return redirect(url_for('register'))

        # Create a new user with a hashed password
        new_user = User(name, email, password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('user_name', None)  # Remove user_name from session
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/delete_job/<int:job_id>', methods=['POST'])
@login_required
def delete_job(job_id):
    # Find the job by its ID
    job_to_delete = Job.query.get(job_id)
    db.session.delete(job_to_delete)
    db.session.commit()
    flash('Job successfully deleted!', 'success')
    return redirect(url_for('companies'))


@app.route('/update_job/<int:job_id>', methods=['GET', 'POST'])
@login_required
def update_job(job_id):
    # Fetch the job from the database
    job = Job.query.get_or_404(job_id)

    if request.method == 'POST':
        # Get updated details from the form
        job.title = request.form.get('job_title')
        job.company = request.form.get('company_name')
        job.location = request.form.get('location')
        job.description = request.form.get('job_description')

        try:
            # Commit changes to the database
            db.session.commit()
            flash('Job successfully updated!', 'success')
        except:
            db.session.rollback()
            flash('An error occurred while updating the job.', 'error')

        return redirect(url_for('companies'))  # Redirect back to the companies page

    # Render the update form template with job details pre-filled
    return render_template('update_job.html', job=job)

@app.route('/api/user', methods=['GET'])
@login_required 
def get_all_users():
    users = User.query.all()
    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'password': user.password 
        })
    return jsonify(users_data), 200

@app.route('/api/jobs', methods=['GET'])
@login_required 
def get_all_jobs():
    jobs = Job.query.all()
    job_data = []
    for user in jobs:
        job_data.append({
            'id': user.id,
            'title': user.title,
            'company': user.company,
            'location': user.location,
            'description': user.description 
        })
    return jsonify(job_data), 200




def get_resume_for_user(user_id):
    return Resume.query.filter_by(user_id=user_id).first()

@app.route('/resume', methods=['GET', 'POST'])
@login_required
def resume():
    resume = Resume.query.filter_by(user_id=current_user.id).first()  # Check if the user has a resume
    
    if request.method == 'POST':
        education = request.form.get('education')
        experience = request.form.get('experience')
        skills = request.form.get('skills')
        projects = request.form.get('projects')

        if resume:
            # If resume exists, update it
            resume.education = education
            resume.experience = experience
            resume.skills = skills
            resume.projects = projects
        else:
            # If no resume exists, create a new one
            resume = Resume(
                user_id=current_user.id,
                education=education,
                experience=experience,
                skills=skills,
                projects=projects
            )
            db.session.add(resume)

        db.session.commit()  # Commit changes to the database
        flash("Resume saved successfully!", "success")
        return redirect(url_for('resume'))  # Redirect to the same page

    return render_template('resume.html', resume=resume)



# @app.route('/user')
# @login_required
# def user_profile():
#     # Fetch the current user's details
#     user = current_user
    
#     # Get the user's resume if it exists
#     resume = Resume.query.filter_by(user_id=current_user.id).first()

#     return render_template('user_profile.html', user=user, resume=resume)



@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        new_name = request.form.get('name')
        new_email = request.form.get('email')
        new_password = request.form.get('password')

        # Update user info
        current_user.name = new_name
        current_user.email = new_email
        if new_password:
            current_user.password = generate_password_hash(new_password)

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('user'))

    return render_template('edit_profile.html', user=current_user)



@app.route('/api/resume/<int:user_id>', methods=['GET'])
def get_resume(user_id):
    resume = Resume.query.filter_by(user_id=user_id).first()
    if not resume:
        return jsonify({'error': 'Resume not found'}), 404
    return jsonify({
        'education': resume.education,
        'experience': resume.experience,
        'skills': resume.skills,
        'projects': resume.projects
    }), 200


if __name__ == '__main__':
    app.run(debug=True)
