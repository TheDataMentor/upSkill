from flask import request
from flask_restful import Resource
from app import rate_limiter
from services.skill_service import SkillService

class SkillResource(Resource):
    @rate_limiter.limit("skill_get", limit=10, period=60)
    def get(self, skill_id):
        skill = SkillService.get_skill(skill_id)
        if skill:
            return {'id': skill.id, 'name': skill.name, 'proficiency': skill.proficiency, 'user_id': skill.user_id}
        return {'message': 'Skill not found'}, 404

    @rate_limiter.limit("skill_put", limit=5, period=60)
    def put(self, skill_id):
        data = request.get_json()
        skill = SkillService.update_skill(skill_id, data)
        if skill:
            return {'message': 'Skill updated successfully'}
        return {'message': 'Skill not found'}, 404

    @rate_limiter.limit("skill_delete", limit=3, period=60)
    def delete(self, skill_id):
        if SkillService.delete_skill(skill_id):
            return {'message': 'Skill deleted successfully'}
        return {'message': 'Skill not found'}, 404

class SkillListResource(Resource):
    @rate_limiter.limit("skill_list_get", limit=20, period=60)
    def get(self):
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        skills_paginated = SkillService.get_all_skills(page=page, per_page=per_page)
        return {
            'skills': [{'id': skill.id, 'name': skill.name, 'proficiency': skill.proficiency, 'user_id': skill.user_id} for skill in skills_paginated.items],
            'total': skills_paginated.total,
            'pages': skills_paginated.pages,
            'current_page': skills_paginated.page
        }

    @rate_limiter.limit("skill_list_post", limit=5, period=60)
    def post(self):
        data = request.get_json()
        skill = SkillService.create_skill(data)
        return {'id': skill.id, 'name': skill.name, 'proficiency': skill.proficiency, 'user_id': skill.user_id}, 201
