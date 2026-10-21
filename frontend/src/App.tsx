import { AgentList } from './components/AgentList';
import { AgentForm } from './components/AgentForm';
import { AgentDetail } from './components/AgentDetail';
import { Routes, Route, useParams } from 'react-router-dom';
import './index.css';

function EditAgentForm() {
  const { id } = useParams<{ id: string }>();
  return <AgentForm isEditing agentId={Number(id)} />;
}

function Dashboard() {
  return (
    <div className="container">
      <nav className="navbar">
        <div className="navbar-brand">Prism Forge</div>
        <div className="navbar-nav">
          <a href="/agents" className="nav-link">Agents</a>
          <a href="/agents/new" className="nav-link">Create Agent</a>
        </div>
      </nav>

      <main className="container" style={{ paddingTop: '1.5rem' }}>
        <Routes>
          <Route path="/agents" element={<AgentList />} />
          <Route path="/agents/new" element={<AgentForm />} />
          <Route path="/agents/:id" element={<AgentDetail />} />
          <Route path="/agents/:id/edit" element={<EditAgentForm />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return <Dashboard />;
}