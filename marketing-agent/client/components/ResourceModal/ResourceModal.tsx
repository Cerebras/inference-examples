import React, { useEffect, useRef, useState } from "react";
import styles from "./ResourceModal.module.css";
import { Resource } from "../../types/resource";
import Image from "next/image";
import ReactMarkdown from "react-markdown";
import { getResourceIcon } from "../ResourcesPanel/ResourcesPanel";
import { LinkedinShareButton, TwitterShareButton } from "next-share";

interface ResourceModalProps {
  resource: Resource;
  isOpen: boolean;
  onClose: () => void;
}

const ResourceModal: React.FC<ResourceModalProps> = ({
  resource,
  isOpen,
  onClose
}) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const [isCopied, setIsCopied] = useState(false);

  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };

    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "unset";
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === modalRef.current) onClose();
  };

  const handleCopy = () => {
    if (resource) {
      const formattedContent = `${resource.title}\n\n${resource.content}`;
      navigator.clipboard
        .writeText(formattedContent)
        .then(() => {
          setIsCopied(true);
          setTimeout(() => setIsCopied(false), 2000); // Reset after 2 seconds
        })
        .catch((err) => console.error("Failed to copy content: ", err));
    }
  };

  const handleShare = () => {
    if (resource && resource.resource_type === "LinkedInPost") {
      const text = encodeURIComponent(resource.content);
      const url = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(window.location.href)}&title=${encodeURIComponent(resource.title)}&summary=${text}`;
      window.open(url, "_blank", "width=570,height=570");
    }
  };

  return (
    <div
      className={styles.modalOverlay}
      ref={modalRef}
      onClick={handleOverlayClick}
    >
      <div className={styles.modalContent}>
        {resource && (
          <>
            <div className={styles.header}>
              <div className={styles.resourceHeader}>
                <div className={styles.resourceImageWrapper}>
                  <Image
                    src={getResourceIcon(resource.resource_type)}
                    alt={resource.resource_type}
                    width={16}
                    height={16}
                    className={styles.resourceImage}
                  />
                  <span>{resource.resource_type}</span>
                </div>
                <p className={styles.resourceTitle}>{resource.title}</p>
              </div>

              <button onClick={onClose} className={styles.closeButton}>
                ✕
              </button>
            </div>
            <div className={styles.contentWrapper}>
              <ReactMarkdown className={styles.markdownContent}>
                {resource.content}
              </ReactMarkdown>
            </div>
            <div className={styles.actions}>
              <button
                onClick={handleCopy}
                className={`${styles.copyButton} ${isCopied ? styles.copied : ""}`}
              >
                {isCopied ? "Copied!" : "Copy text"}
              </button>

              {resource.resource_type === "LinkedInPost" && (
                <div className={styles.shareButton}>
                  <LinkedinShareButton
                    url={window.location.href}
                    title={resource.title}
                    summary={resource.content}
                  >
                    Share to LinkedIn
                  </LinkedinShareButton>
                </div>
              )}
              {resource.resource_type === "Tweet" && (
                <div className={styles.shareButton}>
                  <TwitterShareButton
                    url={window.location.href}
                    title={resource.content}
                  >
                    Share to Twitter
                  </TwitterShareButton>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ResourceModal;
