<template>
  <div class="app-container">
    <header class="app-header">
      <div class="logo">
        <h1>Gemini Alert</h1>
      </div>
      <div class="user-info" v-if="user">
        <span>{{ user.displayName || user.email }}</span>
        <button @click="logout" class="logout-btn">Sign Out</button>
      </div>
    </header>

    <main class="main-content">
      <div class="alert-panel">
        <h2>Send Emergency Alert</h2>
        <p class="intro-text">Describe your situation in detail. This will be shared with people nearby who can help you.</p>

        <div class="emergency-type">
          <label>Emergency Type</label>
          <div class="type-buttons">
            <button
              v-for="type in emergencyTypes"
              :key="type.value"
              :class="['type-btn', { active: emergencyType === type.value }]"
              @click="emergencyType = type.value"
            >
              {{ type.label }}
            </button>
          </div>
        </div>

        <div class="message-input">
          <label for="alert-message">Message</label>
          <textarea
            id="alert-message"
            v-model="alertMessage"
            placeholder="Describe your situation in detail..."
            rows="4"
          ></textarea>
        </div>

        <div class="location-status">
          <span :class="['status-indicator', locationTracking ? 'active' : '']"></span>
          <span>{{ locationStatus }}</span>
        </div>

        <div v-if="locationErrorMessage" class="location-error">
          <span>{{ locationErrorMessage }}</span>
          <button
            v-if="mockLocation"
            class="demo-mode-badge"
            @click="alertMessage = 'Help! This is a test emergency alert from the Gemini Alert app.'"
          >
            Using Demo Mode
          </button>
        </div>

        <div class="button-group">
          <button
            @click="sendAlert"
            :disabled="!canSendAlert || isLoading"
            class="send-alert-btn"
          >
            {{ isLoading ? 'Sending...' : 'Send Emergency Alert' }}
          </button>

          <button
            @click="showGeminiPanel = !showGeminiPanel"
            class="ask-gemini-toggle-btn"
          >
            {{ showGeminiPanel ? 'Hide Gemini AI' : 'Ask Gemini AI' }}
          </button>
        </div>

        <div v-if="alertSent" class="alert-success">
          <h3>Alert Sent!</h3>
          <p>{{ notificationMessage }}</p>
        </div>

        <div v-if="showGeminiPanel" class="gemini-panel">
          <h3>Ask Gemini AI for Help</h3>
          <p class="gemini-intro">Need advice or tips for a crisis situation? Ask Gemini AI for help.</p>

          <div class="chat-container">
            <!-- Chat messages go here -->
            <div v-if="chatHistory.length === 0" class="empty-chat">
              <p>Start a conversation with Gemini. Ask for emergency assistance, safety tips, or how to respond to specific situations.</p>
            </div>
            
            <div v-else class="chat-messages">
              <div 
                v-for="(message, index) in chatHistory" 
                :key="index" 
                :class="['chat-message', message.sender === 'user' ? 'user-message' : 'ai-message']"
              >
                <div class="message-avatar">
                  <span v-if="message.sender === 'user'">👤</span>
                  <span v-else>🤖</span>
                </div>
                <div class="message-bubble">
                  <div v-if="message.sender === 'ai' && isMockResponseMessage(message)" class="mock-response-badge">
                    MOCK RESPONSE
                  </div>
                  <div 
                    class="message-text" 
                    v-html="formatMessageText(message.text)"
                  ></div>
                  <div class="message-actions" v-if="message.sender === 'ai'">
                    <button
                      @click="speakMessage(message.text)"
                      :disabled="isSpeaking"
                      class="message-action-btn"
                      title="Listen to this message"
                    >
                      <i class="speaker-icon">🔊</i>
                    </button>
                    <button
                      @click="copyMessage(message.text)"
                      class="message-action-btn"
                      title="Copy message to clipboard"
                    >
                      <i class="copy-icon">📋</i>
                    </button>
                  </div>
                </div>
              </div>
              
              <!-- Loading indicator for streaming responses -->
              <div v-if="geminiLoading" class="chat-message ai-message">
                <div class="message-avatar">
                  <span>🤖</span>
                </div>
                <div class="message-bubble typing-indicator">
                  <span class="dot"></span>
                  <span class="dot"></span>
                  <span class="dot"></span>
                </div>
              </div>
            </div>
          </div>

          <div class="chat-input-area">
            <textarea
              v-model="geminiQuestion"
              placeholder="Type your message here..."
              rows="2"
              class="chat-input"
              @keydown.enter.prevent="handleEnterKey"
            ></textarea>
            
            <div class="chat-controls">
              <button
                @click="toggleVoiceInput"
                :class="['voice-input-btn', { active: isListening }]"
                :disabled="!isSpeechRecognitionAvailable"
                :title="isSpeechRecognitionAvailable ? 'Click to use voice input' : 'Speech recognition not available in your browser'"
              >
                <span v-if="isListening">🎤</span>
                <span v-else>🎤</span>
              </button>
              
              <button
                @click="askGeminiAI"
                :disabled="!geminiQuestion.trim() || geminiLoading"
                class="send-message-btn"
              >
                <span v-if="geminiLoading">⏳</span>
                <span v-else>📤</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="map-container">
        <h2>Nearby Users</h2>
        <div id="map" ref="mapElement"></div>

        <div class="nearby-users">
          <h3>People Who Can Help</h3>
          <div v-if="nearbyUsers.length === 0" class="no-users">
            <p>No users nearby at the moment.</p>
          </div>
          <ul v-else class="user-list">
            <li v-for="user in nearbyUsers" :key="user.uid" class="user-item">
              <div class="user-info">
                <strong>{{ user.displayName }}</strong>
                <span>{{ formatDistance(user.distance) }} away</span>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </main>

    <div v-if="nearbyAlerts.length > 0" class="alerts-panel">
      <h2>Active Alerts Nearby</h2>
      <ul class="alert-list">
        <li
          v-for="alert in nearbyAlerts"
          :key="alert.id"
          :class="['alert-item', { 'own-alert': alert.isOwnAlert }]"
        >
          <div class="alert-header">
            <span class="alert-type">{{ alert.emergencyType }}</span>
            <span class="alert-distance">{{ formatDistance(alert.distance) }}</span>
          </div>
          <div class="alert-body">
            <p class="alert-message">{{ alert.message }}</p>
            <div class="alert-meta">
              <span>From: {{ alert.userName }}</span>
              <span>{{ formatTime(alert.createdAt) }}</span>
            </div>
          </div>
          <div class="alert-actions" v-if="!alert.isOwnAlert">
            <button @click="respondToAlert(alert.id)" class="respond-btn">Respond</button>
          </div>
        </li>
      </ul>
    </div>

    <div v-if="showResponseModal" class="modal-overlay">
      <div class="modal-content">
        <h3>Respond to Alert</h3>
        <p>Send a message to the person in need:</p>
        <textarea
          v-model="responseMessage"
          placeholder="How can you help? (e.g., 'I'm nearby and can assist')"
          rows="3"
        ></textarea>
        <div class="modal-actions">
          <button @click="showResponseModal = false" class="cancel-btn">Cancel</button>
          <button @click="submitResponse" :disabled="!responseMessage.trim()" class="submit-btn">
            Send Response
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { auth } from '../firebase'
import { signOut, onAuthStateChanged } from 'firebase/auth'
import {
  startLocationTracking,
  stopLocationTracking,
  findNearbyUsers
} from '../services/locationService'
import {
  sendEmergencyAlert,
  getNearbyAlerts,
  respondToAlert as respondToAlertService
} from '../services/alertService'
import {
  initMap,
  centerMapOnUserLocation,
  showNearbyUsers,
  showAlerts,
  cleanupMap
} from '../services/mapService'
import { askGemini, askGeminiStream } from '../services/geminiService'

export default {
  name: 'HomePage',

  setup() {
    // User state
    const user = ref(null)
    const router = useRouter()

    // Map references
    const mapElement = ref(null)
    const mapAvailable = ref(false)

    // UI state
    const showGeminiPanel = ref(false)

    // Alert form
    const alertMessage = ref('')
    const emergencyType = ref('general')
    const isLoading = ref(false)
    const alertSent = ref(false)
    const notificationMessage = ref('')

    // Gemini chat
    const geminiQuestion = ref('')
    const geminiResponse = ref('')
    const geminiLoading = ref(false)
    const chatHistory = ref([])  // Store conversation history

    // Location tracking
    const locationTracking = ref(false)
    const locationStatus = ref('Location tracking inactive')
    const locationErrorMessage = ref('')
    const mockLocation = ref(false) // For testing when geolocation is not available

    // Nearby users and alerts
    const nearbyUsers = ref([])
    const nearbyAlerts = ref([])

    // Response modal
    const showResponseModal = ref(false)
    const responseMessage = ref('')
    const currentAlertId = ref(null)

    // Emergency types
    const emergencyTypes = [
      { label: 'General', value: 'general' },
      { label: 'Medical', value: 'medical' },
      { label: 'Safety', value: 'safety' },
      { label: 'Harassment', value: 'harassment' }
    ]

    // Voice recognition and speech synthesis
    const isListening = ref(false)
    const isSpeaking = ref(false)
    const speechRecognition = ref(null)
    const speechSynthesis = ref(window.speechSynthesis || null)
    const isSpeechRecognitionAvailable = ref(false)

    // Computed properties
    const canSendAlert = computed(() => {
      return alertMessage.value.trim().length > 0 && locationTracking.value;
    })

    const formattedGeminiResponse = computed(() => {
      if (!geminiResponse.value) return '';
      // Convert line breaks to <br> for HTML display
      return geminiResponse.value.replace(/\n/g, '<br>');
    })

    const isMockResponse = computed(() => {
      // Check if the response contains the mock response identifier text
      return geminiResponse.value && geminiResponse.value.includes('mock response because no valid Gemini API key');
    });

    // Methods
    const initializeMap = async () => {
      try {
        await initMap('map')
        mapAvailable.value = true

        try {
          const location = await centerMapOnUserLocation(5) // 5km radius
          console.log('Map centered at:', location)

          // Show nearby users on map
          await refreshNearbyUsers()

          // Show nearby alerts
          await refreshNearbyAlerts()
        } catch (geoError) {
          console.error('Geolocation error:', geoError)
          if (geoError.code === 1) { // Permission denied
            locationErrorMessage.value = 'Location permission denied. Please enable location access to use all features.'
          } else if (geoError.code === 2) { // Position unavailable
            locationErrorMessage.value = 'Unable to determine your location. Please try again later.'
          } else if (geoError.code === 3) { // Timeout
            locationErrorMessage.value = 'Location request timed out. Using default location.'
          } else {
            locationErrorMessage.value = 'Error getting location: ' + geoError.message
          }

          // Use a default location for development
          mockLocation.value = true
          locationStatus.value = 'Using demo location'
        }
      } catch (mapError) {
        console.error('Error initializing map:', mapError)
        mapAvailable.value = false
        locationStatus.value = 'Map service unavailable'
        locationErrorMessage.value = 'Google Maps could not be loaded. Some features will be limited.'
      }
    }

    const startTracking = async () => {
      try {
        // Check for mock mode first
        if (mockLocation.value) {
          locationTracking.value = true
          locationStatus.value = 'Using demo location'
          return true
        }

        const started = await startLocationTracking()
        locationTracking.value = started
        locationStatus.value = started
          ? 'Location tracking active'
          : 'Error starting location tracking'

        if (!started) {
          // Fall back to mock location if tracking fails
          mockLocation.value = true
          locationTracking.value = true
          locationStatus.value = 'Using demo location'
        }

        return locationTracking.value
      } catch (error) {
        console.error('Error starting location tracking:', error)
        locationTracking.value = false
        locationStatus.value = 'Error starting location tracking'

        // Fall back to mock location
        mockLocation.value = true
        locationTracking.value = true
        locationStatus.value = 'Using demo location'

        return locationTracking.value
      }
    }

    const refreshNearbyUsers = async () => {
      try {
        if (mockLocation.value) {
          // Use mock data for development
          nearbyUsers.value = [
            { uid: 'mock1', displayName: 'Demo User 1', distance: 0.8 },
            { uid: 'mock2', displayName: 'Demo User 2', distance: 1.5 },
            { uid: 'mock3', displayName: 'Demo User 3', distance: 2.3 }
          ]
          return
        }

        // Find users within 5km
        const users = await findNearbyUsers(5)
        nearbyUsers.value = users

        // Show users on map
        if (mapAvailable.value) {
          await showNearbyUsers(5)
        }
      } catch (error) {
        console.error('Error finding nearby users:', error)
        // Use mock data when real data can't be fetched
        if (nearbyUsers.value.length === 0) {
          nearbyUsers.value = [
            { uid: 'mock1', displayName: 'Demo User 1', distance: 0.8 },
            { uid: 'mock2', displayName: 'Demo User 2', distance: 1.5 }
          ]
        }
      }
    }

    const refreshNearbyAlerts = async () => {
      try {
        if (mockLocation.value) {
          // Use mock data for development
          nearbyAlerts.value = [
            {
              id: 'mock1',
              userId: 'mock-user-1',
              userName: 'Demo Alert Sender',
              message: 'This is a demonstration alert. In a real emergency, detailed information would appear here.',
              emergencyType: 'general',
              distance: 1.2,
              createdAt: new Date(),
              isOwnAlert: false
            }
          ]
          return
        }

        // Get alerts within 10km
        const alerts = await getNearbyAlerts(10)
        nearbyAlerts.value = alerts

        // Show alerts on map
        if (mapAvailable.value) {
          await showAlerts(alerts)
        }
      } catch (error) {
        console.error('Error getting nearby alerts:', error)
        // Use mock data when real data can't be fetched
        if (nearbyAlerts.value.length === 0) {
          nearbyAlerts.value = [
            {
              id: 'mock1',
              userId: 'mock-user-1',
              userName: 'Demo Alert Sender',
              message: 'This is a demonstration alert. In a real emergency, detailed information would appear here.',
              emergencyType: 'general',
              distance: 1.2,
              createdAt: new Date(),
              isOwnAlert: false
            }
          ]
        }
      }
    }
    
    const sendAlert = async () => {
      if (!canSendAlert.value) return
      
      isLoading.value = true
      alertSent.value = false
      
      try {
        if (mockLocation.value) {
          // Simulate sending an alert in demo mode
          console.log('Demo mode: Simulating alert send')
          
          setTimeout(() => {
            alertSent.value = true
            notificationMessage.value = 'Demo mode: Alert simulated. In a real app, nearby users would be notified.'
            
            // Add the user's alert to the list
            nearbyAlerts.value.unshift({
              id: 'user-mock-' + Date.now(),
              userId: auth.currentUser.uid,
              userName: auth.currentUser.displayName || auth.currentUser.email,
              message: alertMessage.value,
              emergencyType: emergencyType.value,
              distance: 0,
              createdAt: new Date(),
              isOwnAlert: true
            })
            
            isLoading.value = false
          }, 1500)
          
          return
        }
        
        // Send real alert
        await sendEmergencyAlert(alertMessage.value, emergencyType.value)
        
        alertSent.value = true
        notificationMessage.value = 'Your alert has been sent to users in your area.'
        
        // Refresh alerts to include the one we just sent
        await refreshNearbyAlerts()
      } catch (error) {
        console.error('Error sending alert:', error)
        alertSent.value = true
        notificationMessage.value = 'There was an error sending your alert. Please try again.'
      } finally {
        isLoading.value = false
      }
    }
    
    const askGeminiAI = async () => {
      if (!geminiQuestion.value.trim()) return;
      
      // Add the user's message to chat history
      chatHistory.value.push({
        sender: 'user',
        text: geminiQuestion.value,
        timestamp: new Date()
      });
      
      // Store the question
      const question = geminiQuestion.value;
      
      // Clear the input field so the user can type a new message
      geminiQuestion.value = '';
      
      geminiLoading.value = true;
      geminiResponse.value = '';
      
      try {
        // Use the streaming API for a more interactive experience
        let fullResponse = '';
        const handleChunk = (chunk) => {
          fullResponse += chunk;
          geminiResponse.value = fullResponse;
          
          // Update the last AI message or add a new one if it doesn't exist yet
          if (chatHistory.value.length > 0 && chatHistory.value[chatHistory.value.length - 1].sender === 'ai') {
            chatHistory.value[chatHistory.value.length - 1].text = fullResponse;
          } else {
            chatHistory.value.push({
              sender: 'ai',
              text: fullResponse,
              timestamp: new Date()
            });
          }
        };
        
        await askGeminiStream(question, handleChunk);
      } catch (error) {
        console.error('Error asking Gemini:', error);
        const errorMessage = 'Sorry, there was an error getting a response. Please try again later.';
        geminiResponse.value = errorMessage;
        
        // Add error message to chat history
        chatHistory.value.push({
          sender: 'ai',
          text: errorMessage,
          timestamp: new Date(),
          isError: true
        });
      } finally {
        geminiLoading.value = false;
      }
    };
    
    const respondToAlert = (alertId) => {
      currentAlertId.value = alertId
      showResponseModal.value = true
    }
    
    const submitResponse = async () => {
      if (!responseMessage.value.trim() || !currentAlertId.value) return
      
      try {
        await respondToAlertService(currentAlertId.value, responseMessage.value)
        showResponseModal.value = false
        responseMessage.value = ''
        currentAlertId.value = null
      } catch (error) {
        console.error('Error sending response:', error)
      }
    }
    
    const logout = async () => {
      try {
        // Stop location tracking
        stopLocationTracking()
        
        // Clean up map
        cleanupMap()
        
        // Sign out
        await signOut(auth)
        
        // Navigate to login
        router.push('/login')
      } catch (error) {
        console.error('Error logging out:', error)
      }
    }
    
    // Helper functions
    const formatDistance = (distance) => {
      if (distance < 1) {
        return `${Math.round(distance * 1000)} m`
      }
      return `${distance.toFixed(1)} km`
    }
    
    const formatTime = (dateTime) => {
      const date = new Date(dateTime)
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
    
    // Chat functionality
    const formatMessageText = (text) => {
      if (!text) return '';
      // Convert line breaks to <br> for HTML display
      return text.replace(/\n/g, '<br>');
    }
    
    const isMockResponseMessage = (message) => {
      return message.sender === 'ai' && message.text && message.text.includes('mock response because no valid Gemini API key');
    }
    
    const handleEnterKey = (event) => {
      // Only proceed if not Shift+Enter and there's content to send
      if (!event.shiftKey && geminiQuestion.value.trim()) {
        askGeminiAI();
      }
    }
    
    // Voice functionality
    const toggleVoiceInput = () => {
      if (!speechRecognition.value) {
        console.warn('Speech recognition not available')
        return
      }
      
      if (isListening.value) {
        speechRecognition.value.stop()
      } else {
        // Clear the input first
        if (!geminiQuestion.value.trim()) {
          geminiQuestion.value = ''
        }
        
        try {
          speechRecognition.value.start()
        } catch (error) {
          console.error('Error starting speech recognition:', error)
        }
      }
    }
    
    const speakMessage = (text) => {
      if (!speechSynthesis.value) {
        console.warn('Speech synthesis not available')
        return
      }
      
      if (isSpeaking.value) {
        speechSynthesis.value.cancel()
        isSpeaking.value = false
        return
      }
      
      // Strip HTML tags from response
      const plainText = text.replace(/<[^>]*>/g, '')
      
      const utterance = new SpeechSynthesisUtterance(plainText)
      utterance.lang = 'en-US'
      utterance.rate = 1.0
      utterance.pitch = 1.0
      
      utterance.onstart = () => {
        isSpeaking.value = true
      }
      
      utterance.onend = () => {
        isSpeaking.value = false
      }
      
      utterance.onerror = (event) => {
        console.error('Speech synthesis error:', event)
        isSpeaking.value = false
      }
      
      speechSynthesis.value.speak(utterance)
    }
    
    // For backward compatibility
    const speakResponse = () => {
      if (geminiResponse.value) {
        speakMessage(geminiResponse.value);
      }
    }
    
    const copyMessage = (text) => {
      const plainText = text.replace(/<[^>]*>/g, '')
      navigator.clipboard.writeText(plainText)
        .then(() => {
          alert('Message copied to clipboard')
        })
        .catch(err => {
          console.error('Error copying to clipboard:', err)
        })
    }
    
    // For backward compatibility
    const copyResponse = () => {
      if (geminiResponse.value) {
        copyMessage(geminiResponse.value);
      }
    }
    
    // Initialize speech recognition if available
    const initSpeechRecognition = () => {
      // Check if the browser supports SpeechRecognition
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      
      if (!SpeechRecognition) {
        console.warn('Speech recognition not supported in this browser')
        isSpeechRecognitionAvailable.value = false
        return
      }
      
      isSpeechRecognitionAvailable.value = true
      
      try {
        speechRecognition.value = new SpeechRecognition()
        speechRecognition.value.continuous = false
        speechRecognition.value.interimResults = true
        speechRecognition.value.lang = 'en-US'
        
        speechRecognition.value.onstart = () => {
          isListening.value = true
        }
        
        speechRecognition.value.onend = () => {
          isListening.value = false
        }
        
        speechRecognition.value.onresult = (event) => {
          const transcript = event.results[0][0].transcript
          geminiQuestion.value = transcript
        }
        
        speechRecognition.value.onerror = (event) => {
          console.error('Speech recognition error:', event.error)
          isListening.value = false
        }
      } catch (error) {
        console.error('Error initializing speech recognition:', error)
        isSpeechRecognitionAvailable.value = false
      }
    }
    
    // Lifecycle hooks
    onMounted(() => {
      // Check if user is logged in
      onAuthStateChanged(auth, (currentUser) => {
        user.value = currentUser
        if (!currentUser) {
          router.push('/login')
          return
        }
        
        // Start location tracking
        startTracking()
        
        // Initialize map
        if (mapElement.value) {
          initializeMap()
        }
        
        // Set up refresh intervals
        const userInterval = setInterval(refreshNearbyUsers, 30000) // Every 30 seconds
        const alertInterval = setInterval(refreshNearbyAlerts, 15000) // Every 15 seconds
        
        // Clean up intervals on component unmount
        onBeforeUnmount(() => {
          clearInterval(userInterval)
          clearInterval(alertInterval)
        })
        
        // Initialize speech recognition
        initSpeechRecognition()
      })
    })

    return {
      user,
      mapElement,
      showGeminiPanel,
      alertMessage,
      emergencyType,
      emergencyTypes,
      isLoading,
      alertSent,
      notificationMessage,
      geminiQuestion,
      geminiResponse,
      geminiLoading,
      formattedGeminiResponse,
      chatHistory,
      locationTracking,
      locationStatus,
      locationErrorMessage,
      mockLocation,
      nearbyUsers,
      nearbyAlerts,
      showResponseModal,
      responseMessage,
      canSendAlert,
      sendAlert,
      askGeminiAI,
      logout,
      respondToAlert,
      submitResponse,
      formatDistance,
      formatTime,
      formatMessageText,
      isMockResponseMessage,
      handleEnterKey,
      isListening,
      isSpeaking,
      isSpeechRecognitionAvailable,
      toggleVoiceInput,
      speakMessage,
      speakResponse,
      copyMessage,
      copyResponse,
      isMockResponse
    }
  }
}
</script>

<style scoped>
.app-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 0;
  border-bottom: 1px solid #e0e0e0;
  margin-bottom: 1.5rem;
}

.logo h1 {
  color: #3f51b5;
  margin: 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logout-btn {
  background-color: transparent;
  border: 1px solid #d32f2f;
  color: #d32f2f;
  border-radius: 4px;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.logout-btn:hover {
  background-color: #d32f2f;
  color: white;
}

.main-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
}

@media (max-width: 768px) {
  .main-content {
    grid-template-columns: 1fr;
  }
}

.alert-panel, .map-container {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
}

.intro-text {
  margin-bottom: 1.5rem;
  color: #666;
}

.emergency-type {
  margin-bottom: 1.5rem;
}

.type-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.type-btn {
  border: 1px solid #3f51b5;
  background-color: white;
  color: #3f51b5;
  border-radius: 4px;
  padding: 0.5rem 1rem;
  transition: all 0.2s;
}

.type-btn.active, .type-btn:hover {
  background-color: #3f51b5;
  color: white;
}

.message-input {
  margin-bottom: 1.5rem;
}

.message-input label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
}

.message-input textarea {
  width: 100%;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 0.75rem;
  font-family: inherit;
  resize: vertical;
}

.location-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.status-indicator {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #ccc;
}

.status-indicator.active {
  background-color: #4caf50;
}

.location-error {
  margin-bottom: 1rem;
  padding: 0.5rem;
  background-color: #ffebee;
  border-radius: 4px;
  font-size: 0.875rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.demo-mode-badge {
  background-color: #ff9800;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
}

.button-group {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.send-alert-btn {
  background-color: #d32f2f;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.75rem 1.5rem;
  font-weight: bold;
  flex: 1;
  transition: background-color 0.2s;
}

.send-alert-btn:hover:not(:disabled) {
  background-color: #b71c1c;
}

.send-alert-btn:disabled {
  background-color: #e0e0e0;
  color: #9e9e9e;
  cursor: not-allowed;
}

.ask-gemini-toggle-btn {
  background-color: #3f51b5;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.75rem 1.5rem;
  transition: background-color 0.2s;
}

.ask-gemini-toggle-btn:hover {
  background-color: #303f9f;
}

.alert-success {
  background-color: #e8f5e9;
  border-radius: 4px;
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.alert-success h3 {
  color: #4caf50;
  margin-top: 0;
}

.gemini-panel {
  background-color: #f3f3fd;
  border-radius: 4px;
  padding: 1rem;
  margin-top: 1rem;
  border: 1px solid #ddd;
  display: flex;
  flex-direction: column;
  height: 500px;
}

.gemini-intro {
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  color: #555;
}

/* Chat container styles */
.chat-container {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 1rem;
  border-radius: 4px;
  background-color: white;
  border: 1px solid #e0e0e0;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
  text-align: center;
  padding: 2rem;
}

.chat-messages {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow-y: auto;
}

.chat-message {
  display: flex;
  margin-bottom: 0.5rem;
}

.message-avatar {
  font-size: 1.5rem;
  margin-right: 0.5rem;
  align-self: flex-start;
}

.message-bubble {
  position: relative;
  padding: 0.75rem;
  border-radius: 18px;
  max-width: 80%;
  word-break: break-word;
}

.user-message {
  justify-content: flex-end;
}

.user-message .message-avatar {
  order: 2;
  margin-right: 0;
  margin-left: 0.5rem;
}

.user-message .message-bubble {
  background-color: #3f51b5;
  color: white;
  border-top-right-radius: 4px;
}

.ai-message .message-bubble {
  background-color: #f0f0f0;
  color: #333;
  border-top-left-radius: 4px;
}

.message-text {
  line-height: 1.4;
  font-size: 0.95rem;
}

.message-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
  justify-content: flex-end;
}

.message-action-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  padding: 0.25rem;
  border-radius: 4px;
  transition: background-color 0.2s;
  opacity: 0.6;
}

.message-action-btn:hover {
  opacity: 1;
  background-color: rgba(0, 0, 0, 0.05);
}

.typing-indicator {
  display: flex;
  align-items: center;
  padding: 0.5rem 1rem;
  gap: 0.3rem;
}

.mock-response-badge {
  background-color: #ff9800;
  color: white;
  font-size: 0.7rem;
  padding: 0.1rem 0.3rem;
  border-radius: 2px;
  margin-bottom: 0.5rem;
  display: inline-block;
}

/* Input area styles */
.chat-input-area {
  display: flex;
  flex-direction: column;
  background-color: white;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  margin-top: auto;
}

.chat-input {
  width: 100%;
  padding: 0.75rem;
  border: none;
  outline: none;
  resize: none;
  font-family: inherit;
  font-size: 0.95rem;
}

.chat-controls {
  display: flex;
  border-top: 1px solid #eee;
  background-color: #f9f9f9;
  padding: 0.5rem;
}

.voice-input-btn {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.voice-input-btn:hover:not(:disabled) {
  background-color: rgba(0, 0, 0, 0.05);
}

.voice-input-btn.active {
  color: #d32f2f;
}

.voice-input-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-message-btn {
  margin-left: auto;
  background-color: #3f51b5;
  color: white;
  border: none;
  border-radius: 50%;
  width: 2.5rem;
  height: 2.5rem;
  font-size: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 0.2s;
}

.send-message-btn:hover:not(:disabled) {
  background-color: #303f9f;
}

.send-message-btn:disabled {
  background-color: #e0e0e0;
  color: #9e9e9e;
  cursor: not-allowed;
}

.dot {
  width: 8px;
  height: 8px;
  background-color: #3f51b5;
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

.dot:nth-child(2) {
  animation-delay: 0.3s;
}

.dot:nth-child(3) {
  animation-delay: 0.6s;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.3;
  }
  50% {
    opacity: 1;
  }
}

#map {
  height: 300px;
  width: 100%;
  margin-bottom: 1.5rem;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
}

.nearby-users h3 {
  margin-top: 0;
  margin-bottom: 1rem;
}

.no-users {
  color: #757575;
  font-style: italic;
}

.user-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.user-item {
  border-bottom: 1px solid #e0e0e0;
  padding: 0.75rem 0;
}

.user-item:last-child {
  border-bottom: none;
}

.user-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.alerts-panel {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.alert-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.alert-item {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.alert-item.own-alert {
  border-color: #3f51b5;
  background-color: #f5f5ff;
}

.alert-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.alert-type {
  background-color: #3f51b5;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  text-transform: capitalize;
}

.alert-body {
  margin-bottom: 1rem;
}

.alert-message {
  margin: 0.5rem 0;
}

.alert-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #757575;
}

.alert-actions {
  display: flex;
  justify-content: flex-end;
}

.respond-btn {
  background-color: #4caf50;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  transition: background-color 0.2s;
}

.respond-btn:hover {
  background-color: #3d8b40;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 100;
}

.modal-content {
  background-color: white;
  border-radius: 8px;
  padding: 1.5rem;
  width: 90%;
  max-width: 500px;
}

.modal-content h3 {
  margin-top: 0;
}

.modal-content textarea {
  width: 100%;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 0.75rem;
  margin: 1rem 0;
  font-family: inherit;
  resize: vertical;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

.cancel-btn {
  background-color: transparent;
  border: 1px solid #757575;
  color: #757575;
  border-radius: 4px;
  padding: 0.5rem 1rem;
}

.submit-btn {
  background-color: #3f51b5;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.5rem 1rem;
}

.submit-btn:disabled {
  background-color: #e0e0e0;
  color: #9e9e9e;
  cursor: not-allowed;
}
</style>