import { describe, it, expect, vi, beforeEach } from 'vitest';
import { academicoService } from '../academico.service';
import { api } from '../../../../shared/services/api';

vi.mock('../../../../shared/services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  }
}));

describe('academico.service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('getUmbral should call the correct endpoint', async () => {
    const mockData = { umbral_pct: 70, valores_aprobatorios: ['Satisfactorio'] };
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockData });

    const result = await academicoService.getUmbral('M1');
    expect(api.get).toHaveBeenCalledWith('/calificaciones/umbral', { params: { materia_id: 'M1' } });
    expect(result).toEqual(mockData);
  });

  it('setUmbral should call the correct endpoint', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ data: { umbral_pct: 65 } });

    await academicoService.setUmbral('M1', 65);
    expect(api.post).toHaveBeenCalledWith('/calificaciones/umbral', { materia_id: 'M1', umbral_pct: 65 });
  });

  it('getAtrasados should call the correct endpoint with query params', async () => {
    const mockData = [{ padron_id: '123', nombre: 'Juan', apellido: 'Perez', actividad: 'TP1', motivo: 'Sin entrega' }];
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockData });

    const result = await academicoService.getAtrasados('M1', 'C1');
    expect(api.get).toHaveBeenCalledWith('/analisis/atrasados', { params: { materia_id: 'M1', cohorte_id: 'C1' } });
    expect(result).toEqual(mockData);
  });

  it('getRanking should call the correct endpoint with query params', async () => {
    const mockData = [{ padron_id: '123', actividades_aprobadas: 3 }];
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockData });

    const result = await academicoService.getRanking('M1', 'C1');
    expect(api.get).toHaveBeenCalledWith('/analisis/ranking', { params: { materia_id: 'M1', cohorte_id: 'C1' } });
    expect(result).toEqual(mockData);
  });

  it('getMonitor should require materia/cohorte and pass filters', async () => {
    const mockData = [{ padron_id: '123', actividad: 'TP1', estado: 'Aprobado' }];
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockData });

    const result = await academicoService.getMonitor('M1', 'C1', { search: 'juan' });
    expect(api.get).toHaveBeenCalledWith('/analisis/monitor', {
      params: { materia_id: 'M1', cohorte_id: 'C1', search: 'juan' }
    });
    expect(result).toEqual(mockData);
  });

  it('importarCalificaciones should post multipart form with materia/cohorte/file', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ data: { imported_count: 10, unmatched_emails: [] } });

    const mockFile = new File(['csv data'], 'notas.csv', { type: 'text/csv' });
    const result = await academicoService.importarCalificaciones('M1', 'C1', mockFile);

    expect(api.post).toHaveBeenCalledWith(
      '/calificaciones/import-csv',
      expect.any(FormData),
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    const formData = vi.mocked(api.post).mock.calls[0][1] as FormData;
    expect(formData.get('materia_id')).toBe('M1');
    expect(formData.get('cohorte_id')).toBe('C1');
    expect(result).toEqual({ imported_count: 10, unmatched_emails: [] });
  });

  it('detectarTrabajosSinCorregir should import completion report and then query pending TPs', async () => {
    const mockPendientes = [{ padron_id: '123', nombre: 'Juan', apellido: 'Perez', actividad: 'TP1', importado_at: null }];
    vi.mocked(api.post).mockResolvedValueOnce({ data: { imported_count: 5, unmatched_emails: [] } });
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockPendientes });

    const mockFile = new File(['csv data'], 'report.csv', { type: 'text/csv' });
    const result = await academicoService.detectarTrabajosSinCorregir('M1', 'C1', mockFile);

    expect(api.post).toHaveBeenCalledWith(
      '/calificaciones/import-completion-csv',
      expect.any(FormData),
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    expect(api.get).toHaveBeenCalledWith('/analisis/tps-sin-corregir', {
      params: { materia_id: 'M1', cohorte_id: 'C1' }
    });
    expect(result).toEqual(mockPendientes);
  });

  it('vaciarCalificaciones should post to the vaciar endpoint', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ data: { ok: true } });

    await academicoService.vaciarCalificaciones('M1', 'C1');
    expect(api.post).toHaveBeenCalledWith('/calificaciones/vaciar', { materia_id: 'M1', cohorte_id: 'C1' });
  });
});
