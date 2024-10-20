from flask import request
from flask_restful import Resource
from app import db, limiter
from models import Course
from services.course_service import CourseService

class CourseResource(Resource):
    @limiter.limit("10 per minute")
    def get(self, course_id):
        course = CourseService.get_course(course_id)
        if course:
            return {'id': course.id, 'title': course.title, 'description': course.description, 'user_id': course.user_id}
        return {'message': 'Course not found'}, 404

    @limiter.limit("5 per minute")
    def put(self, course_id):
        data = request.get_json()
        course = CourseService.update_course(course_id, data)
        if course:
            return {'message': 'Course updated successfully'}
        return {'message': 'Course not found'}, 404

    @limiter.limit("3 per minute")
    def delete(self, course_id):
        if CourseService.delete_course(course_id):
            return {'message': 'Course deleted successfully'}
        return {'message': 'Course not found'}, 404

class CourseListResource(Resource):
    @limiter.limit("20 per minute")
    def get(self):
        courses = CourseService.get_all_courses()
        return [{'id': course.id, 'title': course.title, 'description': course.description, 'user_id': course.user_id} for course in courses]

    @limiter.limit("5 per minute")
    def post(self):
        data = request.get_json()
        course = CourseService.create_course(data)
        return {'id': course.id, 'title': course.title, 'description': course.description, 'user_id': course.user_id}, 201
