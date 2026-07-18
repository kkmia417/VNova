import { readFileSync, readdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import {
  EventEnvelopeValidationError,
  PublishableEventValidationError,
  assertValidEventEnvelope,
  assertValidPublishableEvent,
  buildActiveEventRegistry,
  isValidEventEnvelope,
  isValidPublishableEvent,
} from "./validation.js";

const packageDirectory = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const fixtureRoot = resolve(packageDirectory, "../../../tests/contracts/fixtures/envelope");
const maxContainerDepth = 64;
const maxJsonNodes = 10_000;
const maxUtf8StringBytes = 1_048_576;

function fixtureNames(kind: "valid" | "invalid"): string[] {
  return readdirSync(resolve(fixtureRoot, kind))
    .filter((name) => name.endsWith(".json"))
    .sort();
}

function loadFixture(kind: "valid" | "invalid", name: string): unknown {
  return JSON.parse(readFileSync(resolve(fixtureRoot, kind, name), "utf8")) as unknown;
}

function expectRejectedByPublicValidation(value: unknown): void {
  expect(isValidEventEnvelope(value)).toBe(false);
  expect(() => {
    assertValidEventEnvelope(value);
  }).toThrow(EventEnvelopeValidationError);
}

function expectAcceptedByPublicValidation(value: unknown): void {
  expect(isValidEventEnvelope(value)).toBe(true);
  expect(() => {
    assertValidEventEnvelope(value);
  }).not.toThrow();
}

function nestedArrays(depth: number): unknown {
  let value: unknown = "leaf";
  for (let index = 0; index < depth; index += 1) {
    value = [value];
  }
  return value;
}

function envelopeWithContainerDepth(depth: number): Record<string, unknown> {
  const value = loadFixture("valid", "minimal.json") as Record<string, unknown>;
  value["payload"] = { nested: nestedArrays(depth - 2) };
  return value;
}

function jsonNodeCount(value: unknown): number {
  if (Array.isArray(value)) {
    let nodes = 1;
    for (const child of value) {
      nodes += jsonNodeCount(child);
    }
    return nodes;
  }
  if (value !== null && typeof value === "object") {
    let nodes = 1;
    for (const child of Object.values(value as Record<string, unknown>)) {
      nodes += jsonNodeCount(child);
    }
    return nodes;
  }
  return 1;
}

function envelopeWithJsonNodeCount(nodes: number): Record<string, unknown> {
  const value = loadFixture("valid", "minimal.json") as Record<string, unknown>;
  const payload: { values: number[] } = { values: [] };
  value["payload"] = payload;
  const fixedNodes = jsonNodeCount(value);
  payload.values = Array.from({ length: nodes - fixedNodes }, (_, index) => index);
  expect(jsonNodeCount(value)).toBe(nodes);
  return value;
}

function utf8StringAndKeyBytes(value: unknown): number {
  if (typeof value === "string") {
    return Buffer.byteLength(value, "utf8");
  }
  if (Array.isArray(value)) {
    let bytes = 0;
    for (const child of value as unknown[]) {
      bytes += utf8StringAndKeyBytes(child);
    }
    return bytes;
  }
  if (value !== null && typeof value === "object") {
    let bytes = 0;
    for (const [key, child] of Object.entries(value as Record<string, unknown>)) {
      bytes += Buffer.byteLength(key, "utf8") + utf8StringAndKeyBytes(child);
    }
    return bytes;
  }
  return 0;
}

function envelopeWithUtf8StringBytes(stringBytes: number): Record<string, unknown> {
  const value = loadFixture("valid", "minimal.json") as Record<string, unknown>;
  const payload = { text: "" };
  value["payload"] = payload;
  const fixedBytes = utf8StringAndKeyBytes(value);
  payload.text = "a".repeat(stringBytes - fixedBytes);
  expect(utf8StringAndKeyBytes(value)).toBe(stringBytes);
  return value;
}

function payloadSchema(path: string, schemaId?: string): Record<string, unknown> {
  const document: Record<string, unknown> = {
    $schema: "https://json-schema.org/draft/2020-12/schema",
    additionalProperties: false,
    properties: { mode: { type: "string" } },
    required: ["mode"],
    type: "object",
  };
  if (schemaId !== undefined) {
    document["$id"] = schemaId;
  }
  return {
    document,
    path,
    source_sha256: "0".repeat(64),
  };
}

function activeRegistry(
  schemaVersion: number,
  schemas: readonly Record<string, unknown>[],
): Record<string, unknown> {
  return {
    active_events: [
      {
        schema: "payloads/mode.schema.json",
        schema_version: schemaVersion,
        type: "ModeChanged",
      },
    ],
    catalog_source: "specs/events/event-catalog.v1.json",
    catalog_source_sha256: "0".repeat(64),
    catalog_version: 1,
    payload_schemas: schemas,
    registry_version: 1,
  };
}

describe("generated active-event authority", () => {
  it.each([0, -1, 1.5, Number.MAX_SAFE_INTEGER + 1])(
    "rejects non-portable schema version %s",
    (schemaVersion) => {
      const registry = activeRegistry(schemaVersion, [
        payloadSchema("payloads/mode.schema.json", "urn:vnova:test:mode:1"),
      ]);

      expect(() => buildActiveEventRegistry(registry)).toThrow(TypeError);
    },
  );

  it.each([undefined, ""])("rejects payload schema $id %s", (schemaId) => {
    const registry = activeRegistry(schemaId === undefined ? 1 : 2, [
      payloadSchema("payloads/mode.schema.json", schemaId),
    ]);

    expect(() => buildActiveEventRegistry(registry)).toThrow(
      "Generated payload schema requires a unique non-empty $id",
    );
  });

  it("rejects duplicate payload schema identifiers", () => {
    const duplicateId = "urn:vnova:test:duplicate";
    const registry = activeRegistry(1, [
      payloadSchema("payloads/mode.schema.json", duplicateId),
      payloadSchema("payloads/shared.schema.json", duplicateId),
    ]);

    expect(() => buildActiveEventRegistry(registry)).toThrow(
      "Generated payload schema requires a unique non-empty $id",
    );
  });

  it("constructs the validator selected by the exact active identity", () => {
    const registry = activeRegistry(1, [
      payloadSchema("payloads/mode.schema.json", "urn:vnova:test:mode:1"),
    ]);

    const authority = buildActiveEventRegistry(registry);
    const validator = authority.validators.get("ModeChanged\u00001");

    expect(authority.identities).toEqual(new Set(["ModeChanged\u00001"]));
    expect(validator?.({ mode: "supervised" })).toBe(true);
    expect(validator?.({ mode: 1 })).toBe(false);
  });
});

describe("event envelope contract parity", () => {
  for (const name of fixtureNames("valid")) {
    it(`accepts ${name}`, () => {
      const value = loadFixture("valid", name);
      expect(isValidEventEnvelope(value)).toBe(true);
      const validated = assertValidEventEnvelope(value);
      const roundTrip = JSON.parse(JSON.stringify(validated)) as unknown;
      expect(isValidEventEnvelope(roundTrip)).toBe(true);
      expect(assertValidEventEnvelope(roundTrip)).toEqual(validated);
    });
  }

  for (const name of fixtureNames("invalid")) {
    it(`rejects ${name}`, () => {
      const value = loadFixture("invalid", name);
      expect(isValidEventEnvelope(value)).toBe(false);
      expect(() => {
        assertValidEventEnvelope(value);
      }).toThrow(EventEnvelopeValidationError);
      try {
        assertValidEventEnvelope(value);
      } catch (error: unknown) {
        expect(error).toMatchObject({ code: "invalid_event_envelope" });
      }
    });
  }

  for (const name of fixtureNames("valid")) {
    it(`does not treat envelope-valid ${name} as publishable authority`, () => {
      const value = loadFixture("valid", name);

      expect(isValidEventEnvelope(value)).toBe(true);
      expect(isValidPublishableEvent(value)).toBe(false);
      expect(() => {
        assertValidPublishableEvent(value);
      }).toThrow(PublishableEventValidationError);
      try {
        assertValidPublishableEvent(value);
      } catch (error: unknown) {
        expect(error).toMatchObject({ code: "invalid_publishable_event" });
      }
    });
  }

  it("normalizes invalid envelopes at the publishable-event boundary", () => {
    const value = loadFixture("invalid", "missing-event-id.json");

    expect(isValidPublishableEvent(value)).toBe(false);
    expect(() => {
      assertValidPublishableEvent(value);
    }).toThrow(PublishableEventValidationError);
  });

  for (const testCase of [
    {
      fieldName: "event_id",
      label: "UUID object",
      value: { value: "018f47df-7c09-7b1a-83b5-57f0d6e15f3f" },
    },
    {
      fieldName: "turn_id",
      label: "explicit null optional UUID",
      value: null,
    },
    {
      fieldName: "stream_session_id",
      label: "uppercase stream-session UUID",
      value: "018F47DF-7C09-7B1A-83B5-57F0D6E15F40",
    },
    {
      fieldName: "turn_id",
      label: "URN turn UUID",
      value: "urn:uuid:018f47df-7c09-7b1a-83b5-57f0d6e15f42",
    },
    {
      fieldName: "schema_version",
      label: "boolean schema version",
      value: true,
    },
    {
      fieldName: "type",
      label: "binary event type",
      value: new Uint8Array([77, 111, 100, 101]),
    },
    {
      fieldName: "occurred_at",
      label: "numeric timestamp",
      value: 0,
    },
  ] as const) {
    it(`rejects a ${testCase.label}`, () => {
      const value = loadFixture("valid", "minimal.json") as Record<string, unknown>;
      value[testCase.fieldName] = testCase.value;

      expectRejectedByPublicValidation(value);
    });
  }

  it("preserves canonical six-digit microseconds and valid astral Unicode", () => {
    const timestamp = assertValidEventEnvelope(loadFixture("valid", "microsecond-time.json"));
    const unicode = assertValidEventEnvelope(loadFixture("valid", "emoji.json"));

    expect(timestamp.occurred_at).toBe("2026-07-17T00:00:00.010000Z");
    expect(unicode.payload["emoji"]).toBe("😀");
  });

  it("normalizes negative zero to positive zero", () => {
    const validated = assertValidEventEnvelope(loadFixture("valid", "negative-zero.json"));
    const normalized = validated.payload["negative_zero"];

    expect(normalized).toBe(0);
    expect(Object.is(normalized, -0)).toBe(false);
  });

  it("treats the container-depth budget as inclusive", () => {
    expectAcceptedByPublicValidation(envelopeWithContainerDepth(maxContainerDepth));
    expectRejectedByPublicValidation(envelopeWithContainerDepth(maxContainerDepth + 1));
  });

  it("treats the JSON-node budget as inclusive", () => {
    expectAcceptedByPublicValidation(envelopeWithJsonNodeCount(maxJsonNodes));
    expectRejectedByPublicValidation(envelopeWithJsonNodeCount(maxJsonNodes + 1));
  });

  it("treats the UTF-8 string budget as inclusive", () => {
    expectAcceptedByPublicValidation(envelopeWithUtf8StringBytes(maxUtf8StringBytes));
    expectRejectedByPublicValidation(envelopeWithUtf8StringBytes(maxUtf8StringBytes + 1));
  });

  it("counts object keys toward the total UTF-8 string budget", () => {
    const value = loadFixture("valid", "minimal.json") as Record<string, unknown>;
    const longKey = "k".repeat(maxUtf8StringBytes / 2);
    value["payload"] = {
      [longKey]: "v".repeat(maxUtf8StringBytes / 2 + 1),
    };

    expectRejectedByPublicValidation(value);
  });

  it("measures contract strings in UTF-8 bytes", () => {
    const value = loadFixture("valid", "minimal.json") as Record<string, unknown>;
    value["payload"] = {
      text: "😀".repeat(maxUtf8StringBytes / 4 + 1),
    };

    expectRejectedByPublicValidation(value);
  });

  it("returns a detached, deeply immutable value", () => {
    const value = loadFixture("valid", "minimal.json") as {
      payload: Record<string, unknown>;
    };
    value.payload = { nested: { items: [{ name: "before" }] } };

    const validated = assertValidEventEnvelope(value);
    value.payload["nested"] = "changed";

    expect(validated.payload).toEqual({ nested: { items: [{ name: "before" }] } });
    expect(Object.isFrozen(validated)).toBe(true);
    expect(Object.isFrozen(validated.payload)).toBe(true);
    expect(() => {
      (validated.payload as Record<string, unknown>)["newValue"] = true;
    }).toThrow(TypeError);
  });

  it("rejects non-JSON values and cycles", () => {
    const base = loadFixture("valid", "minimal.json") as {
      payload: Record<string, unknown>;
    };
    expect(isValidEventEnvelope({ ...base, payload: { fn: () => 1 } })).toBe(false);
    expect(isValidEventEnvelope({ ...base, payload: { nan: Number.NaN } })).toBe(false);
    expect(isValidEventEnvelope({ ...base, payload: { date: new Date() } })).toBe(false);
    expect(isValidEventEnvelope({ ...base, payload: { map: new Map() } })).toBe(false);

    const cyclic: Record<string, unknown> = {};
    cyclic["self"] = cyclic;
    expect(isValidEventEnvelope({ ...base, payload: cyclic })).toBe(false);
    expect(() => assertValidEventEnvelope({ ...base, payload: cyclic })).toThrow(
      EventEnvelopeValidationError,
    );
  });

  it.each(["payload", "nested payload"] as const)(
    "rejects a %s getter without executing it",
    (getterLocation) => {
      const value = loadFixture("valid", "minimal.json") as {
        payload: Record<string, unknown>;
      };
      let getterExecutions = 0;
      const getter = (): never => {
        getterExecutions += 1;
        throw new Error("Untrusted contract getters must never execute");
      };

      if (getterLocation === "payload") {
        Object.defineProperty(value, "payload", {
          configurable: true,
          enumerable: true,
          get: getter,
        });
      } else {
        Object.defineProperty(value.payload, "nested", {
          configurable: true,
          enumerable: true,
          get: getter,
        });
      }

      expect(isValidEventEnvelope(value)).toBe(false);
      expect(getterExecutions).toBe(0);

      let validationError: unknown;
      try {
        assertValidEventEnvelope(value);
      } catch (error: unknown) {
        validationError = error;
      }

      expect(validationError).toBeInstanceOf(EventEnvelopeValidationError);
      expect(validationError).toMatchObject({
        code: "invalid_event_envelope",
        errors: [],
      });
      expect(getterExecutions).toBe(0);
    },
  );

  it("inspects a Proxy snapshot before AJV can read mutable source properties", () => {
    const target = loadFixture("valid", "minimal.json") as Record<string, unknown>;
    let propertyReads = 0;
    const value = new Proxy(target, {
      get(object, property, receiver): unknown {
        propertyReads += 1;
        return Reflect.get(object, property, receiver) as unknown;
      },
      getOwnPropertyDescriptor(object, property) {
        const descriptor = Reflect.getOwnPropertyDescriptor(object, property);
        if (property === "payload" && descriptor !== undefined) {
          return {
            ...descriptor,
            value: { invalid: () => "not JSON" },
          };
        }
        return descriptor;
      },
    });

    expect(isValidEventEnvelope(value)).toBe(false);
    expect(propertyReads).toBe(0);
    expect(() => assertValidEventEnvelope(value)).toThrow(EventEnvelopeValidationError);
    expect(propertyReads).toBe(0);
  });
});
