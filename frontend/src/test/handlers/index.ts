import { authHandlers } from './auth'
import { catalogHandlers } from './catalog'

export const handlers = [...authHandlers, ...catalogHandlers]
