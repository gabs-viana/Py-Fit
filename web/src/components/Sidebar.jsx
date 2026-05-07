import React from 'react';
import './Sidebar.css';

export default function Sidebar({ activeTab, setActiveTab }) {
  return (
    <aside className="sidebar glass-card">
      <div className="sidebar-logo">
        <h2>Py-Fit <span className="highlight">V6</span></h2>
        <p>Dual-Core System</p>
      </div>

      <nav className="sidebar-nav">
        <button 
          className={`nav-item ${activeTab === 'systemic' ? 'active' : ''}`}
          onClick={() => setActiveTab('systemic')}
        >
          <span className="icon">🧠</span>
          <span className="label">Visão Sistêmica</span>
        </button>

        <button 
          className={`nav-item ${activeTab === 'runlab' ? 'active' : ''}`}
          onClick={() => setActiveTab('runlab')}
        >
          <span className="icon">🧬</span>
          <span className="label">Run Lab</span>
        </button>
      </nav>

      <div className="sidebar-footer">
        <p>Elite Edition</p>
      </div>
    </aside>
  );
}
