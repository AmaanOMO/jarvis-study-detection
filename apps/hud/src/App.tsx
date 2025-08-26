import React from 'react'
import { Scene } from './components/Scene'
import { Typewriter } from './components/Typewriter'
import { useHUDStore } from './store'
import { wsClient } from './ws'

const StatusIndicator: React.FC = () => {
  const { status, connected } = useHUDStore()
  
  const getStatusColor = () => {
    switch (status) {
      case 'LOOKING':
        return 'text-green-400'
      case 'AWAY':
        return 'text-red-400'
      default:
        return 'text-gray-400'
    }
  }
  
  const getStatusText = () => {
    if (!connected) return 'Offline'
    return status
  }
  
  return (
    <div className="flex items-center space-x-2">
      <div className={`w-3 h-3 rounded-full ${getStatusColor()} jarvis-glow`} />
      <span className="text-sm font-mono">{getStatusText()}</span>
    </div>
  )
}

const Header: React.FC = () => {
  const { connected } = useHUDStore()
  
  return (
    <div className="absolute top-0 left-0 right-0 z-10 flex justify-between items-center p-6">
      {/* Left: JARVIS */}
      <div className="flex items-center space-x-2">
        <div className="w-3 h-3 rounded-full bg-jarvis-primary jarvis-glow" />
        <span className="text-xl font-bold font-mono text-jarvis-primary jarvis-text-glow">
          JARVIS
        </span>
      </div>
      
      {/* Right: Status */}
      <StatusIndicator />
    </div>
  )
}

const HUDLayout: React.FC = () => {
  const { connected } = useHUDStore()
  
  const handleOrbClick = () => {
    if (connected) {
      wsClient.sendClick()
    }
  }
  
  return (
    <div className="relative w-full h-screen bg-jarvis-bg overflow-hidden">
      {/* Header */}
      <Header />
      
      {/* Main HUD area */}
      <div className="relative w-full h-full">
        {/* Three.js Scene */}
        <Scene className="w-full h-full" />
        
        {/* Clickable orb overlay */}
        <div 
          className="absolute inset-0 flex items-center justify-center cursor-pointer"
          onClick={handleOrbClick}
          title="Click to trigger roast"
        >
          {/* Invisible click area */}
          <div className="w-32 h-32 rounded-full opacity-0 hover:opacity-10 hover:bg-jarvis-primary transition-opacity" />
        </div>
        
        {/* Typewriter text below orb */}
        <div className="absolute bottom-32 left-0 right-0">
          <Typewriter />
        </div>
        
        {/* Connection status */}
        {!connected && (
          <div className="absolute bottom-6 left-6 bg-red-900/80 text-red-100 px-3 py-1 rounded text-sm font-mono">
            Disconnected from server
          </div>
        )}
      </div>
    </div>
  )
}

const App: React.FC = () => {
  return <HUDLayout />
}

export default App
