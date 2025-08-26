# Jarvis HUD - React Web Interface

A modern, cinematic HUD interface for the Jarvis Study Detection system, built with React, Three.js, and WebSocket communication.

## 🚀 Features

- **Cinematic Visual Effects**: Glowing orb, rotating sweep lines, concentric rings, and starfield particles
- **Real-time Status**: Shows LOOKING/AWAY status from Python backend
- **Audio-reactive Animations**: Orb pulses to TTS audio envelope
- **Interactive Orb**: Click to trigger roast lines
- **Typewriter Effect**: Animated text display for spoken lines
- **WebSocket Integration**: Real-time communication with Python backend

## 🛠️ Tech Stack

- **Frontend**: React 18 + TypeScript
- **3D Graphics**: Three.js + React Three Fiber
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Build Tool**: Vite
- **Communication**: WebSocket

## 📦 Installation

```bash
cd apps/hud
npm install
```

## 🚀 Development

```bash
npm run dev
```

The app will run on `http://localhost:5173`

## 🔌 WebSocket Connection

The HUD connects to the Python backend via WebSocket at `ws://localhost:8765`

**Incoming Messages:**
- `status`: Current focus status (LOOKING/AWAY)
- `speak`: TTS text and audio envelope
- `playing`: TTS playback state

**Outgoing Messages:**
- `click`: Orb click event

## 🎨 Visual Components

- **Orb**: Central glowing sphere that pulses to audio
- **Rings**: Concentric circles around the orb
- **Sweeps**: Rotating radar-like lines
- **Starfield**: Animated background particles
- **Typewriter**: Text display with typewriter effect

## 🎯 Usage

1. **Start Python Backend**: Run `python main.py` in the root directory
2. **Start React Dev Server**: Run `npm run dev` in `apps/hud/`
3. **Open Browser**: Navigate to `http://localhost:5173`
4. **Interact**: Click the orb to trigger roast lines

## 🎬 Filming

The HUD is designed for phone recording with:
- High contrast colors
- Smooth 60fps animations
- Cinematic visual effects
- Clean, minimalist interface

## 🔧 Configuration

Visual settings can be adjusted in the component files:
- `Orb.tsx`: Orb size, glow intensity, pulse scale
- `Rings.tsx`: Ring count, spacing, rotation speed
- `Sweeps.tsx`: Sweep line count, length, rotation speed
- `Starfield.tsx`: Particle count, size, animation speed

## 📱 Browser Compatibility

- Chrome/Edge (recommended)
- Firefox
- Safari
- Mobile browsers (for testing)

## 🚨 Troubleshooting

- **WebSocket Connection Failed**: Ensure Python backend is running
- **3D Performance Issues**: Check browser WebGL support
- **Audio Not Working**: Verify TTS integration in Python backend
