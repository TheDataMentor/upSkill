from flask import request, jsonify
from flask_restful import Resource
from utils.rate_limiter_init import rate_limiter
from services.user_service import UserService
from app import cache
from flask_compress import Compress

compress = Compress()

class UserResource(Resource):
    @rate_limiter.limit("user_get", limit=10, period=60)
    @cache.cached(timeout=60, key_prefix='user_resource')
    @compress.compressed()
    def get(self, user_id):
        user = UserService.get_user_with_courses_and_skills(user_id)
        if user:
            return user
        return {'message': 'User not found'}, 404

    @rate_limiter.limit("user_put", limit=5, period=60)
    @compress.compressed()
    def put(self, user_id):
        data = request.get_json()
        user = UserService.update_user(user_id, data)
        if user:
            cache.delete_memoized(UserService.get_user, user_id)
            cache.delete_memoized(UserService.get_user_with_courses_and_skills, user_id)
            return {'message': 'User updated successfully'}
        return {'message': 'User not found'}, 404

    @rate_limiter.limit("user_delete", limit=3, period=60)
    def delete(self, user_id):
        if UserService.delete_user(user_id):
            cache.delete_memoized(UserService.get_user, user_id)
            cache.delete_memoized(UserService.get_user_with_courses_and_skills, user_id)
            return {'message': 'User deleted successfully'}
        return {'message': 'User not found'}, 404

class UserListResource(Resource):
    @rate_limiter.limit("user_list_get", limit=20, period=60)
    @cache.cached(timeout=60, key_prefix='user_list_resource')
    @compress.compressed()
    def get(self):
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        users_paginated = UserService.get_all_users(page=page, per_page=per_page)
        return {
            'users': [{'id': user.id, 'username': user.username, 'email': user.email} for user in users_paginated.items],
            'total': users_paginated.total,
            'pages': users_paginated.pages,
            'current_page': users_paginated.page
        }

    @rate_limiter.limit("user_list_post", limit=5, period=60)
    @compress.compressed()
    def post(self):
        data = request.get_json()
        user = UserService.create_user(data)
        cache.delete_memoized(UserService.get_all_users)
        return {'id': user.id, 'username': user.username, 'email': user.email}, 201

class UserCoursesResource(Resource):
    @rate_limiter.limit("user_courses_get", limit=15, period=60)
    @cache.cached(timeout=60, key_prefix='user_courses_resource')
    @compress.compressed()
    def get(self, user_id):
        courses = UserService.get_user_courses(user_id)
        return {
            'courses': [{'id': course.id, 'title': course.title, 'description': course.description} for course in courses]
        }

class UserSkillsResource(Resource):
    @rate_limiter.limit("user_skills_get", limit=15, period=60)
    @cache.cached(timeout=60, key_prefix='user_skills_resource')
    @compress.compressed()
    def get(self, user_id):
        skills = UserService.get_user_skills(user_id)
        return {
            'skills': [{'id': skill.id, 'name': skill.name, 'proficiency': skill.proficiency} for skill in skills]
        }

class UsersWithCourseCountResource(Resource):
    @rate_limiter.limit("users_with_course_count_get", limit=10, period=60)
    @cache.cached(timeout=300, key_prefix='users_with_course_count')
    @compress.compressed()
    def get(self):
        users_with_count = UserService.get_users_with_course_count()
        return {'users': users_with_count}
