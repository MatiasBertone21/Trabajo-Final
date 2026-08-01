interface InputProps {
  label: string;
  type?: string;
  testId: string;
  onChange: (value: string) => void;
}

export const Input = ({ label, type = "text", testId, onChange }: InputProps) => (
  <div className="input-group">
    <label>{label}</label>
    <input
      type={type}
      data-testid={testId}
      onChange={(e) => onChange(e.target.value)}
    />
  </div>
);