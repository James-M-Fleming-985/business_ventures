import { create } from 'zustand';

export const usePortfolioStore = create((set) => ({
  mvps: [
    { id: '1', name: 'MVP 1', description: 'First MVP' },
    { id: '2', name: 'MVP 2', description: 'Second MVP' },
  ],
  addMVP: (mvp) => set((state) => ({ mvps: [...state.mvps, mvp] })),
  removeMVP: (id) => set((state) => ({ mvps: state.mvps.filter((m) => m.id !== id) })),
}));