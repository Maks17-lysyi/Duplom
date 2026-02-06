import { Link } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card } from '../components/ui/Card';
import { Gamepad2 } from 'lucide-react';

export default function Login() {
    return (
        <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center p-4">
            <Card className="w-full max-w-md p-8 space-y-6 bg-surface/80 backdrop-blur-xl border-surface-hover/50 shadow-2xl">
                <div className="text-center space-y-2">
                    <div className="inline-flex p-3 rounded-xl bg-accent/10 mb-2">
                        <Gamepad2 className="w-8 h-8 text-accent" />
                    </div>
                    <h1 className="text-2xl font-bold tracking-tight">Welcome Back</h1>
                    <p className="text-secondary text-sm">Enter your credentials to access your account</p>
                </div>

                <div className="space-y-4">
                    <Button variant="outline" className="w-full gap-2 relative overflow-hidden group border-surface-hover hover:border-white/20 hover:bg-white/5">
                        {/* Mock Google Icon */}
                        <svg className="w-5 h-5" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" /><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" /><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" /><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" /></svg>
                        Continue with Google
                    </Button>
                    <Button variant="outline" className="w-full gap-2 relative overflow-hidden group border-surface-hover hover:border-white/20 hover:bg-[#171a21]/50">
                        {/* Mock Steam Icon */}
                        <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M11.979 0C5.666 0 .506 4.908 0 11.235l4.305 1.772c.67-.23 1.4-.2 2.045.06l3.352-4.834c-.035-.306-.057-.618-.057-.936 0-3.69 2.99-6.68 6.68-6.68 3.692 0 6.68 2.99 6.68 6.68 0 3.693-2.988 6.68-6.68 6.68l-4.502-1.854c-1.385 1.252-3.468 1.69-5.234 1.054l-1.928 2.32c1.37 1.012 3.12 1.488 4.903 1.252 3.823-.505 6.61-3.774 6.55-7.796C15.998 4.267 11.979 0 11.979 0zm.09 3.513c2.455 0 4.446 1.99 4.446 4.446 0 2.455-1.99 4.445-4.446 4.445-2.454 0-4.445-1.99-4.445-4.445 0-2.456 1.99-4.446 4.445-4.446z" /></svg>
                        Continue with Steam
                    </Button>
                </div>

                <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                        <span className="w-full border-t border-surface-hover" />
                    </div>
                    <div className="relative flex justify-center text-xs uppercase">
                        <span className="bg-surface px-2 text-muted">Or continue with</span>
                    </div>
                </div>

                <form className="space-y-4">
                    <div className="space-y-2">
                        <Input type="email" placeholder="Email" label="Email" />
                    </div>
                    <div className="space-y-2">
                        <Input type="password" placeholder="Password" label="Password" />
                    </div>
                    <Button className="w-full" type="submit">
                        Sign In
                    </Button>
                </form>

                <div className="text-center text-sm">
                    <span className="text-secondary">Don't have an account? </span>
                    <Link to="/register" className="text-accent hover:text-accent-hover font-medium underline-offset-4 hover:underline">
                        Sign up
                    </Link>
                </div>
            </Card>
        </div>
    );
}
