from flask import request
from flask_restful import Resource
from app import rate_limiter
from services.course_service import CourseService

class CourseResource(Resource):
    @rate_limiter.limit("course_get", limit=15, period=60)
    def get(self, course_id):
        course = CourseService.get_course(course_id)
        if course:
            return {'id': course.id, 'title': course.title, 'description': course.description, 'user_id': course.user_id}
        return {'message': 'Course not found'}, 404

    @rate_limiter.limit("course_put", limit=5, period=60)
    def put(self, course_id):
        data = request.get_json()
        course = CourseService.update_course(course_id, data)
        if course:
            return {'message': 'Course updated successfully'}
        return {'message': 'Course not found'}, 404

    @rate_limiter.limit("course_delete", limit=3, period=60)
    def delete(self, course_id):
        if CourseService.delete_course(course_id):
            return {'message': 'Course deleted successfully'}
        return {'message': 'Course not found'}, 404

class CourseListResource(Resource):
    @rate_limiter.limit("course_list_get", limit=30, period=60)
    def get(self):
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        courses_paginated = CourseService.get_all_courses(page=page, per_page=per_page)
        return {
            'courses': [{'id': course.id, 'title': course.title, 'description': course.description, 'user_id': course.user_id} for course in courses_paginated.items],
            'total': courses_paginated.total,
            'pages': courses_paginated.pages,
            'current_page': courses_paginated.page
        }

    @rate_limiter.limit("course_list_post", limit=5, period=60)
    def post(self):
        data = request.get_json()
        course = CourseService.create_course(data)
        return {'id': course.id, 'title': course.title, 'description': course.description, 'user_id': course.user_id}, 201
