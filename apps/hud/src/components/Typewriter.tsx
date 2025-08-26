import React, { useState, useEffect } from 'react'
import { useHUDStore } from '../store'

interface TypewriterProps {
  className?: string
}

export const Typewriter: React.FC<TypewriterProps> = ({ className = '' }) => {
  const { lastLine, isSpeaking } = useHUDStore()
  const [displayText, setDisplayText] = useState('')
  const [currentIndex, setCurrentIndex] = useState(0)
  
  useEffect(() => {
    if (!lastLine) {
      setDisplayText('')
      setCurrentIndex(0)
      return
    }
    
    if (isSpeaking) {
      // Start typewriter effect
      setCurrentIndex(0)
      setDisplayText('')
      
      const interval = setInterval(() => {
        setCurrentIndex(prev => {
          if (prev >= lastLine.length) {
            clearInterval(interval)
            return prev
          }
          return prev + 1
        })
      }, 25) // ~40 characters per second
      
      return () => clearInterval(interval)
    } else {
      // Show full text when not speaking
      setDisplayText(lastLine)
      setCurrentIndex(lastLine.length)
    }
  }, [lastLine, isSpeaking])
  
  useEffect(() => {
    setDisplayText(lastLine.slice(0, currentIndex))
  }, [currentIndex, lastLine])
  
  if (!lastLine) return null
  
  return (
    <div className={`font-mono text-2xl text-center ${className}`}>
      <span className="text-jarvis-primary jarvis-text-glow">
        {displayText}
      </span>
      {isSpeaking && currentIndex < lastLine.length && (
        <span className="text-jarvis-accent animate-pulse">|</span>
      )}
    </div>
  )
}
