import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, cleanup, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AgentList } from '../src/components/AgentList';
import { api } from '../src/api/client';

vi.mock('../src/api/client', () => ({
  api: {
    agents: {
      list: vi.fn(),
      delete: vi.fn(),
    },
  },
}));

const mockAgents = [
  {
    id: 1,
    name: 'Agent 1',
    description: 'First agent',
    workspace_path: './agent1',
    system_prompt: null,
    model_config: null,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: 'Agent 2',
    description: 'Second agent',
    workspace_path: './agent2',
    system_prompt: null,
    model_config: null,
    is_active: false,
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
];

function renderWithRouter(ui: React.ReactElement) {
  return render(
    <MemoryRouter initialEntries={['/agents']}>
      {ui}
    </MemoryRouter>
  );
}

describe('AgentList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    cleanup();
  });

  it('renders loading state initially', async () => {
    api.agents.list.mockResolvedValue({ agents: [], total: 0 });

    renderWithRouter(<AgentList />);

    await waitFor(() => {
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    });
  });

  it('renders agent list when data loads', async () => {
    api.agents.list.mockResolvedValue({ agents: mockAgents, total: 2 });

    renderWithRouter(<AgentList />);

    await waitFor(() => {
      expect(screen.getByText('Agent 1')).toBeInTheDocument();
      expect(screen.getByText('Agent 2')).toBeInTheDocument();
    });
  });

  it('renders empty state when no agents', async () => {
    api.agents.list.mockResolvedValue({ agents: [], total: 0 });

    renderWithRouter(<AgentList />);

    await waitFor(() => {
      expect(screen.getByText('No agents yet')).toBeInTheDocument();
    });
  });

  it('shows error message on API failure', async () => {
    api.agents.list.mockRejectedValue(new Error('Network error'));

    renderWithRouter(<AgentList />);

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('calls delete API when delete button clicked', async () => {
    api.agents.list
      .mockResolvedValueOnce({ agents: mockAgents, total: 2 })
      .mockResolvedValueOnce({ agents: [mockAgents[1]], total: 1 });
    api.agents.delete.mockResolvedValue(undefined);

    renderWithRouter(<AgentList />);

    await waitFor(() => {
      expect(screen.getByText('Agent 1')).toBeInTheDocument();
    });

    // Mock confirm to return true
    vi.stubGlobal('confirm', vi.fn(() => true));

    const deleteButton = screen.getAllByText('Delete')[0];
    await act(async () => {
      fireEvent.click(deleteButton);
    });

    await waitFor(() => {
      expect(api.agents.delete).toHaveBeenCalledWith(1);
    });
  });
});