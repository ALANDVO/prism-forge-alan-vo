import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, Agent } from '../api/client';

export function AgentList() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const fetchAgents = async () => {
    try {
      setLoading(true);
      const response = await api.agents.list();
      setAgents(response.agents);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load agents');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgents();
  }, []);

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this agent?')) return;

    try {
      await api.agents.delete(id);
      await fetchAgents();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete agent');
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner" data-testid="loading-spinner" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-message">
        {error}
        <button className="btn btn-secondary btn-sm" style={{ marginLeft: '1rem' }} onClick={fetchAgents}>
          Retry
        </button>
      </div>
    );
  }

  if (agents.length === 0) {
    return (
      <div className="card empty-state">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M18.75 6.75a9.071 9.071 0 01-2.439 5.598M3.75 15.597a9.071 9.071 0 002.439 5.598m11.322-11.202A9.071 9.071 0 0112 21.75m0-17.25a9.071 9.071 0 00-9.071 9.071m18.142 0a9.071 9.071 0 01-9.071 9.071M12 15.75a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
        </svg>
        <h3>No agents yet</h3>
        <p>Create your first agent to get started.</p>
        <Link to="/agents/new" className="btn btn-primary" style={{ marginTop: '1rem' }}>
          Create Agent
        </Link>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="page-header">
        <h2 className="page-title">Agents</h2>
        <Link to="/agents/new" className="btn btn-primary">
          Create Agent
        </Link>
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Workspace</th>
              <th>Description</th>
              <th>Status</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {agents.map(agent => (
              <tr key={agent.id}>
                <td>
                  <Link to={`/agents/${agent.id}`} className="nav-link">
                    {agent.name}
                  </Link>
                </td>
                <td><code>{agent.workspace_path}</code></td>
                <td>{agent.description || '-'}</td>
                <td>
                  <span className={`badge ${agent.is_active ? 'badge-success' : 'badge-secondary'}`}>
                    {agent.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td>{new Date(agent.created_at).toLocaleDateString()}</td>
                <td>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <Link to={`/agents/${agent.id}/edit`} className="btn btn-secondary btn-sm">
                      Edit
                    </Link>
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={() => handleDelete(agent.id)}
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}