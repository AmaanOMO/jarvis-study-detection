import React, { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

interface SweepsProps {
  position?: [number, number, number]
  count?: number
  length?: number
  baseRadius?: number
}

export const Sweeps: React.FC<SweepsProps> = ({ 
  position = [0, 0, 0],
  count = 8,
  length = 1.0,
  baseRadius = 1.5
}) => {
  const sweepsRef = useRef<THREE.Group>(null)
  
  useFrame((state) => {
    if (!sweepsRef.current) return
    
    const time = state.clock.elapsedTime
    
    // Rotate sweep lines
    sweepsRef.current.rotation.z = time * 0.6
    
    // Animate sweep line opacity
    sweepsRef.current.children.forEach((sweep, index) => {
      if (sweep instanceof THREE.Mesh && sweep.material instanceof THREE.MeshBasicMaterial) {
        const opacity = 0.6 + 0.4 * Math.sin(time * 3 + index * 0.5)
        sweep.material.opacity = Math.max(0.2, opacity)
      }
    })
  })
  
  return (
    <group ref={sweepsRef} position={position}>
      {Array.from({ length: count }, (_, i) => {
        const angle = (i / count) * Math.PI * 2
        const startRadius = baseRadius
        const endRadius = baseRadius + length
        
        // Create sweep line geometry
        const points = [
          new THREE.Vector3(
            Math.cos(angle) * startRadius,
            Math.sin(angle) * startRadius,
            0
          ),
          new THREE.Vector3(
            Math.cos(angle) * endRadius,
            Math.sin(angle) * endRadius,
            0
          )
        ]
        
        const geometry = new THREE.BufferGeometry().setFromPoints(points)
        
        return (
          <line key={i} geometry={geometry}>
            <lineBasicMaterial 
              color="#5AB4FF" 
              transparent 
              opacity={0.8}
              linewidth={2}
            />
          </line>
        )
      })}
    </group>
  )
}
