import { http, HttpResponse } from 'msw'

export const testUser = {
  id: 1,
  email: 'test@example.com',
  first_name: 'Test',
  last_name: 'User',
  rut: null,
  phone: null,
  is_admin: false,
}

export const authHandlers = [
  http.post('*api/auth/login/', () =>
    HttpResponse.json(
      {
        access: 'access-token',
        refresh: 'refresh-token',
        email: testUser.email,
        password: '',
      },
      { status: 200 },
    ),
  ),

  http.post('*api/auth/register/', () =>
    HttpResponse.json(
      { message: 'Usuario registrado con éxito de forma segura.' },
      { status: 201 },
    ),
  ),

  http.post('*api/auth/logout/', () =>
    HttpResponse.json(
      { message: 'Sesión cerrada correctamente.' },
      { status: 200 },
    ),
  ),

  http.get('*api/auth/me/', () => HttpResponse.json(testUser, { status: 200 })),
]
