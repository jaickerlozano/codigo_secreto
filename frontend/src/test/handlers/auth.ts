import { http, HttpResponse } from 'msw'

export const authHandlers = [
  http.post('/api/auth/login/', async () =>
    HttpResponse.json({ detail: 'Login successful' }, { status: 200 }),
  ),
]
