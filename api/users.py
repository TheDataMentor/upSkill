from flask import request
from flask_restful import Resource
from app import db, limiter
from models import User
from services.user_service import UserService

class UserResource(Resource):
    @limiter.limit("10 per minute")
    def get(self, user_id):
        user = UserService.get_user(user_id)
        if user:
            return {'id': user.id, 'username': user.username, 'email': user.email}
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
        users = UserService.get_all_users()
        return [{'id': user.id, 'username': user.username, 'email': user.email} for user in users]

    @limiter.limit("5 per minute")
    def post(self):
        data = request.get_json()
        user = UserService.create_user(data)
        return {'id': user.id, 'username': user.username, 'email': user.email}, 201
