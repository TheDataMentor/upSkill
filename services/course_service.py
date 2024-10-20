from app import db
from models import Course
from utils.helpers import cache_response, invalidate_cache, get_cache_key

class CourseService:
    @staticmethod
    @cache_response(timeout=600)  # Cache for 10 minutes
    def get_course(course_id):
        return Course.query.get(course_id)

    @staticmethod
    @cache_response(timeout=300)  # Cache for 5 minutes
    def get_all_courses():
        return Course.query.all()

    @staticmethod
    def create_course(data):
        course = Course(title=data['title'], description=data['description'], user_id=data['user_id'])
        db.session.add(course)
        db.session.commit()
        invalidate_cache(get_cache_key('courses'))
        return course

    @staticmethod
    def update_course(course_id, data):
        course = Course.query.get(course_id)
        if course:
            course.title = data.get('title', course.title)
            course.description = data.get('description', course.description)
            db.session.commit()
            invalidate_cache(get_cache_key('courses', course_id))
        return course

    @staticmethod
    def delete_course(course_id):
        course = Course.query.get(course_id)
        if course:
            db.session.delete(course)
            db.session.commit()
            invalidate_cache(get_cache_key('courses', course_id))
            return True
        return False
