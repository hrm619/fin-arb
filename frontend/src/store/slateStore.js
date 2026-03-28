import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useSlateStore = create(
  persist(
    (set, get) => ({
      currentSlateId: null,
      setCurrentSlateId: (id) => set({ currentSlateId: id }),

      // Map of external_event_id -> game metadata (persists across league switches)
      selectedGames: {},
      toggleGame: (game) => set((state) => {
        const next = { ...state.selectedGames };
        if (next[game.id]) {
          delete next[game.id];
        } else {
          next[game.id] = { ...game, market_type: 'moneyline' };
        }
        return { selectedGames: next };
      }),
      setGameMarketType: (gameId, marketType) => set((state) => {
        const game = state.selectedGames[gameId];
        if (!game) return state;
        return {
          selectedGames: { ...state.selectedGames, [gameId]: { ...game, market_type: marketType } },
        };
      }),
      clearSelectedGames: () => set({ selectedGames: {} }),
      isGameSelected: (gameId) => !!get().selectedGames[gameId],
    }),
    {
      name: 'slate-store',
      partialize: (state) => ({ currentSlateId: state.currentSlateId }),
    }
  )
);
