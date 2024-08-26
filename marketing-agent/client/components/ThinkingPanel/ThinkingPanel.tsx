import styles from "./ThinkingPanel.module.css";
import { PulseLoader } from "react-spinners";
interface ThinkingPanelProps {
  thoughts: string[];
  isLoading: boolean;
}

export default function ThinkingPanel({
  thoughts,
  isLoading
}: ThinkingPanelProps) {
  return (
    <div className={styles.container}>
      <h2 className={styles.title}>
        Thinking{" "}
        {isLoading && <PulseLoader size={6} color="var(--main-accent)" />}
      </h2>
      <ol className={styles.list}>
        {thoughts.map((item, index) => (
          <li key={index} className={styles.listItem}>
            <span className={styles.itemText}>{item}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
