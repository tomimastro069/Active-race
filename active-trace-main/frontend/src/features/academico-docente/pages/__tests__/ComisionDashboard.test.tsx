// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi } from 'vitest';
import { ComisionDashboard } from '../ComisionDashboard';
import { academicoService } from '../../services/academico.service';

vi.mock('../../services/academico.service', () => ({
  academicoService: {
    getUmbral: vi.fn(),
    getAtrasados: vi.fn(),
    getRanking: vi.fn(),
  }
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

describe('ComisionDashboard', () => {
  it('renders correctly with url params', async () => {
    vi.mocked(academicoService.getUmbral).mockResolvedValueOnce({ umbral_pct: 65 });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/comisiones/MAT1/COH1']}>
          <Routes>
            <Route path="/comisiones/:materiaId/:cohorteId" element={<ComisionDashboard />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    // Should display the commission headers
    expect(await screen.findByText(/Comisión MAT1 - Cohorte COH1/i)).toBeInTheDocument();
    
    // Default tab should be calificaciones
    expect(screen.getByText('calificaciones')).toBeInTheDocument();
    expect(screen.getByText('atrasados')).toBeInTheDocument();
    expect(screen.getByText('comunicaciones')).toBeInTheDocument();
  });
});
