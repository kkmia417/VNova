/* Generated from specs/events/event-envelope.v1.schema.json. Do not edit. */

/**
 * This interface was referenced by `VNovaEventEnvelopeV1`'s JSON-Schema
 * via the `definition` "JsonValue".
 */
export type JsonValue =
  | null
  | boolean
  | number
  | string
  | JsonValue[]
  | {
      [k: string]: JsonValue;
    };

/**
 * Base transport envelope. Payload validation additionally requires the event catalog entry selected by type and schema_version.
 */
export interface VNovaEventEnvelopeV1 {
  /**
   * Globally unique immutable event identifier.
   */
  event_id: string;
  /**
   * Event type registered in event-catalog.v1.json.
   */
  type: string;
  /**
   * Payload schema version scoped to the event type.
   */
  schema_version: number;
  stream_session_id: string;
  turn_id?: string;
  /**
   * Canonical UTC RFC 3339 timestamp: uppercase T/Z, no leap second, and either no fraction or exactly six fractional digits whose value is not all zero.
   */
  occurred_at: string;
  /**
   * Validated against the payload schema selected by (type, schema_version).
   */
  payload: {
    [k: string]: JsonValue;
  };
}
