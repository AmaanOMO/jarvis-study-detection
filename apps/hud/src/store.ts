import { create } from 'zustand'

export interface HUDState {
  // Connection state
  connected: boolean
  
  // Status
  status: 'LOOKING' | 'AWAY' | 'UNKNOWN'
  
  // Speaking state
  isSpeaking: boolean
  lastLine: string
  
  // Audio envelope for orb pulsing
  envelope: number[]
  currentEnvelopeIndex: number
  
  // Actions
  setConnected: (connected: boolean) => void
  setStatus: (status: 'LOOKING' | 'AWAY' | 'UNKNOWN') => void
  setSpeaking: (speaking: boolean, line?: string) => void
  setEnvelope: (envelope: number[]) => void
  advanceEnvelope: () => void
  reset: () => void
}

export const useHUDStore = create<HUDState>((set, get) => ({
  // Initial state
  connected: false,
  status: 'UNKNOWN',
  isSpeaking: false,
  lastLine: '',
  envelope: [],
  currentEnvelopeIndex: 0,
  
  // Actions
  setConnected: (connected) => set({ connected }),
  
  setStatus: (status) => set({ status }),
  
  setSpeaking: (speaking, line) => set((state) => ({
    isSpeaking: speaking,
    lastLine: line || state.lastLine,
    currentEnvelopeIndex: 0
  })),
  
  setEnvelope: (envelope) => set({ 
    envelope,
    currentEnvelopeIndex: 0
  }),
  
  advanceEnvelope: () => set((state) => ({
    currentEnvelopeIndex: Math.min(
      state.currentEnvelopeIndex + 1,
      state.envelope.length - 1
    )
  })),
  
  reset: () => set({
    isSpeaking: false,
    lastLine: '',
    envelope: [],
    currentEnvelopeIndex: 0
  })
}))

// Get current pulse value from envelope
export const getCurrentPulse = (): number => {
  const { envelope, currentEnvelopeIndex } = useHUDStore.getState()
  if (envelope.length === 0) return 0
  return envelope[Math.min(currentEnvelopeIndex, envelope.length - 1)] || 0
}
