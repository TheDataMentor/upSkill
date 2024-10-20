import React from 'react';
import { Link } from 'react-router-dom';

function Home() {
  return (
    <div className="jumbotron">
      <h1 className="display-4">Welcome to UpSkill</h1>
      <p className="lead">A scalable micro SaaS application for managing your skills and courses.</p>
      <hr className="my-4" />
      <p>Get started by exploring our users, courses, and skills.</p>
      <div className="d-flex justify-content-around">
        <Link to="/users" className="btn btn-primary btn-lg">Users</Link>
        <Link to="/courses" className="btn btn-success btn-lg">Courses</Link>
        <Link to="/skills" className="btn btn-info btn-lg">Skills</Link>
      </div>
    </div>
  );
}

export default Home;
