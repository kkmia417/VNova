import type {
  JsonValue as GeneratedJsonValue,
  VNovaEventEnvelopeV1 as GeneratedEventEnvelope,
} from "./generated/event-envelope.v1.js";

type DeepReadonly<T> = T extends readonly (infer Item)[]
  ? readonly DeepReadonly<Item>[]
  : T extends object
    ? { readonly [Key in keyof T]: DeepReadonly<T[Key]> }
    : T;

export type JsonValue = DeepReadonly<GeneratedJsonValue>;
export type VNovaEventEnvelopeV1 = DeepReadonly<GeneratedEventEnvelope>;
