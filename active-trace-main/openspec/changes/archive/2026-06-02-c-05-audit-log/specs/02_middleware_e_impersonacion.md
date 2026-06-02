# Especificación 02: Middleware e Impersonación (C-05)

## 1. Responsabilidad
Detallar la implementación del servicio de auditoría para registro estandarizado y el flujo completo de autenticación bajo impersonación.

## 2. Extensión del JWT
La función generadora de JWT (`create_access_token`) debe soportar inyectar el claim `impersonated_sub`.
```json
{
  "sub": "uuid-actor-real",
  "impersonated_sub": "uuid-usuario-suplantado",
  "exp": 1234567890
}
```

## 3. Adaptación del Dependency get_current_user
La dependencia de FastAPI `get_current_user` debe:
1. Extraer ambos IDs del payload del JWT.
2. Si `impersonated_sub` no está presente, flujo normal.
3. Si está presente, recuperar el usuario correspondiente al `impersonated_sub` para que las reglas de negocio del sistema lo asuman como el emisor de la request.
4. Adosar el `actor_id` (el real) en `request.state` o en un envoltorio DTO para que el servicio de auditoría sepa a quién atribuir las acciones.

## 4. Endpoints de Soporte
Agregar a `routers/auth.py`:
- `POST /auth/impersonate`
  - Body: `{"usuario_id": "uuid-del-usuario-a-suplantar"}`
  - Dependency/Guard: `require_permission("impersonacion:usar")`
  - Acción: Emite el token extendido y genera una traza de auditoría `IMPERSONACION_INICIAR` indicando a quién se está suplantando.
