import { describe, it, expect, vi, beforeEach } from 'vitest';
import { comunicacionesService } from '../comunicaciones.service';
import { api } from '../../../../shared/services/api';

vi.mock('../../../../shared/services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  }
}));

describe('comunicaciones.service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('previewMensaje should post templates and variables to /comunicaciones/preview', async () => {
    const payload = {
      asunto_template: 'Hola {{nombre}}',
      cuerpo_template: 'Te faltan: {{actividades_faltantes}}',
      variables: { nombre: 'Ana', actividades_faltantes: 'TP1' },
    };
    const mockData = { asunto_renderizado: 'Hola Ana', cuerpo_renderizado: 'Te faltan: TP1' };
    vi.mocked(api.post).mockResolvedValueOnce({ data: mockData });

    const result = await comunicacionesService.previewMensaje(payload);
    expect(api.post).toHaveBeenCalledWith('/comunicaciones/preview', payload);
    expect(result).toEqual(mockData);
  });

  it('enviarLote should enqueue destinatarios and return comunicaciones with lote_id', async () => {
    const payload = {
      asunto_template: 'a',
      cuerpo_template: 'b',
      destinatarios: [{ email: 'ana@mail.com', nombre: 'Ana', actividades_faltantes: '' }],
      materia_id: 'M1',
    };
    const mockData = [{ id: 'c1', lote_id: 'lote-123', estado: 'Pendiente' }];
    vi.mocked(api.post).mockResolvedValueOnce({ data: mockData });

    const result = await comunicacionesService.enviarLote(payload);
    expect(api.post).toHaveBeenCalledWith('/comunicaciones/', payload);
    expect(result).toEqual(mockData);
  });

  it('getLoteStatus should call /comunicaciones/lotes/{id} and return por_estado', async () => {
    const mockData = { lote_id: 'lote-123', total: 3, por_estado: { Enviado: 2, Pendiente: 1 } };
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockData });

    const result = await comunicacionesService.getLoteStatus('lote-123');
    expect(api.get).toHaveBeenCalledWith('/comunicaciones/lotes/lote-123');
    expect(result).toEqual(mockData);
  });
});
