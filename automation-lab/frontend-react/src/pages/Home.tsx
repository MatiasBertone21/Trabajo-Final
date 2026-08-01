import { Card } from '../components/common/Card';

export const Home = () => (
  <div data-testid="home-page">
    <h1>Bienvenido al Automation Lab</h1>
    <Card title="Estado del Sistema" testId="system-status-card">
      <p>Backend: Conectado</p>
      <p>Frontend: Listo para pruebas</p>
    </Card>
  </div>
);