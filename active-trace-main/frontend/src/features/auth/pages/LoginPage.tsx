import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useAuth } from '@/shared/contexts/AuthContext';
import { authService } from '../services/auth.service';
import { useNavigate, useLocation } from 'react-router-dom';
import { AxiosError } from 'axios';

const loginSchema = z.object({
  email: z.string().email('Email inválido'),
  password: z.string().min(1, 'La contraseña es requerida'),
});

const twoFactorSchema = z.object({
  token_2fa: z.string().length(6, 'El código debe tener 6 dígitos'),
});

type LoginFormValues = z.infer<typeof loginSchema>;
type TwoFactorFormValues = z.infer<typeof twoFactorSchema>;

export const LoginPage: React.FC = () => {
  const [step, setStep] = useState<'login' | '2fa' | 'recovery'>('login');
  const [tempToken, setTempToken] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const { loginUser } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/';

  const loginForm = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const twoFactorForm = useForm<TwoFactorFormValues>({
    resolver: zodResolver(twoFactorSchema),
  });

  const onLoginSubmit = async (data: LoginFormValues) => {
    setErrorMsg(null);
    try {
      const response = await authService.login({ email: data.email, password: data.password });
      if (response.requires_2fa) {
        // El backend devuelve un token temporal que habilita /auth/verify-2fa
        setTempToken(response.access_token);
        setStep('2fa');
      } else {
        const user = await authService.me();
        loginUser(user, response.access_token);
        navigate(from, { replace: true });
      }
    } catch (error) {
      if (error instanceof AxiosError && error.response?.status === 401) {
        setErrorMsg('Credenciales inválidas');
      } else {
        setErrorMsg('Error al intentar iniciar sesión');
      }
    }
  };

  const onTwoFactorSubmit = async (data: TwoFactorFormValues) => {
    setErrorMsg(null);
    try {
      const response = await authService.verify2fa(tempToken, data.token_2fa);
      const user = await authService.me();
      loginUser(user, response.access_token);
      navigate(from, { replace: true });
    } catch (error) {
      setErrorMsg('Código 2FA inválido');
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100">
      <div className="w-full max-w-md p-8 bg-white rounded-lg shadow-md">
        <h2 className="text-2xl font-bold text-center text-gray-800 mb-6">
          {step === 'login' ? 'Iniciar Sesión' : step === '2fa' ? 'Verificación 2FA' : 'Recuperar Contraseña'}
        </h2>

        {errorMsg && (
          <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-md text-sm">
            {errorMsg}
          </div>
        )}

        {step === 'login' && (
          <form onSubmit={loginForm.handleSubmit(onLoginSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Email</label>
              <input
                type="email"
                {...loginForm.register('email')}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
              {loginForm.formState.errors.email && (
                <p className="mt-1 text-sm text-red-600">{loginForm.formState.errors.email.message}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Contraseña</label>
              <input
                type="password"
                {...loginForm.register('password')}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
              {loginForm.formState.errors.password && (
                <p className="mt-1 text-sm text-red-600">{loginForm.formState.errors.password.message}</p>
              )}
            </div>
            <button
              type="submit"
              disabled={loginForm.formState.isSubmitting}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {loginForm.formState.isSubmitting ? 'Iniciando...' : 'Entrar'}
            </button>
            <div className="text-center mt-4">
              <button
                type="button"
                onClick={() => setStep('recovery')}
                className="text-sm text-blue-600 hover:underline"
              >
                ¿Olvidaste tu contraseña?
              </button>
            </div>
          </form>
        )}

        {step === '2fa' && (
          <form onSubmit={twoFactorForm.handleSubmit(onTwoFactorSubmit)} className="space-y-4">
            <p className="text-sm text-gray-600 mb-4">Ingresa el código de 6 dígitos de tu aplicación autenticadora.</p>
            <div>
              <label className="block text-sm font-medium text-gray-700">Código TOTP</label>
              <input
                type="text"
                {...twoFactorForm.register('token_2fa')}
                maxLength={6}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-center tracking-widest text-lg"
              />
              {twoFactorForm.formState.errors.token_2fa && (
                <p className="mt-1 text-sm text-red-600">{twoFactorForm.formState.errors.token_2fa.message}</p>
              )}
            </div>
            <button
              type="submit"
              disabled={twoFactorForm.formState.isSubmitting}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
            >
              Verificar
            </button>
            <div className="text-center mt-4">
              <button
                type="button"
                onClick={() => setStep('login')}
                className="text-sm text-gray-600 hover:underline"
              >
                Volver al inicio de sesión
              </button>
            </div>
          </form>
        )}

        {step === 'recovery' && (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">La recuperación de contraseña será implementada próximamente.</p>
            <button
              type="button"
              onClick={() => setStep('login')}
              className="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              Volver
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
