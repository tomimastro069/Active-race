import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export const Layout = () => {
  const { user, logoutUser } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logoutUser();
    navigate('/login');
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-white flex flex-col">
        <div className="p-4 border-b border-slate-800">
          <h2 className="text-xl font-bold tracking-tight">ActiveTrace</h2>
        </div>
        
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          <div className="text-xs uppercase text-slate-500 font-semibold mb-2 mt-4">General</div>
          <Link to="/dashboard" className="block px-4 py-2 rounded text-slate-300 hover:bg-slate-800 hover:text-white transition-colors">
            Dashboard
          </Link>
          
          {(user?.roles?.includes('PROFESOR') || user?.roles?.includes('TUTOR') || user?.roles?.includes('COORDINADOR') || user?.roles?.includes('ADMIN')) && (
            <>
              <div className="text-xs uppercase text-slate-500 font-semibold mb-2 mt-6">Académico Docente</div>
              <Link to="/comisiones" className="block px-4 py-2 rounded text-slate-300 hover:bg-slate-800 hover:text-white transition-colors">
                Mis Comisiones
              </Link>
              <Link to="/monitor-seguimiento" className="block px-4 py-2 rounded text-slate-300 hover:bg-slate-800 hover:text-white transition-colors">
                Monitor Seguimiento
              </Link>
              <Link to="/padron" className="block px-4 py-2 rounded text-slate-300 hover:bg-slate-800 hover:text-white transition-colors">
                Importar Padrón
              </Link>
              <Link to="/encuentros" className="block px-4 py-2 rounded text-slate-300 hover:bg-slate-800 hover:text-white transition-colors">
                Encuentros
              </Link>
              <Link to="/guardias" className="block px-4 py-2 rounded text-slate-300 hover:bg-slate-800 hover:text-white transition-colors">
                Mis Guardias
              </Link>
            </>
          )}

          {(user?.roles?.includes('COORDINADOR') || user?.roles?.includes('ADMIN')) && (
            <>
              <div className="text-xs uppercase text-slate-500 font-semibold mb-2 mt-6">Coordinación</div>
              <Link to="/usuarios" className="block px-4 py-2 rounded text-slate-300 hover:bg-slate-800 hover:text-white transition-colors">
                Gestión de Usuarios
              </Link>
              <Link to="/equipos" className="block px-4 py-2 rounded text-slate-300 hover:bg-slate-800 hover:text-white transition-colors">
                Equipos Docentes
              </Link>
              <Link to="/avisos" className="block px-4 py-2 rounded text-slate-300 hover:bg-slate-800 hover:text-white transition-colors">
                Avisos
              </Link>
              <Link to="/tareas" className="block px-4 py-2 rounded text-slate-300 hover:bg-slate-800 hover:text-white transition-colors">
                Tareas Internas
              </Link>
              <Link to="/monitor-coordinacion" className="block px-4 py-2 rounded text-slate-300 hover:bg-slate-800 hover:text-white transition-colors">
                Monitor Coordinación
              </Link>
            </>
          )}

          <div className="text-xs uppercase text-slate-500 font-semibold mb-2 mt-6">Mi Cuenta</div>
          <Link to="/inbox" className="block px-4 py-2 rounded text-slate-300 hover:bg-slate-800 hover:text-white transition-colors">
            Mensajería
          </Link>
          <Link to="/perfil" className="block px-4 py-2 rounded text-slate-300 hover:bg-slate-800 hover:text-white transition-colors">
            Mi Perfil
          </Link>
        </nav>

        <div className="p-4 border-t border-slate-800">
          <div className="mb-2">
            <p className="text-sm font-medium">{user?.email}</p>
            <p className="text-xs text-slate-400">{user?.roles?.join(', ')}</p>
          </div>
          <button 
            onClick={handleLogout}
            className="w-full mt-2 text-sm text-center py-2 border border-slate-700 rounded hover:bg-slate-800 transition-colors"
          >
            Cerrar Sesión
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto bg-white shadow-inner">
        <Outlet />
      </main>
    </div>
  );
};
