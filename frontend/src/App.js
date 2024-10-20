import React from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import Home from './components/Home';
import UserList from './components/UserList';
import CourseList from './components/CourseList';
import SkillList from './components/SkillList';

function App() {
  return (
    <Router>
      <div className="container mt-3">
        <nav className="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
          <div className="container-fluid">
            <Link className="navbar-brand" to="/">UpSkill</Link>
            <div className="navbar-nav">
              <Link className="nav-link" to="/">Home</Link>
              <Link className="nav-link" to="/users">Users</Link>
              <Link className="nav-link" to="/courses">Courses</Link>
              <Link className="nav-link" to="/skills">Skills</Link>
            </div>
          </div>
        </nav>

        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/users" element={<UserList />} />
          <Route path="/courses" element={<CourseList />} />
          <Route path="/skills" element={<SkillList />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
