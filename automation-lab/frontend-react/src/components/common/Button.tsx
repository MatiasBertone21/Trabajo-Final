interface ButtonProps {
  label: string;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
  testId: string; // para automatización
  className?: string;
}

export const Button = ({ label, onClick, type = 'button', testId, className = 'button-primary' }: ButtonProps) => (
  <button type={type} onClick={onClick} data-testid={testId} className={className}>
    {label}
  </button>
);