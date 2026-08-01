interface CardProps {
  title: string;
  children: React.ReactNode;
  testId: string;
}

export const Card = ({ title, children, testId }: CardProps) => (
  <div data-testid={testId} className="card-base">
    <h3 className="card-title">{title}</h3>
    <div className="card-content">{children}</div>
  </div>
);