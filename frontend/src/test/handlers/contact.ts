import { http, HttpResponse } from 'msw'

export const trackedContactMessages: Record<string, unknown>[] = []
export function resetContactHandlers(): void { trackedContactMessages.length = 0 }

export const contactHandlers = [
  http.post('http://localhost:8000/api/contact/', async ({ request }) => {
    trackedContactMessages.push((await request.json()) as Record<string, unknown>)
    return HttpResponse.json({ id: trackedContactMessages.length, status: 'NEW' }, { status: 201 })
  }),
]
