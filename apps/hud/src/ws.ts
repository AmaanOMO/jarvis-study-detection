import { useHUDStore } from './store'

class WebSocketClient {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private url: string

  constructor(url: string = 'ws://localhost:8765') {
    this.url = url
  }

  connect() {
    try {
      console.log('🌐 Connecting to WebSocket server...')
      this.ws = new WebSocket(this.url)
      
      this.ws.onopen = this.onOpen.bind(this)
      this.ws.onmessage = this.onMessage.bind(this)
      this.ws.onclose = this.onClose.bind(this)
      this.ws.onerror = this.onError.bind(this)
      
    } catch (error) {
      console.error('❌ Failed to create WebSocket connection:', error)
      this.scheduleReconnect()
    }
  }

  private onOpen() {
    console.log('✅ WebSocket connected')
    this.reconnectAttempts = 0
    useHUDStore.getState().setConnected(true)
  }

  private onMessage(event: MessageEvent) {
    try {
      const data = JSON.parse(event.data)
      this.handleMessage(data)
    } catch (error) {
      console.error('❌ Failed to parse WebSocket message:', error)
    }
  }

  private handleMessage(data: any) {
    const { type, value, text, envelope } = data
    
    switch (type) {
      case 'connected':
        console.log('📨 Connected message:', data.message)
        break
        
      case 'status':
        console.log('📊 Status update:', value)
        useHUDStore.getState().setStatus(value)
        break
        
      case 'speak':
        console.log('🎤 Speak event:', text)
        useHUDStore.getState().setSpeaking(true, text)
        if (envelope) {
          useHUDStore.getState().setEnvelope(envelope)
        }
        break
        
      case 'playing':
        console.log('▶️ Playing state:', value)
        if (!value) {
          useHUDStore.getState().setSpeaking(false)
        }
        break
        
      case 'pong':
        // Keep alive response
        break
        
      default:
        console.log('📨 Unknown message type:', type, data)
    }
  }

  private onClose() {
    console.log('🔌 WebSocket disconnected')
    useHUDStore.getState().setConnected(false)
    this.scheduleReconnect()
  }

  private onError(error: Event) {
    console.error('❌ WebSocket error:', error)
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`🔄 Reconnecting in ${this.reconnectDelay}ms... (Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
      
      setTimeout(() => {
        this.connect()
      }, this.reconnectDelay)
      
      // Exponential backoff
      this.reconnectDelay *= 2
    } else {
      console.error('❌ Max reconnection attempts reached')
    }
  }

  sendClick() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = { type: 'click' }
      this.ws.send(JSON.stringify(message))
      console.log('🎯 Sent click event to server')
    } else {
      console.warn('⚠️ WebSocket not connected, cannot send click')
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
}

// Export singleton instance
export const wsClient = new WebSocketClient()

// Auto-connect on import
if (typeof window !== 'undefined') {
  wsClient.connect()
}
