import React, { useState } from 'react';
import Dashboard from './components/Dashboard';
import RunLab from './components/RunLab';
import Sidebar from './components/Sidebar';

function App() {
  const [activeTab, setActiveTab] = useState('systemic');

  return (
    <div className="app-layout">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="main-content">
        {activeTab === 'systemic' && <Dashboard />}
        {activeTab === 'runlab' && <RunLab />}
      </main>
    </div>
  );
}

export default App;
