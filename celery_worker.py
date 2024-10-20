from celery import Celery
from config import Config

celery = Celery(
    'tasks',
    broker=Config.REDIS_URL,
    backend=Config.REDIS_URL
)

celery.conf.update(Config.__dict__)

@celery.task
def update_user_stats(user_id):
    from models import User, Course, Skill
    from extensions import db
    
    user = User.query.get(user_id)
    if user:
        course_count = Course.query.filter_by(user_id=user_id).count()
        skill_count = Skill.query.filter_by(user_id=user_id).count()
        user.course_count = course_count
        user.skill_count = skill_count
        db.session.commit()
    return f"Updated stats for user {user_id}"

@celery.task
def generate_user_report(user_id):
    from models import User, Course, Skill
    
    user = User.query.get(user_id)
    if user:
        courses = Course.query.filter_by(user_id=user_id).all()
        skills = Skill.query.filter_by(user_id=user_id).all()
        report = f"User Report for {user.username}\n"
        report += f"Courses ({len(courses)}):\n"
        for course in courses:
            report += f"- {course.title}\n"
        report += f"\nSkills ({len(skills)}):\n"
        for skill in skills:
            report += f"- {skill.name} (Proficiency: {skill.proficiency})\n"
        return report
    return f"User {user_id} not found"

def init_celery(app):
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
