from app import db
from models import Skill
from utils.helpers import cache_response, invalidate_cache, get_cache_key

class SkillService:
    @staticmethod
    @cache_response(timeout=600)  # Cache for 10 minutes
    def get_skill(skill_id):
        return Skill.query.get(skill_id)

    @staticmethod
    @cache_response(timeout=300)  # Cache for 5 minutes
    def get_all_skills():
        return Skill.query.all()

    @staticmethod
    def create_skill(data):
        skill = Skill(name=data['name'], proficiency=data['proficiency'], user_id=data['user_id'])
        db.session.add(skill)
        db.session.commit()
        invalidate_cache(get_cache_key('skills'))
        return skill

    @staticmethod
    def update_skill(skill_id, data):
        skill = Skill.query.get(skill_id)
        if skill:
            skill.name = data.get('name', skill.name)
            skill.proficiency = data.get('proficiency', skill.proficiency)
            db.session.commit()
            invalidate_cache(get_cache_key('skills', skill_id))
        return skill

    @staticmethod
    def delete_skill(skill_id):
        skill = Skill.query.get(skill_id)
        if skill:
            db.session.delete(skill)
            db.session.commit()
            invalidate_cache(get_cache_key('skills', skill_id))
            return True
        return False
