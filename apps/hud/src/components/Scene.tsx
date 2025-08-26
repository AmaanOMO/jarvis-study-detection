import React, { useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import { Orb } from './Orb'
import { Rings } from './Rings'
import { Sweeps } from './Sweeps'
import { Starfield } from './Starfield'
import { useHUDStore } from '../store'

// Camera controller component
const CameraController: React.FC = () => {
  const controlsRef = useRef<any>(null)
  
  useFrame(() => {
    if (controlsRef.current) {
      // Keep camera focused on the orb
      controlsRef.current.target.set(0, 0, 0)
    }
  })
  
  return (
    <OrbitControls
      ref={controlsRef}
      enableZoom={false}
      enablePan={false}
      enableRotate={false}
      maxPolarAngle={Math.PI / 2}
      minPolarAngle={Math.PI / 2}
    />
  )
}

// Main scene content
const SceneContent: React.FC = () => {
  const { isSpeaking } = useHUDStore()
  
  return (
    <>
      {/* Background starfield */}
      <Starfield count={150} size={0.015} depth={15} />
      
      {/* Central orb */}
      <Orb position={[0, 0, 0]} size={1.2} />
      
      {/* Concentric rings */}
      <Rings 
        position={[0, 0, 0]} 
        count={3} 
        baseRadius={1.8} 
        spacing={0.4} 
      />
      
      {/* Sweep lines */}
      <Sweeps 
        position={[0, 0, 0]} 
        count={8} 
        length={1.2} 
        baseRadius={2.2} 
      />
      
      {/* Ambient light for subtle illumination */}
      <ambientLight intensity={0.1} color="#5AB4FF" />
      
      {/* Point light for orb glow */}
      <pointLight 
        position={[0, 0, 2]} 
        intensity={isSpeaking ? 0.8 : 0.3} 
        color="#5AB4FF" 
        distance={10}
      />
    </>
  )
}

interface SceneProps {
  className?: string
}

export const Scene: React.FC<SceneProps> = ({ className = '' }) => {
  return (
    <div className={`w-full h-full ${className}`}>
      <Canvas
        camera={{ position: [0, 0, 5], fov: 60 }}
        gl={{ 
          antialias: true, 
          alpha: true,
          powerPreference: "high-performance"
        }}
        onCreated={({ gl }) => {
          gl.setClearColor('#0b0f14', 0)
          gl.setPixelRatio(Math.min(window.devicePixelRatio, 2))
        }}
      >
        <SceneContent />
        <CameraController />
      </Canvas>
    </div>
  )
}
