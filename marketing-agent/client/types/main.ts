import { z } from "zod";
import { Resource } from "./resource";

export enum ModelProviders {
  cerebras = "cerebras",
  fireworks = "fireworks",
  groq = "groq",
  together = "together"
}

// Message schemas
export const GenerateRequestSchema = z.object({
  product_description: z.string(),
  provider: z.nativeEnum(ModelProviders)
});

export const GenerateResponseSchema = z.object({
  job_id: z.string()
});

export const StatusUpdateMessageSchema = z.object({
  type: z.literal("status_update"),
  data: z.object({
    status: z.string(),
    message: z.string()
  })
});

export const ResourceCreatedMessageSchema = z.object({
  type: z.literal("resource_created"),
  data: z.custom<Resource>()
});

export const ErrorMessageSchema = z.object({
  type: z.literal("error"),
  data: z.object({
    message: z.string()
  })
});

export const CompletedMessageSchema = z.object({
  type: z.literal("completed"),
  data: z.null()
});

export const WebSocketMessageSchema = z.discriminatedUnion("type", [
  StatusUpdateMessageSchema,
  ResourceCreatedMessageSchema,
  ErrorMessageSchema,
  CompletedMessageSchema
]);

// Inferred types
export type GenerateRequest = z.infer<typeof GenerateRequestSchema>;
export type GenerateResponse = z.infer<typeof GenerateResponseSchema>;
export type StatusUpdateMessage = z.infer<typeof StatusUpdateMessageSchema>;
export type ResourceCreatedMessage = z.infer<
  typeof ResourceCreatedMessageSchema
>;
export type ErrorMessage = z.infer<typeof ErrorMessageSchema>;
export type WebSocketMessage = z.infer<typeof WebSocketMessageSchema>;
