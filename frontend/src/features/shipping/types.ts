import type { components } from '@/api/schema.d.ts'

type SnakeToCamel<Value extends string> =
  Value extends `${infer Prefix}_${infer Suffix}`
    ? `${Prefix}${Capitalize<SnakeToCamel<Suffix>>}`
    : Value

type CamelCaseProperties<Value> = Value extends readonly (infer Item)[]
  ? CamelCaseProperties<Item>[]
  : Value extends object
    ? {
        [Key in keyof Value as Key extends string
          ? SnakeToCamel<Key>
          : Key]: CamelCaseProperties<Value[Key]>
      }
    : Value

export type Region = Omit<
  CamelCaseProperties<components['schemas']['Region']>,
  'comunas'
>
export type Comuna = CamelCaseProperties<components['schemas']['Comuna']>
export type DispatchOptions = CamelCaseProperties<
  components['schemas']['DispatchOptions']
>
