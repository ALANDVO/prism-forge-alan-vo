import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, AgentCreate, AgentUpdate } from '../api/client';

interface AgentFormProps {
  initialData?: AgentCreate | AgentUpdate;
  isEditing?: boolean;
  agentId?: number;
}

export function AgentForm({ initialData, isEditing = false, agentId }: AgentFormProps) {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [name, setName] = useState(initialData?.name || '');
  const [workspacePath, setWorkspacePath] = useState((initialData as AgentCreate)?.workspace_path || './');
  const [description, setDescription] = useState(initialData?.description || '');
  const [systemPrompt, setSystemPrompt] = useState(initialData?.system_prompt || '');
  const [modelConfig, setModelConfig] = useState(initialData?.model_config || '');
  const [isActive, setIsActive] = useState((initialData as AgentUpdate)?.is_active ?? true);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isEditing && agentId) {
        await api.agents.update(agentId, {
          name,
          description,
          system_prompt: systemPrompt,
          model_config: modelConfig,
          is_active: isActive,
        } as AgentUpdate);
      } else {
        await api.agents.create({
          name,
          workspace_path: workspacePath,
          description,
          system_prompt: systemPrompt,
          model_config: modelConfig,
        } as AgentCreate);
      }
      navigate('/agents');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save agent');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2 className="page-title">{isEditing ? 'Edit Agent' : 'Create Agent'}</h2>

      {error && <div className="error-message">{error}</div>}

      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="name" className="form-label">
              Name *
            </label>
            <input
              type="text"
              id="name"
              className="form-input"
              value={name}
              onChange={e => setName(e.target.value)}
              required
              placeholder="Enter agent name"
            />
          </div>

          <div className="form-group">
            <label htmlFor="workspace_path" className="form-label">
              Workspace Path *
            </label>
            <input
              type="text"
              id="workspace_path"
              className="form-input"
              value={workspacePath}
              onChange={e => setWorkspacePath(e.target.value)}
              required
              placeholder="./agent-name"
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="description" className="form-label">
            Description
          </label>
          <textarea
            id="description"
            className="form-input form-textarea"
            value={description}
            onChange={e => setDescription(e.target.value)}
            placeholder="Optional description"
          />
        </div>

        <div className="form-group">
          <label htmlFor="system_prompt" className="form-label">
            System Prompt
          </label>
          <textarea
            id="system_prompt"
            className="form-input form-textarea"
            value={systemPrompt}
            onChange={e => setSystemPrompt(e.target.value)}
            placeholder="Optional system prompt"
          />
        </div>

        <div className="form-group">
          <label htmlFor="model_config" className="form-label">
            Model Config (JSON)
          </label>
          <textarea
            id="model_config"
            className="form-input form-textarea"
            value={modelConfig}
            onChange={e => setModelConfig(e.target.value)}
            placeholder='{"model": "gpt-4", "temperature": 0.7}'
          />
        </div>

        {isEditing && (
          <div className="form-group">
            <label className="form-label">
              <input
                type="checkbox"
                checked={isActive}
                onChange={e => setIsActive(e.target.checked)}
              />
              Active
            </label>
          </div>
        )}

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Saving...' : isEditing ? 'Update Agent' : 'Create Agent'}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => navigate('/agents')}
            disabled={loading}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}