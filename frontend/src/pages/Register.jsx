import { Link } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card } from '../components/ui/Card';
import { Gamepad2 } from 'lucide-react';

export default function Register() {
    return (
        <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center p-4">
            <Card className="w-full max-w-md p-8 space-y-6 bg-surface/80 backdrop-blur-xl border-surface-hover/50 shadow-2xl">
                <div className="text-center space-y-2">
                    <div className="inline-flex p-3 rounded-xl bg-accent/10 mb-2">
                        <Gamepad2 className="w-8 h-8 text-accent" />
                    </div>
                    <h1 className="text-2xl font-bold tracking-tight">Create an Account</h1>
                    <p className="text-secondary text-sm">Join the community and find your squad</p>
                </div>

                <form className="space-y-4">
                    <div className="space-y-2">
                        <Input type="text" placeholder="Username" label="Username" />
                    </div>
                    <div className="space-y-2">
                        <Input type="email" placeholder="Email" label="Email" />
                    </div>
                    <div className="space-y-2">
                        <Input type="password" placeholder="Password" label="Password" />
                    </div>
                    <div className="space-y-2">
                        <Input type="password" placeholder="Confirm Password" label="Confirm Password" />
                    </div>

                    <div className="pt-2">
                        <Button className="w-full" type="submit">
                            Create Account
                        </Button>
                    </div>
                </form>

                <div className="text-center text-sm">
                    <span className="text-secondary">Already have an account? </span>
                    <Link to="/login" className="text-accent hover:text-accent-hover font-medium underline-offset-4 hover:underline">
                        Sign in
                    </Link>
                </div>
            </Card>
        </div>
    );
}
