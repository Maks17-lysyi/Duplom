import { useState } from 'react';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card } from '../components/ui/Card';
import { Search, Filter, Users, Mic, Clock } from 'lucide-react';
import Modal from '../components/ui/Modal';

export default function Dashboard() {
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

    const lobbies = [
        { id: 1, title: 'CS2 Premier Grind', game: 'Counter-Strike 2', players: 3, maxPlayers: 5, rank: '15k+', mic: true, region: 'EU West' },
        { id: 2, title: 'Chill Dota 2 Turbo', game: 'Dota 2', players: 4, maxPlayers: 5, rank: 'Any', mic: false, region: 'NA East' },
        { id: 3, title: 'Valorant Comp', game: 'Valorant', players: 2, maxPlayers: 5, rank: 'Diamond', mic: true, region: 'EU East' },
    ];

    return (
        <div className="container mx-auto p-4 md:p-8 space-y-8 animate-in fade-in duration-500">

            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-secondary bg-clip-text text-transparent">Lobby Browser</h1>
                    <p className="text-secondary mt-1">Find your perfect teammates.</p>
                </div>
                <Button size="lg" className="shadow-accent/20 shadow-xl gap-2" onClick={() => setIsCreateModalOpen(true)}>
                    <Users className="w-5 h-5" />
                    Create Lobby
                </Button>
            </div>

            {/* Filters */}
            <div className="flex flex-col md:flex-row gap-4">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-2.5 h-5 w-5 text-muted" />
                    <Input placeholder="Search lobbies by game or title..." className="pl-10 bg-surface/50 border-surface-hover" />
                </div>
                <Button variant="secondary" className="gap-2">
                    <Filter className="w-4 h-4" />
                    Filters
                </Button>
            </div>

            {/* Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {lobbies.map((lobby) => (
                    <Card key={lobby.id} className="group hover:border-accent/50 transition-colors cursor-pointer hover:shadow-lg hover:shadow-accent/5">
                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <span className="text-xs font-medium px-2 py-1 rounded bg-accent/10 text-accent mb-2 inline-block">
                                    {lobby.game}
                                </span>
                                <h3 className="font-semibold text-lg group-hover:text-accent transition-colors">{lobby.title}</h3>
                            </div>
                            <div className="text-xs text-secondary bg-surface-hover px-2 py-1 rounded">
                                {lobby.region}
                            </div>
                        </div>

                        <div className="space-y-3 text-sm text-secondary">
                            <div className="flex items-center gap-2">
                                <Users className="w-4 h-4 text-muted" />
                                <span>{lobby.players}/{lobby.maxPlayers} Players</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-4 h-4 flex items-center justify-center">
                                    {lobby.mic ? <Mic className="w-4 h-4 text-success" /> : <Mic className="w-4 h-4 text-muted" />}
                                </div>
                                <span>{lobby.mic ? 'Voice Required' : 'No Voice'}</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="w-4 text-center font-bold text-muted">#</span>
                                <span>Rank: {lobby.rank}</span>
                            </div>
                        </div>

                        <div className="mt-6">
                            <Button className="w-full" variant="secondary">Join Lobby</Button>
                        </div>
                    </Card>
                ))}

                {/* Empty State / Create Prompt */}
                <Card
                    className="flex flex-col items-center justify-center p-12 text-center border-dashed border-2 hover:border-accent/50 transition-colors group cursor-pointer h-full min-h-[280px]"
                    onClick={() => setIsCreateModalOpen(true)}
                >
                    <div className="w-12 h-12 rounded-full bg-surface-hover flex items-center justify-center mb-4 group-hover:scale-110 transition-transform shadow-lg shadow-black/20">
                        <span className="text-2xl text-accent">+</span>
                    </div>
                    <h3 className="text-lg font-medium group-hover:text-accent transition-colors">Create a New Lobby</h3>
                    <p className="text-secondary text-sm">Can't find what you're looking for?</p>
                </Card>
            </div>

            <Modal isOpen={isCreateModalOpen} onClose={() => setIsCreateModalOpen(false)} title="Create New Lobby">
                <form className="space-y-4">
                    <div>
                        <label className="text-sm font-medium text-secondary mb-1 block">Game</label>
                        <select className="flex h-11 w-full rounded-lg border border-surface-hover bg-surface px-3 py-2 text-sm text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent">
                            <option>Counter-Strike 2</option>
                            <option>Dota 2</option>
                            <option>Valorant</option>
                            <option>League of Legends</option>
                        </select>
                    </div>
                    <Input label="Lobby Title" placeholder="e.g. Grinding to Global Elite" />
                    <div className="grid grid-cols-2 gap-4">
                        <Input label="Max Players" type="number" defaultValue="5" />
                        <div>
                            <label className="text-sm font-medium text-secondary mb-1 block">Region</label>
                            <select className="flex h-11 w-full rounded-lg border border-surface-hover bg-surface px-3 py-2 text-sm text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent">
                                <option>EU West</option>
                                <option>EU East</option>
                                <option>NA East</option>
                                <option>NA West</option>
                            </select>
                        </div>
                    </div>
                    <Input label="Rank Requirement (Optional)" placeholder="e.g. Gold+" />

                    <div className="flex items-center gap-2 pt-2">
                        <input type="checkbox" id="mic-req" className="w-4 h-4 rounded border-gray-300 text-accent focus:ring-accent" />
                        <label htmlFor="mic-req" className="text-sm text-secondary">Voice Chat Required</label>
                    </div>

                    <div className="pt-4 flex gap-3">
                        <Button type="button" variant="ghost" className="flex-1" onClick={() => setIsCreateModalOpen(false)}>Cancel</Button>
                        <Button type="submit" className="flex-1">Create Lobby</Button>
                    </div>
                </form>
            </Modal>
        </div>
    );
}
