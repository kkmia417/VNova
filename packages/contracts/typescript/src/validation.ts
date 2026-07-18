import { Ajv2020, type AnySchema, type ErrorObject, type ValidateFunction } from "ajv/dist/2020.js";
import * as addFormatsNamespace from "ajv-formats";
import type { FormatsPlugin } from "ajv-formats";

import activeEventRegistryDocument from "./generated/active-event-registry.v1.json" with { type: "json" };
import eventEnvelopeSchema from "./generated/event-envelope.v1.schema.json" with { type: "json" };
import type { VNovaEventEnvelopeV1 } from "./types.js";

// ajv-formats is CommonJS with a typed default export. NodeNext exposes the
// runtime default correctly, while TypeScript models the namespace wrapper.
const addFormats = addFormatsNamespace.default as unknown as FormatsPlugin;

function createContractAjv(): Ajv2020 {
  const instance = new Ajv2020({
    allErrors: true,
    strict: true,
    validateFormats: true,
  });
  addFormats(instance);
  instance.addKeyword("x-vnova-extension-point");
  instance.addKeyword("x-vnova-json-profile");
  return instance;
}

const envelopeAjv = createContractAjv();

const maxPortableJsonNumber = Number.MAX_SAFE_INTEGER;
const maxContainerDepth = 64;
const maxJsonNodes = 10_000;
const maxUtf8StringBytes = 1_048_576;

interface JsonProfileState {
  readonly active: WeakSet<object>;
  nodes: number;
  utf8StringBytes: number;
}

function assertCanonicalJsonProfile(): void {
  const profile = eventEnvelopeSchema["x-vnova-json-profile"];
  if (
    profile.maxContainerDepth !== maxContainerDepth ||
    profile.maxNodes !== maxJsonNodes ||
    profile.maxUtf8StringBytes !== maxUtf8StringBytes ||
    !profile.normalizeNegativeZero ||
    !profile.requireUnicodeScalarStrings
  ) {
    throw new Error("Generated event schema has an unsupported VNova JSON profile");
  }
}

assertCanonicalJsonProfile();

const validateEventEnvelope: ValidateFunction<VNovaEventEnvelopeV1> =
  envelopeAjv.compile<VNovaEventEnvelopeV1>(eventEnvelopeSchema);

interface ActiveEventRegistry {
  readonly identities: ReadonlySet<string>;
  readonly validators: ReadonlyMap<string, ValidateFunction>;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function hasExactKeys(value: Record<string, unknown>, expected: readonly string[]): boolean {
  const actual = Object.keys(value).sort();
  const sortedExpected = [...expected].sort();
  return (
    actual.length === sortedExpected.length &&
    actual.every((key, index) => key === sortedExpected[index])
  );
}

function safeRegistryPath(value: unknown): string | undefined {
  if (typeof value !== "string" || value.length === 0 || value.includes("\\")) {
    return undefined;
  }
  const parts = value.split("/");
  if (
    value.startsWith("/") ||
    parts.some((part) => part.length === 0 || part === "." || part === "..")
  ) {
    return undefined;
  }
  return value;
}

function activeEventIdentity(eventType: string, schemaVersion: number): string {
  return `${eventType}\u0000${String(schemaVersion)}`;
}

let activeEventRegistryCache: ActiveEventRegistry | undefined;

/** @internal Builds fail-closed runtime authority from a generated registry document. */
export function buildActiveEventRegistry(rawRegistry: unknown): ActiveEventRegistry {
  if (
    !isRecord(rawRegistry) ||
    !hasExactKeys(rawRegistry, [
      "active_events",
      "catalog_source",
      "catalog_source_sha256",
      "catalog_version",
      "payload_schemas",
      "registry_version",
    ]) ||
    rawRegistry["registry_version"] !== 1 ||
    rawRegistry["catalog_version"] !== 1 ||
    rawRegistry["catalog_source"] !== "specs/events/event-catalog.v1.json" ||
    typeof rawRegistry["catalog_source_sha256"] !== "string" ||
    !/^[0-9a-f]{64}$/u.test(rawRegistry["catalog_source_sha256"]) ||
    !Array.isArray(rawRegistry["payload_schemas"]) ||
    !Array.isArray(rawRegistry["active_events"])
  ) {
    throw new TypeError("Generated active-event registry has an invalid header");
  }

  const payloadAjv = createContractAjv();
  const schemas = new Map<string, AnySchema>();
  const schemaIdentifiers = new Set<string>();
  for (const rawSchema of rawRegistry["payload_schemas"]) {
    if (
      !isRecord(rawSchema) ||
      !hasExactKeys(rawSchema, ["document", "path", "source_sha256"]) ||
      typeof rawSchema["source_sha256"] !== "string" ||
      !/^[0-9a-f]{64}$/u.test(rawSchema["source_sha256"]) ||
      !isRecord(rawSchema["document"])
    ) {
      throw new TypeError("Generated registry contains an invalid payload schema");
    }
    const path = safeRegistryPath(rawSchema["path"]);
    if (path === undefined || schemas.has(path)) {
      throw new TypeError("Generated registry payload schema path is invalid or duplicated");
    }
    const schemaIdentifier = rawSchema["document"]["$id"];
    if (
      typeof schemaIdentifier !== "string" ||
      schemaIdentifier.length === 0 ||
      schemaIdentifiers.has(schemaIdentifier)
    ) {
      throw new TypeError("Generated payload schema requires a unique non-empty $id");
    }
    schemaIdentifiers.add(schemaIdentifier);
    const document = rawSchema["document"] as AnySchema;
    schemas.set(path, document);
    payloadAjv.addSchema(document);
  }

  const identities = new Set<string>();
  const validators = new Map<string, ValidateFunction>();
  for (const rawEvent of rawRegistry["active_events"]) {
    if (
      !isRecord(rawEvent) ||
      !hasExactKeys(rawEvent, ["schema", "schema_version", "type"]) ||
      typeof rawEvent["type"] !== "string" ||
      rawEvent["type"].length === 0 ||
      typeof rawEvent["schema_version"] !== "number" ||
      !Number.isSafeInteger(rawEvent["schema_version"]) ||
      rawEvent["schema_version"] < 1
    ) {
      throw new TypeError("Generated registry contains an invalid active-event identity");
    }
    const schemaPath = safeRegistryPath(rawEvent["schema"]);
    const schema = schemaPath === undefined ? undefined : schemas.get(schemaPath);
    const identity = activeEventIdentity(rawEvent["type"], rawEvent["schema_version"]);
    if (schema === undefined || identities.has(identity)) {
      throw new TypeError("Generated active event lacks one exact payload schema");
    }
    identities.add(identity);
    validators.set(identity, payloadAjv.compile(schema));
  }
  if (validators.size !== identities.size) {
    throw new TypeError("Generated payload-validator registry is not exact");
  }

  return Object.freeze({ identities, validators });
}

function activeEventRegistry(): ActiveEventRegistry {
  activeEventRegistryCache ??= buildActiveEventRegistry(activeEventRegistryDocument);
  return activeEventRegistryCache;
}

function recordUnicodeScalarString(value: string, state: JsonProfileState): string {
  if (value.length > maxUtf8StringBytes - state.utf8StringBytes) {
    throw new TypeError("Contract strings exceed the UTF-8 byte budget");
  }
  for (let index = 0; index < value.length; index += 1) {
    const codeUnit = value.charCodeAt(index);
    let utf8Bytes: number;
    if (codeUnit >= 0xd800 && codeUnit <= 0xdbff) {
      const lowSurrogate = value.charCodeAt(index + 1);
      if (index + 1 >= value.length || lowSurrogate < 0xdc00 || lowSurrogate > 0xdfff) {
        throw new TypeError("Contract strings must contain only Unicode scalar values");
      }
      utf8Bytes = 4;
      index += 1;
    } else if (codeUnit >= 0xdc00 && codeUnit <= 0xdfff) {
      throw new TypeError("Contract strings must contain only Unicode scalar values");
    } else if (codeUnit <= 0x7f) {
      utf8Bytes = 1;
    } else if (codeUnit <= 0x7ff) {
      utf8Bytes = 2;
    } else {
      utf8Bytes = 3;
    }
    state.utf8StringBytes += utf8Bytes;
    if (state.utf8StringBytes > maxUtf8StringBytes) {
      throw new TypeError("Contract strings exceed the UTF-8 byte budget");
    }
  }
  return value;
}

function immutableJsonClone(value: unknown, state: JsonProfileState, depth: number): unknown {
  state.nodes += 1;
  if (state.nodes > maxJsonNodes) {
    throw new TypeError("Contract input exceeds the JSON node budget");
  }

  if (value === null || typeof value === "boolean") {
    return value;
  }
  if (typeof value === "string") {
    return recordUnicodeScalarString(value, state);
  }
  if (typeof value === "number") {
    if (!Number.isFinite(value) || Math.abs(value) > maxPortableJsonNumber) {
      throw new TypeError("Contract payload numbers must use the portable IEEE-754 range");
    }
    return Object.is(value, -0) ? 0 : value;
  }
  if (typeof value !== "object") {
    throw new TypeError("Contract values must use JSON-compatible types");
  }
  if (depth > maxContainerDepth) {
    throw new TypeError("Contract input exceeds the container-depth budget");
  }
  if (state.active.has(value)) {
    throw new TypeError("Contract payload cannot contain cycles");
  }
  state.active.add(value);
  try {
    if (Array.isArray(value)) {
      if (value.length > maxJsonNodes - state.nodes) {
        throw new TypeError("Contract input exceeds the JSON node budget");
      }
      const ownKeys = Reflect.ownKeys(value);
      if (ownKeys.length > maxJsonNodes - state.nodes + 1) {
        throw new TypeError("Contract input exceeds the JSON node budget");
      }
      if (ownKeys.some((key) => typeof key === "symbol") || ownKeys.length !== value.length + 1) {
        throw new TypeError("Contract arrays must be dense and cannot expose extra keys");
      }
      const clone: unknown[] = [];
      for (let index = 0; index < value.length; index += 1) {
        const descriptor = Object.getOwnPropertyDescriptor(value, String(index));
        if (descriptor?.enumerable !== true || !("value" in descriptor)) {
          throw new TypeError("Contract arrays cannot contain holes or accessor elements");
        }
        clone.push(immutableJsonClone(descriptor.value, state, depth + 1));
      }
      return Object.freeze(clone);
    }
    const prototype = Object.getPrototypeOf(value) as object | null;
    if (prototype !== Object.prototype && prototype !== null) {
      throw new TypeError("Contract objects must be plain JSON objects");
    }
    const ownKeys = Reflect.ownKeys(value);
    if (ownKeys.length > maxJsonNodes - state.nodes) {
      throw new TypeError("Contract input exceeds the JSON node budget");
    }
    const clone: Record<string, unknown> = Object.create(null) as Record<string, unknown>;
    for (const key of ownKeys) {
      if (typeof key === "symbol") {
        throw new TypeError("Contract objects cannot contain symbol keys");
      }
      const descriptor = Object.getOwnPropertyDescriptor(value, key);
      if (descriptor?.enumerable !== true || !("value" in descriptor)) {
        throw new TypeError("Contract objects cannot contain hidden or accessor properties");
      }
      const canonicalKey = recordUnicodeScalarString(key, state);
      Object.defineProperty(clone, canonicalKey, {
        configurable: false,
        enumerable: true,
        value: immutableJsonClone(descriptor.value, state, depth + 1),
        writable: false,
      });
    }
    return Object.freeze(clone);
  } finally {
    state.active.delete(value);
  }
}

function immutableClone(value: unknown): unknown {
  return immutableJsonClone(
    value,
    { active: new WeakSet<object>(), nodes: 0, utf8StringBytes: 0 },
    1,
  );
}

export class EventEnvelopeValidationError extends Error {
  public readonly code = "invalid_event_envelope";
  public readonly errors: readonly ErrorObject[];

  public constructor(errors: readonly ErrorObject[]) {
    super("Value is not a valid VNova event envelope");
    this.name = "EventEnvelopeValidationError";
    this.errors = errors;
  }
}

export class PublishableEventValidationError extends Error {
  public readonly code = "invalid_publishable_event";

  public constructor() {
    super("Value is not a publishable VNova event");
    this.name = "PublishableEventValidationError";
  }
}

export function isValidEventEnvelope(value: unknown): boolean {
  try {
    const clone = immutableClone(value);
    return validateEventEnvelope(clone);
  } catch {
    return false;
  }
}

export function assertValidEventEnvelope(value: unknown): VNovaEventEnvelopeV1 {
  let clone: unknown;
  try {
    clone = immutableClone(value);
  } catch {
    throw new EventEnvelopeValidationError([]);
  }

  try {
    if (!validateEventEnvelope(clone)) {
      throw new EventEnvelopeValidationError(validateEventEnvelope.errors ?? []);
    }
    return clone;
  } catch (error: unknown) {
    if (error instanceof EventEnvelopeValidationError) {
      throw error;
    }
    throw new EventEnvelopeValidationError([]);
  }
}

export function assertValidPublishableEvent(value: unknown): VNovaEventEnvelopeV1 {
  try {
    const envelope = assertValidEventEnvelope(value);
    const identity = activeEventIdentity(envelope.type, envelope.schema_version);
    const registry = activeEventRegistry();
    if (!registry.identities.has(identity)) {
      throw new TypeError("Event identity is not active");
    }
    const validatePayload = registry.validators.get(identity);
    if (!validatePayload?.(envelope.payload)) {
      throw new TypeError("Active event payload does not match its exact schema");
    }
    return envelope;
  } catch {
    throw new PublishableEventValidationError();
  }
}

export function isValidPublishableEvent(value: unknown): boolean {
  try {
    assertValidPublishableEvent(value);
    return true;
  } catch {
    return false;
  }
}
