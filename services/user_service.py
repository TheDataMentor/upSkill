from app import db, cache
from models import User, Course, Skill
from sqlalchemy.orm import joinedload, contains_eager
from utils.helpers import invalidate_cache, get_cache_key
import json
from sqlalchemy import text, Index, func

class UserService:
    @staticmethod
    @cache.memoize(timeout=600)  # Cache for 10 minutes
    def get_user(user_id):
        user = User.query.options(
            joinedload(User.courses),
            joinedload(User.skills)
        ).get(user_id)
        if user:
            from celery_worker import update_user_stats
            update_user_stats.delay(user_id)  # Trigger background task
        return user

    @staticmethod
    @cache.memoize(timeout=300)  # Cache for 5 minutes
    def get_all_users(page=1, per_page=20):
        return User.query.options(
            joinedload(User.courses),
            joinedload(User.skills)
        ).paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_user_with_courses_and_skills(user_id):
        cache_key = f"user:{user_id}:full"
        cached_data = cache.get(cache_key)
        if cached_data:
            return json.loads(cached_data)

        user = User.query.options(
            contains_eager(User.courses),
            contains_eager(User.skills)
        ).outerjoin(User.courses).outerjoin(User.skills).filter(User.id == user_id).first()

        if user:
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'courses': [{'id': c.id, 'title': c.title} for c in user.courses],
                'skills': [{'id': s.id, 'name': s.name, 'proficiency': s.proficiency} for s in user.skills]
            }
            cache.set(cache_key, json.dumps(user_data), timeout=600)  # Cache for 10 minutes
            from celery_worker import update_user_stats
            update_user_stats.delay(user_id)  # Trigger background task
            return user_data
        return None

    @staticmethod
    def create_user(data):
        user = User(username=data['username'], email=data['email'])
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        invalidate_cache(get_cache_key('users'))
        from celery_worker import update_user_stats
        update_user_stats.delay(user.id)  # Trigger background task
        return user

    @staticmethod
    def update_user(user_id, data):
        user = User.query.get(user_id)
        if user:
            user.username = data.get('username', user.username)
            user.email = data.get('email', user.email)
            if 'password' in data:
                user.set_password(data['password'])
            db.session.commit()
            invalidate_cache(get_cache_key('users', user_id))
            from celery_worker import update_user_stats
            update_user_stats.delay(user_id)  # Trigger background task
        return user

    @staticmethod
    def delete_user(user_id):
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            invalidate_cache(get_cache_key('users', user_id))
            return True
        return False

    @staticmethod
    @cache.memoize(timeout=300)  # Cache for 5 minutes
    def get_user_courses(user_id):
        return Course.query.filter(Course.user_id == user_id).all()

    @staticmethod
    @cache.memoize(timeout=300)  # Cache for 5 minutes
    def get_user_skills(user_id):
        return Skill.query.filter(Skill.user_id == user_id).all()

    @staticmethod
    @cache.memoize(timeout=300)  # Cache for 5 minutes
    def get_users_with_course_count():
        query = db.session.query(
            User.id,
            User.username,
            User.email,
            func.count(Course.id).label('course_count')
        ).outerjoin(Course).group_by(User.id, User.username, User.email)
        
        result = query.all()
        return [dict(zip(['id', 'username', 'email', 'course_count'], row)) for row in result]

    @staticmethod
    def ensure_indexes():
        # Check if indexes already exist
        existing_indexes = db.session.execute(text("SELECT indexname FROM pg_indexes WHERE tablename = 'user'")).fetchall()
        existing_index_names = [index[0] for index in existing_indexes]

        # Create indexes if they don't exist
        if 'ix_user_username' not in existing_index_names:
            Index('ix_user_username', User.username).create(db.engine)
        if 'ix_user_email' not in existing_index_names:
            Index('ix_user_email', User.email).create(db.engine)

    @staticmethod
    def generate_user_report(user_id):
        from celery_worker import generate_user_report
        return generate_user_report.delay(user_id)
