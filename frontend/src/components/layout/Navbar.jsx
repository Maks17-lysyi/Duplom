import { Link } from 'react-router-dom';
import { Button } from '../ui/Button';
import { Gamepad2, Bell, User } from 'lucide-react';

export default function Navbar() {
    return (
        <nav className="border-b border-surface-hover bg-background/80 backdrop-blur-md sticky top-0 z-50">
            <div className="container mx-auto px-4 h-16 flex items-center justify-between">
                <Link to="/" className="flex items-center gap-2 text-xl font-bold text-primary hover:text-white transition-colors group">
                    <div className="p-2 bg-accent/10 rounded-lg group-hover:bg-accent/20 transition-colors">
                        <Gamepad2 className="w-6 h-6 text-accent" />
                    </div>
                    <span className="tracking-tight">Party<span className="text-accent">Finder</span></span>
                </Link>

                {/* Desktop Navigation */}
                <div className="hidden md:flex items-center gap-1">
                    <NavLink to="/dashboard">Lobbies</NavLink>
                    <NavLink to="/map">Map View</NavLink>
                    <NavLink to="/community">Community</NavLink>
                </div>

                <div className="flex items-center gap-3">
                    <Button variant="ghost" size="icon" className="text-secondary hover:text-white relative">
                        <Bell className="w-5 h-5" />
                        <span className="absolute top-2 right-2 w-2 h-2 bg-error rounded-full pointer-events-none" />
                    </Button>

                    <div className="h-6 w-px bg-surface-hover mx-1 hidden sm:block"></div>

                    <Link to="/login">
                        <Button variant="primary" size="sm" className="hidden sm:flex">
                            Login / Register
                        </Button>
                    </Link>
                    {/* Mobile Menu Button would go here */}
                </div>
            </div>
        </nav>
    );
}

function NavLink({ to, children }) {
    return (
        <Link
            to={to}
            className="px-4 py-2 text-sm font-medium text-secondary hover:text-white hover:bg-surface rounded-md transition-all"
        >
            {children}
        </Link>
    )
}
