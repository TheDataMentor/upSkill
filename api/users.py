from flask import request
from flask_restful import Resource
from app import limiter
from services.user_service import UserService

class UserResource(Resource):
    @limiter.limit("10 per minute")
    def get(self, user_id):
        user = UserService.get_user_with_courses_and_skills(user_id)
        if user:
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'courses': [{'id': c.id, 'title': c.title} for c in user.courses],
                'skills': [{'id': s.id, 'name': s.name, 'proficiency': s.proficiency} for s in user.skills]
            }
        return {'message': 'User not found'}, 404

    @limiter.limit("5 per minute")
    def put(self, user_id):
        data = request.get_json()
        user = UserService.update_user(user_id, data)
        if user:
            return {'message': 'User updated successfully'}
        return {'message': 'User not found'}, 404

    @limiter.limit("3 per minute")
    def delete(self, user_id):
        if UserService.delete_user(user_id):
            return {'message': 'User deleted successfully'}
        return {'message': 'User not found'}, 404

class UserListResource(Resource):
    @limiter.limit("20 per minute")
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

    @limiter.limit("5 per minute")
    def post(self):
        data = request.get_json()
        user = UserService.create_user(data)
        return {'id': user.id, 'username': user.username, 'email': user.email}, 201

class UserCoursesResource(Resource):
    @limiter.limit("10 per minute")
    def get(self, user_id):
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        courses = UserService.get_user_courses(user_id)
        return {
            'courses': [{'id': course.id, 'title': course.title, 'description': course.description} for course in courses]
        }

class UserSkillsResource(Resource):
    @limiter.limit("10 per minute")
    def get(self, user_id):
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        skills = UserService.get_user_skills(user_id)
        return {
            'skills': [{'id': skill.id, 'name': skill.name, 'proficiency': skill.proficiency} for skill in skills]
        }
