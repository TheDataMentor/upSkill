from flask import request
from flask_restful import Resource
from app import db, limiter
from models import Skill
from services.skill_service import SkillService

class SkillResource(Resource):
    @limiter.limit("10 per minute")
    def get(self, skill_id):
        skill = SkillService.get_skill(skill_id)
        if skill:
            return {'id': skill.id, 'name': skill.name, 'proficiency': skill.proficiency, 'user_id': skill.user_id}
        return {'message': 'Skill not found'}, 404

    @limiter.limit("5 per minute")
    def put(self, skill_id):
        data = request.get_json()
        skill = SkillService.update_skill(skill_id, data)
        if skill:
            return {'message': 'Skill updated successfully'}
        return {'message': 'Skill not found'}, 404

    @limiter.limit("3 per minute")
    def delete(self, skill_id):
        if SkillService.delete_skill(skill_id):
            return {'message': 'Skill deleted successfully'}
        return {'message': 'Skill not found'}, 404

class SkillListResource(Resource):
    @limiter.limit("20 per minute")
    def get(self):
        skills = SkillService.get_all_skills()
        return [{'id': skill.id, 'name': skill.name, 'proficiency': skill.proficiency, 'user_id': skill.user_id} for skill in skills]

    @limiter.limit("5 per minute")
    def post(self):
        data = request.get_json()
        skill = SkillService.create_skill(data)
        return {'id': skill.id, 'name': skill.name, 'proficiency': skill.proficiency, 'user_id': skill.user_id}, 201
