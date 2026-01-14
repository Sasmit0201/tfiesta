from app import app, db, Job, Application

def create_fake_data():
    with app.app_context():
        # Clear existing data to start fresh
        db.drop_all()
        db.create_all()

        # Create 3 Fake Jobs
        job1 = Job(title="Machine Learning Intern", company_name="DeepMind", 
                   description="Work on LLMs.", skills="Python, Pytorch, AI")
        job2 = Job(title="Web Developer", company_name="Google", 
                   description="Build React dashboards.", skills="React, JavaScript, CSS")
        job3 = Job(title="Data Analyst", company_name="Goldman Sachs", 
                   description="Analyze financial trends.", skills="SQL, Excel, Python")

        db.session.add_all([job1, job2, job3])
        
        # Create 2 Fake Applications
        app1 = Application(job_id=1, student_name="Alice (Demo User)")
        app2 = Application(job_id=3, student_name="Bob (Demo User)")
        
        db.session.add_all([app1, app2])
        db.session.commit()
        print("✅ Database populated with fake data!")

if __name__ == '__main__':
    create_fake_data()