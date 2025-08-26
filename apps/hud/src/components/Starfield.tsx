import React, { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

interface StarfieldProps {
  count?: number
  size?: number
  depth?: number
}

export const Starfield: React.FC<StarfieldProps> = ({ 
  count = 100,
  size = 0.02,
  depth = 10
}) => {
  const starsRef = useRef<THREE.Points>(null)
  
  // Generate star positions
  const starPositions = useMemo(() => {
    const positions = new Float32Array(count * 3)
    
    for (let i = 0; i < count; i++) {
      const i3 = i * 3
      positions[i3] = (Math.random() - 0.5) * depth * 2
      positions[i3 + 1] = (Math.random() - 0.5) * depth * 2
      positions[i3 + 2] = (Math.random() - 0.5) * depth
    }
    
    return positions
  }, [count, depth])
  
  useFrame((state) => {
    if (!starsRef.current) return
    
    const time = state.clock.elapsedTime
    
    // Rotate starfield slowly
    starsRef.current.rotation.z = time * 0.05
    
    // Animate individual stars
    const positions = starsRef.current.geometry.attributes.position.array as Float32Array
    
    for (let i = 0; i < count; i++) {
      const i3 = i * 3
      const speed = 0.1 + Math.random() * 0.2
      
      // Move stars in a subtle pattern
      positions[i3] += Math.sin(time * speed + i) * 0.001
      positions[i3 + 1] += Math.cos(time * speed + i) * 0.001
    }
    
    starsRef.current.geometry.attributes.position.needsUpdate = true
  })
  
  return (
    <points ref={starsRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={count}
          array={starPositions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={size}
        color="#5AB4FF"
        transparent
        opacity={0.8}
        sizeAttenuation
      />
    </points>
  )
}
