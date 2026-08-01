import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Input } from '../components/common/Input';
import { Button } from '../components/common/Button';
import { apiClient } from '../api/axiosConfig';

export const Login = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await apiClient.post('/login', {
        email: username,
        password: password
      });

      if (response.status === 200) {
        localStorage.setItem('user', username);
        navigate('/');
      }
    } catch (error) {
      alert("Email o contraseña incorrectos. Por favor, intenta de nuevo.");
      console.error("Login failed", error);
    }
  };

  return (
    <div data-testid="login-page" className="page-shell">
      <div className="form-card">
        <h2>Iniciar Sesión</h2>
        <p className="page-copy">Ingresa tus credenciales para continuar en la plataforma.</p>

        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1.5rem' }}>
          <Input
            label="Usuario"
            testId="login-email"
            onChange={setUsername}
          />

          <Input
            label="Password"
            type="password"
            testId="login-password"
            onChange={setPassword}
          />

          <button type="submit" data-testid="login-button" style={{ display: 'none' }}>
            Login Oculto
          </button>

          <Button
            label="Entrar"
            testId="login-button-visible"
            type="submit"
          />
        </form>
      </div>
    </div>
  );
}