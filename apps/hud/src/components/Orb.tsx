import React, { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import { useHUDStore, getCurrentPulse } from '../store'
import * as THREE from 'three'

interface OrbProps {
  position?: [number, number, number]
  size?: number
}

export const Orb: React.FC<OrbProps> = ({ 
  position = [0, 0, 0], 
  size = 1 
}) => {
  const meshRef = useRef<THREE.Mesh>(null)
  const glowRef = useRef<THREE.Mesh>(null)
  const { isSpeaking } = useHUDStore()
  
  // Create materials
  const materials = useMemo(() => {
    const coreMaterial = new THREE.MeshBasicMaterial({
      color: '#ffffff',
      transparent: true,
      opacity: 0.9
    })
    
    const glowMaterial = new THREE.MeshBasicMaterial({
      color: '#5AB4FF',
      transparent: true,
      opacity: 0.3
    })
    
    return { coreMaterial, glowMaterial }
  }, [])
  
  useFrame((state) => {
    if (!meshRef.current || !glowRef.current) return
    
    const pulse = getCurrentPulse()
    const time = state.clock.elapsedTime
    
    // Pulse animation
    const pulseScale = 1 + 0.06 * pulse
    meshRef.current.scale.setScalar(pulseScale)
    glowRef.current.scale.setScalar(pulseScale * 1.5)
    
    // Breathing animation
    const breath = Math.sin(time * 2) * 0.05
    const finalScale = pulseScale + breath
    meshRef.current.scale.setScalar(finalScale)
    glowRef.current.scale.setScalar(finalScale * 1.5)
    
    // Glow intensity based on pulse
    if (materials.glowMaterial) {
      materials.glowMaterial.opacity = 0.2 + 0.3 * pulse
    }
  })
  
  return (
    <group position={position}>
      {/* Outer glow */}
      <mesh ref={glowRef} material={materials.glowMaterial}>
        <sphereGeometry args={[size * 1.5, 32, 32]} />
      </mesh>
      
      {/* Core orb */}
      <mesh ref={meshRef} material={materials.coreMaterial}>
        <sphereGeometry args={[size, 32, 32]} />
      </mesh>
      
      {/* Inner highlight */}
      <mesh position={[-size * 0.3, -size * 0.3, size * 0.1]}>
        <sphereGeometry args={[size * 0.4, 16, 16]} />
        <meshBasicMaterial color="#ffffff" transparent opacity={0.8} />
      </mesh>
    </group>
  )
}
