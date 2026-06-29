export interface paths {
  '/api/auth/login/': {
    post: {
      requestBody: {
        content: {
          'application/json': {
            email: string
            password: string
          }
        }
      }
      responses: {
        200: {
          content: {
            'application/json': {
              detail: string
            }
          }
        }
        400: {
          content: {
            'application/json': {
              detail: string
            }
          }
        }
        401: {
          content: {
            'application/json': {
              detail: string
            }
          }
        }
      }
    }
  }
}

export type webhooks = Record<string, never>
export interface components {}
export type $defs = Record<string, never>
export interface operations {}
