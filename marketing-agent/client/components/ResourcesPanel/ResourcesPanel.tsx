import styles from "./ResourcesPanel.module.css";
import { PulseLoader } from "react-spinners";
import Image from "next/image";
import { Resource } from "../../types/resource";

interface ResourcesPanelProps {
  resources: Resource[];
  isLoading: boolean;
  onResourceClick: (resource: Resource) => void;
}
export const getResourceIcon = (resourceType: Resource["resource_type"]) => {
  switch (resourceType) {
    case "Tweet":
      return "/x.png";
    case "LinkedInPost":
      return "/linkedin.png";
    case "Email":
      return "/email.png";
    // Add more cases as needed
    default:
      return "/default.png";
  }
};

export default function ResourcesPanel({
  resources,
  onResourceClick,
  isLoading
}: ResourcesPanelProps) {
  return (
    <div className={styles.container}>
      <h2 className={styles.title}>
        Resources{" "}
        {isLoading && <PulseLoader size={6} color="var(--main-accent)" />}
      </h2>
      <div className={styles.grid}>
        {resources.length > 0
          ? resources.map((resource, index) => (
              <div
                key={index}
                className={styles.resourceCard}
                onClick={() => onResourceClick(resource)}
              >
                <div className={styles.resourceHeader}>
                  <Image
                    src={getResourceIcon(resource.resource_type)}
                    alt={resource.resource_type}
                    width={16}
                    height={16}
                    className={styles.resourceImage}
                  />
                  {resource.resource_type}
                </div>
                <p className={styles.resourceTitle}>{resource.title}</p>
              </div>
            ))
          : // Skeleton loaders
            Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className={styles.skeletonCard}>
                <div className={styles.skeletonImage}></div>
                <div className={styles.skeletonTitle}></div>
              </div>
            ))}
      </div>
    </div>
  );
}
