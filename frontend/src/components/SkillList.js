import React, { useState, useEffect } from 'react';
import axios from 'axios';

function SkillList() {
  const [skills, setSkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSkills = async () => {
      try {
        const response = await axios.get('/api/skills');
        setSkills(response.data.skills);
        setLoading(false);
      } catch (err) {
        setError('Error fetching skills');
        setLoading(false);
      }
    };

    fetchSkills();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>{error}</div>;

  return (
    <div>
      <h2>Skills</h2>
      <ul className="list-group">
        {skills.map(skill => (
          <li key={skill.id} className="list-group-item d-flex justify-content-between align-items-center">
            {skill.name}
            <span className="badge bg-primary rounded-pill">Proficiency: {skill.proficiency}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default SkillList;
