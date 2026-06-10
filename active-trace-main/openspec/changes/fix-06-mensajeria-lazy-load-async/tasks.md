# Tasks: fix-06-mensajeria-lazy-load-async

## 1. Backend

- [x] 1.1 `create_thread`: devolver el hilo recargado con eager loading (miembros, mensajes,
      remitentes) usando el método existente del repository, con scope de tenant.
- [x] 1.2 `reply_to_thread`: cargar `remitente` del mensaje con `session.refresh(...,
      ["remitente"])` antes de devolverlo.

## 2. Verificación

- [x] 2.1 `pytest tests/test_c20_perfil_y_mensajeria.py` en verde.
- [x] 2.2 Suite completa en verde (181/181) contra Postgres real.
