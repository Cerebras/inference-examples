import { useState } from "react";
import { ModelProviders, GenerateRequest } from "../../types/main";
import styles from "./ProductForm.module.css";
interface ProductFormProps {
  onSubmit: (request: GenerateRequest) => void;
}

const ModelProviderDisplayNames: Record<ModelProviders, string> = {
  [ModelProviders.cerebras]: "Cerebras (Fastest)",
  [ModelProviders.fireworks]: "Fireworks (Terribly slow)",
  [ModelProviders.groq]: "Groq (Boo)",
  [ModelProviders.together]: "Together (lacks flavour)"
};

export default function ProductForm({ onSubmit }: ProductFormProps) {
  const [productDescription, setProductDescription] = useState("");
  const [modelProvider, setModelProvider] = useState<ModelProviders>(
    ModelProviders.cerebras
  );

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    onSubmit({
      product_description: productDescription,
      provider: modelProvider
    });
  };

  return (
    <form onSubmit={handleSubmit} className={styles.formContainer}>
      <div className={styles.formGroup}>
        <label className={styles.label}>Product Description</label>
        <input
          type="text"
          value={productDescription}
          onChange={(e) => setProductDescription(e.target.value)}
          className={styles.input}
          placeholder="Enter product description"
        />
      </div>
      <div className={styles.formGroup}>
        <label className={styles.label}>Speed</label>
        <select
          value={modelProvider}
          onChange={(e) => setModelProvider(e.target.value as ModelProviders)}
          className={styles.select}
        >
          {Object.values(ModelProviders).map((provider) => (
            <option key={provider} value={provider}>
              {ModelProviderDisplayNames[provider]}
            </option>
          ))}
        </select>
      </div>
      <div className={styles.buttonContainer}>
        <button type="submit" className={styles.submitButton}>
          Submit
        </button>
      </div>
    </form>
  );
}
