import React, { useState, useEffect } from "react";
import styles from "./ThinkingPanel.module.css";
import { PulseLoader } from "react-spinners";

interface ThinkingPanelProps {
  latestThought: string | null;
  isLoading: boolean;
}

export default function ThinkingPanel({
  latestThought,
  isLoading
}: ThinkingPanelProps) {
  const [thoughts, setThoughts] = useState<string[]>([]);

  useEffect(() => {
    if (latestThought) {
      setThoughts((prevThoughts) => [latestThought, ...prevThoughts]);
    }
  }, [latestThought]);

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>
        Thinking{" "}
        {isLoading && <PulseLoader size={6} color="var(--main-accent)" />}
      </h2>
      <ol className={styles.list}>
        {thoughts.map((item, index) => (
          <li
            key={index}
            className={styles.listItem}
            style={{
              backgroundColor: index % 2 === 0 ? "#e6f3ff" : "#f2f9fb"
            }}
          >
            <span className={styles.itemNumber}>
              {thoughts.length - index}.
            </span>
            <span className={styles.itemText}>{item}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
