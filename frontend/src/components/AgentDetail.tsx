import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api, Agent, FileListResponse } from '../api/client';

export function AgentDetail() {
  const { id } = useParams<{ id: string }>();
  const agentId = Number(id);
  const [agent, setAgent] = useState<Agent | null>(null);
  const [files, setFiles] = useState<FileListResponse['files']>([]);
  const [fileContent, setFileContent] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const fetchAgent = async () => {
    try {
      setLoading(true);
      const data = await api.agents.get(agentId);
      setAgent(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load agent');
    } finally {
      setLoading(false);
    }
  };

  const fetchFiles = async (path = '') => {
    try {
      const response = await api.agents.files.list(agentId, path);
      setFiles(response.files);
    } catch (err) {
      setFileError(err instanceof Error ? err.message : 'Failed to load files');
    }
  };

  const fetchFileContent = async (path: string) => {
    try {
      setFileError(null);
      const response = await api.agents.files.read(agentId, path);
      setFileContent(response.content);
      setSelectedFile(path);
    } catch (err) {
      setFileError(err instanceof Error ? err.message : 'Failed to read file');
    }
  };

  const saveFile = async (path: string, content: string) => {
    try {
      setSaving(true);
      setFileError(null);
      await api.agents.files.write(agentId, { path, content });
      setFileContent(content);
      await fetchFiles(); // Refresh file list
    } catch (err) {
      setFileError(err instanceof Error ? err.message : 'Failed to save file');
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => {
    fetchAgent();
    fetchFiles();
  }, [agentId]);

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner" />
      </div>
    );
  }

  if (error || !agent) {
    return (
      <div className="error-message">
        {error || 'Agent not found'}
        <Link to="/agents" className="btn btn-secondary" style={{ marginLeft: '1rem' }}>
          Back to Agents
        </Link>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">{agent.name}</h1>
          <p style={{ color: '#6b7280', marginTop: '0.25rem' }}>
            Workspace: <code>{agent.workspace_path}</code>
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <Link to={`/agents/${agent.id}/edit`} className="btn btn-secondary">
            Edit
          </Link>
          <Link to="/agents" className="btn btn-secondary">
            Back
          </Link>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '1.5rem' }}>
        <div className="card">
          <h3 style={{ marginBottom: '1rem' }}>Files</h3>
          {fileError && <div className="error-message">{fileError}</div>}
          <div style={{ maxHeight: '60vh', overflowY: 'auto' }}>
            {files.length === 0 ? (
              <div className="empty-state" style={{ padding: '1.5rem' }}>
                <p>No files in workspace</p>
              </div>
            ) : (
              <ul style={{ listStyle: 'none' }}>
                {files.map(file => (
                  <li
                    key={file.path}
                    style={{
                      padding: '0.5rem',
                      borderBottom: '1px solid #e5e7eb',
                      cursor: 'pointer',
                      backgroundColor: selectedFile === file.path ? '#eff6ff' : 'transparent',
                    }}
                    onClick={() => {
                      if (file.is_dir) {
                        fetchFiles(file.path);
                      } else {
                        fetchFileContent(file.path);
                      }
                    }}
                  >
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      {file.is_dir ? (
                        <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M10 4H4a2 2 0 00-2 2v12a2 2 0 002 2h16a2 2 0 002-2V8a2 2 0 00-2-2h-8l-2-2z" />
                        </svg>
                      ) : (
                        <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                        </svg>
                      )}
                      {file.name}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div className="card" style={{ minHeight: '400px', display: 'flex', flexDirection: 'column' }}>
          {selectedFile ? (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '1rem' }}>{selectedFile}</h3>
                <button
                  className="btn btn-primary btn-sm"
                  onClick={() => saveFile(selectedFile, fileContent)}
                  disabled={saving}
                >
                  {saving ? 'Saving...' : 'Save'}
                </button>
              </div>
              <textarea
                className="form-input"
                style={{
                  flex: 1,
                  fontFamily: 'monospace',
                  fontSize: '0.875rem',
                  lineHeight: 1.6,
                  minHeight: '350px',
                  resize: 'none',
                }}
                value={fileContent}
                onChange={e => setFileContent(e.target.value)}
                placeholder="Select a file to view/edit..."
                readOnly={!selectedFile}
              />
            </>
          ) : (
            <div className="empty-state" style={{ flex: 1 }}>
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5A2.25 2.25 0 000 6.75v10.5A2.25 2.25 0 002.25 19.5h10.5A2.25 2.25 0 0015 17.25V6.75A2.25 2.25 0 0012.75 4.5M3.75 3h13.5M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <p>Select a file to view or edit</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}