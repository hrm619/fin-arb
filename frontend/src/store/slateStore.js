import { create } from 'zustand';

export const useSlateStore = create((set) => ({
  currentSlateId: null,
  setCurrentSlateId: (id) => set({ currentSlateId: id }),
}));
