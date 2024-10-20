from app import db
from models import User, Course, Skill
from sqlalchemy.orm import joinedload, contains_eager
from utils.helpers import cache_response, invalidate_cache, get_cache_key

class UserService:
    @staticmethod
    @cache_response(timeout=600)  # Cache for 10 minutes
    def get_user(user_id):
        return User.query.options(
            joinedload(User.courses),
            joinedload(User.skills)
        ).get(user_id)

    @staticmethod
    @cache_response(timeout=300)  # Cache for 5 minutes
    def get_all_users(page=1, per_page=20):
        return User.query.options(
            joinedload(User.courses),
            joinedload(User.skills)
        ).paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_user_with_courses_and_skills(user_id):
        return User.query.options(
            contains_eager(User.courses),
            contains_eager(User.skills)
        ).outerjoin(User.courses).outerjoin(User.skills).filter(User.id == user_id).first()

    @staticmethod
    def create_user(data):
        user = User(username=data['username'], email=data['email'])
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        invalidate_cache(get_cache_key('users'))
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
    def get_user_courses(user_id):
        return Course.query.filter(Course.user_id == user_id).all()

    @staticmethod
    def get_user_skills(user_id):
        return Skill.query.filter(Skill.user_id == user_id).all()
