import React, { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

interface RingsProps {
  position?: [number, number, number]
  count?: number
  baseRadius?: number
  spacing?: number
}

export const Rings: React.FC<RingsProps> = ({ 
  position = [0, 0, 0],
  count = 3,
  baseRadius = 1.5,
  spacing = 0.5
}) => {
  const ringsRef = useRef<THREE.Group>(null)
  
  useFrame((state) => {
    if (!ringsRef.current) return
    
    const time = state.clock.elapsedTime
    
    // Rotate rings slowly
    ringsRef.current.rotation.z = time * 0.1
    
    // Animate ring opacity
    ringsRef.current.children.forEach((ring, index) => {
      if (ring instanceof THREE.Mesh && ring.material instanceof THREE.MeshBasicMaterial) {
        const opacity = 0.3 + 0.2 * Math.sin(time * 2 + index)
        ring.material.opacity = Math.max(0.1, opacity)
      }
    })
  })
  
  return (
    <group ref={ringsRef} position={position}>
      {Array.from({ length: count }, (_, i) => {
        const radius = baseRadius + (i * spacing)
        const opacity = 0.4 - (i * 0.1)
        
        return (
          <mesh key={i}>
            <ringGeometry args={[radius, radius + 0.05, 64]} />
            <meshBasicMaterial 
              color="#5AB4FF" 
              transparent 
              opacity={opacity}
              side={THREE.DoubleSide}
            />
          </mesh>
        )
      })}
    </group>
  )
}
