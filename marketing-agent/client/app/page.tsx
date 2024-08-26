"use client";

import { useState } from "react";
import axios from "axios";
import { z } from "zod";
import ProductForm from "../components/ProductForm/ProductForm";
import ThinkingPanel from "../components/ThinkingPanel/ThinkingPanel";
import ResourcesPanel from "../components/ResourcesPanel/ResourcesPanel";
import ResourceModal from "../components/ResourceModal/ResourceModal";
import styles from "./Home.module.css";
import {
  GenerateRequestSchema,
  WebSocketMessageSchema,
  GenerateRequest,
  ResourceCreatedMessage,
  WebSocketMessage,
  GenerateResponseSchema,
  StatusUpdateMessage
} from "../types/main";

const baseURL = process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:8000";
type AppStage = "welcome" | "generating" | "completed";

export default function Home() {
  const [appStage, setAppStage] = useState<AppStage>("welcome");
  const [thoughts, setThoughts] = useState<string[]>([]);
  const [resources, setResources] = useState<any[]>([]);
  const [selectedResource, setSelectedResource] = useState<any>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleResourceClick = (resource: any) => {
    setSelectedResource(resource);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedResource(null);
  };

  const handleSubmit = async (request: GenerateRequest) => {
    try {
      const job_id = await initiateGeneration(request);
      setupWebSocket(job_id);
      setAppStage("generating");
    } catch (error) {
      console.error("Error submitting form:", error);
    }
  };

  const initiateGeneration = async (
    request: GenerateRequest
  ): Promise<string> => {
    try {
      const validatedRequest = GenerateRequestSchema.parse(request);
      const response = await axios.post(
        `${baseURL}/generate`,
        validatedRequest
      );
      const responseData = GenerateResponseSchema.parse(response.data);
      return responseData.job_id;
    } catch (error) {
      if (error instanceof z.ZodError) {
        console.error("Validation error:", error.errors);
        throw new Error("Invalid request or response format");
      }
      if (axios.isAxiosError(error)) {
        console.error("API error:", error.response?.data);
        throw new Error("API request failed");
      }
      throw error;
    }
  };

  const setupWebSocket = (job_id: string) => {
    const socket = new WebSocket(
      `${baseURL.replace(/^http/, "ws")}/status/${job_id}`
    );

    socket.onmessage = (event: MessageEvent) => {
      const data = JSON.parse(event.data);
      console.log(JSON.stringify(data));

      const parsedData = WebSocketMessageSchema.safeParse(data);
      if (!parsedData.success) {
        console.error("Invalid WebSocket message format", parsedData.error);
        return;
      }

      const message: WebSocketMessage = parsedData.data;

      switch (message.type) {
        case "status_update":
          if (message.data.status === "completed") {
            socket.close();
            break;
          }
          updateThoughts(message);
          break;
        case "resource_created":
          updateResources(message);
          break;
        case "error":
          console.error(`Error: ${message.data.message}`);
          break;
      }
    };
    socket.onclose = () => {
      console.log("WebSocket connection closed");
      setAppStage("completed");
    };
  };

  const updateThoughts = (message: WebSocketMessage) => {
    const data = (message as StatusUpdateMessage).data;
    setThoughts((prevThoughts) => [...prevThoughts, data.message]);
  };

  const updateResources = (message: WebSocketMessage) => {
    const data = (message as ResourceCreatedMessage).data;
    setResources((prevResources) => [
      ...prevResources,
      {
        title: data.title,
        content: data.content,
        metadata: data.metadata,
        resource_type: data.resource_type
      }
    ]);
  };

  return (
    <main className={styles.main}>
      <div className={styles.container}>
        <div className={styles.header}>
          <div>
            <h1 className={styles.title}>Marketing Agent</h1>
          </div>
          {appStage !== "welcome" && (
            <button
              className={styles.restartButton}
              onClick={() => {
                setAppStage("welcome");
                setThoughts([]);
                setResources([]);
              }}
            >
              <svg
                className={styles.restartIcon}
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M2 10C2 10 4.00498 7.26822 5.63384 5.63824C7.26269 4.00827 9.5136 3 12 3C16.9706 3 21 7.02944 21 12C21 16.9706 16.9706 21 12 21C7.89691 21 4.43511 18.2543 3.35177 14.5M2 10V4M2 10H8"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              Restart
            </button>
          )}
        </div>
        {appStage === "welcome" && <ProductForm onSubmit={handleSubmit} />}
        {appStage !== "welcome" && (
          <div className={styles.generatingContainer}>
            <ThinkingPanel
              thoughts={thoughts}
              isLoading={appStage === "generating"}
            />
            <ResourcesPanel
              resources={resources}
              onResourceClick={handleResourceClick}
              isLoading={appStage === "generating"}
            />
          </div>
        )}
      </div>

      {selectedResource && (
        <ResourceModal
          resource={selectedResource}
          isOpen={isModalOpen}
          onClose={closeModal}
        />
      )}
    </main>
  );
}
