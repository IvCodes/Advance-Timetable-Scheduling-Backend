/**
 * Frontend Integration Example for Application-Aware Chatbot
 * 
 * This example shows how to integrate the enhanced chatbot system
 * with context awareness in a React/JavaScript frontend.
 */

// Example React Hook for Chatbot Integration
import { useState, useEffect, useContext } from 'react';
import { useLocation } from 'react-router-dom';

// Auth context to get user information
import { AuthContext } from '../contexts/AuthContext';

/**
 * Custom hook for chatbot integration with context awareness
 */
export const useChatbot = () => {
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [conversationId, setConversationId] = useState(null);
    
    const location = useLocation();
    const { user } = useContext(AuthContext);

    /**
     * Send a message to the chatbot with full context
     */
    const sendMessage = async (message) => {
        setIsLoading(true);
        
        try {
            // Add user message to chat
            const userMessage = {
                role: 'user',
                content: message,
                timestamp: new Date()
            };
            setMessages(prev => [...prev, userMessage]);

            // Prepare request with context
            const requestBody = {
                message: message,
                user_id: user?.id,
                current_page: location.pathname,  // Current page for context
                user_role: user?.role,           // User role for personalization
                conversation_id: conversationId
            };

            // Send to chatbot API
            const response = await fetch('/api/v1/chatbot/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${user?.token}`
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                throw new Error('Failed to get chatbot response');
            }

            const data = await response.json();

            // Add assistant response to chat
            const assistantMessage = {
                role: 'assistant',
                content: data.message,
                timestamp: new Date(),
                suggestions: data.suggestions || []
            };
            setMessages(prev => [...prev, assistantMessage]);

            // Update conversation ID
            if (data.conversation_id) {
                setConversationId(data.conversation_id);
            }

            return data;

        } catch (error) {
            console.error('Chatbot error:', error);
            
            // Add error message
            const errorMessage = {
                role: 'assistant',
                content: 'Sorry, I encountered an error. Please try again.',
                timestamp: new Date(),
                isError: true
            };
            setMessages(prev => [...prev, errorMessage]);
            
            throw error;
        } finally {
            setIsLoading(false);
        }
    };

    /**
     * Get page-specific greeting when user enters a new page
     */
    const getPageGreeting = async () => {
        if (!user || !location.pathname) return;

        try {
            const response = await fetch('/api/v1/chatbot/page-greeting', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${user?.token}`
                },
                body: JSON.stringify({
                    current_page: location.pathname,
                    user_role: user?.role
                })
            });

            if (response.ok) {
                const data = await response.json();
                if (data.greeting) {
                    const greetingMessage = {
                        role: 'assistant',
                        content: data.greeting,
                        timestamp: new Date(),
                        suggestions: data.help_topics || [],
                        isGreeting: true
                    };
                    setMessages(prev => [...prev, greetingMessage]);
                }
            }
        } catch (error) {
            console.error('Failed to get page greeting:', error);
        }
    };

    // Get page greeting when location changes
    useEffect(() => {
        getPageGreeting();
    }, [location.pathname, user?.role]);

    return {
        messages,
        sendMessage,
        isLoading,
        conversationId
    };
};

/**
 * Example ChatWidget Component
 */
export const ChatWidget = () => {
    const { messages, sendMessage, isLoading } = useChatbot();
    const [inputValue, setInputValue] = useState('');
    const [isOpen, setIsOpen] = useState(false);

    const handleSend = async () => {
        if (!inputValue.trim()) return;
        
        const message = inputValue.trim();
        setInputValue('');
        
        try {
            await sendMessage(message);
        } catch (error) {
            // Error handling is done in the hook
        }
    };

    const handleSuggestionClick = (suggestion) => {
        setInputValue(suggestion);
    };

    return (
        <div className={`chat-widget ${isOpen ? 'open' : 'closed'}`}>
            {/* Chat Toggle Button */}
            <button 
                className="chat-toggle"
                onClick={() => setIsOpen(!isOpen)}
            >
                💬 Assistant
            </button>

            {/* Chat Window */}
            {isOpen && (
                <div className="chat-window">
                    <div className="chat-header">
                        <h3>Timetable Assistant</h3>
                        <button onClick={() => setIsOpen(false)}>×</button>
                    </div>

                    {/* Messages */}
                    <div className="chat-messages">
                        {messages.map((message, index) => (
                            <div 
                                key={index} 
                                className={`message ${message.role} ${message.isError ? 'error' : ''}`}
                            >
                                <div className="message-content">
                                    {message.content}
                                </div>
                                
                                {/* Suggestions */}
                                {message.suggestions && message.suggestions.length > 0 && (
                                    <div className="suggestions">
                                        {message.suggestions.map((suggestion, idx) => (
                                            <button
                                                key={idx}
                                                className="suggestion-btn"
                                                onClick={() => handleSuggestionClick(suggestion)}
                                            >
                                                {suggestion}
                                            </button>
                                        ))}
                                    </div>
                                )}
                                
                                <div className="message-time">
                                    {message.timestamp.toLocaleTimeString()}
                                </div>
                            </div>
                        ))}
                        
                        {isLoading && (
                            <div className="message assistant loading">
                                <div className="typing-indicator">
                                    <span></span><span></span><span></span>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Input */}
                    <div className="chat-input">
                        <input
                            type="text"
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                            placeholder="Ask me about your timetable..."
                            disabled={isLoading}
                        />
                        <button 
                            onClick={handleSend}
                            disabled={isLoading || !inputValue.trim()}
                        >
                            Send
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

/**
 * Example usage in different pages
 */

// Teacher Allocation Report Page
export const TeacherAllocationPage = () => {
    const { sendMessage } = useChatbot();
    
    // Example: Contextual help button
    const explainWorkload = () => {
        sendMessage("What does workload percentage mean?");
    };

    return (
        <div className="teacher-allocation-page">
            <h1>Teacher Allocation Report</h1>
            
            {/* Report content */}
            <div className="report-stats">
                <div className="stat-card">
                    <h3>Total Teachers: 22</h3>
                    <button onClick={explainWorkload}>
                        ❓ What does this mean?
                    </button>
                </div>
                <div className="stat-card">
                    <h3>Average Workload: 30%</h3>
                    <button onClick={() => sendMessage("How is workload calculated?")}>
                        ❓ How is this calculated?
                    </button>
                </div>
            </div>
            
            {/* Chat widget automatically provides context */}
            <ChatWidget />
        </div>
    );
};

// Space Occupancy Report Page  
export const SpaceOccupancyPage = () => {
    const { sendMessage } = useChatbot();
    
    return (
        <div className="space-occupancy-page">
            <h1>Space Occupancy Report</h1>
            
            <div className="report-stats">
                <div className="stat-card">
                    <h3>Total Spaces: 30</h3>
                    <button onClick={() => sendMessage("Show me underutilized rooms")}>
                        📊 Find underused rooms
                    </button>
                </div>
                <div className="stat-card">
                    <h3>Average Occupancy: 5%</h3>
                    <button onClick={() => sendMessage("Why is occupancy so low?")}>
                        🤔 Why so low?
                    </button>
                </div>
            </div>
            
            <ChatWidget />
        </div>
    );
};

/**
 * CSS Styles (example)
 */
const styles = `
.chat-widget {
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 1000;
}

.chat-widget.closed .chat-window {
    display: none;
}

.chat-toggle {
    background: #007bff;
    color: white;
    border: none;
    padding: 12px 20px;
    border-radius: 25px;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0,123,255,0.3);
}

.chat-window {
    width: 350px;
    height: 500px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    display: flex;
    flex-direction: column;
    margin-bottom: 10px;
}

.chat-header {
    background: #007bff;
    color: white;
    padding: 15px;
    border-radius: 12px 12px 0 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 15px;
}

.message {
    margin-bottom: 15px;
}

.message.user {
    text-align: right;
}

.message.user .message-content {
    background: #007bff;
    color: white;
    padding: 10px 15px;
    border-radius: 18px 18px 4px 18px;
    display: inline-block;
    max-width: 80%;
}

.message.assistant .message-content {
    background: #f1f3f5;
    color: #333;
    padding: 10px 15px;
    border-radius: 18px 18px 18px 4px;
    display: inline-block;
    max-width: 80%;
}

.suggestions {
    margin-top: 10px;
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
}

.suggestion-btn {
    background: #e9ecef;
    border: 1px solid #dee2e6;
    padding: 5px 10px;
    border-radius: 15px;
    font-size: 12px;
    cursor: pointer;
    transition: background 0.2s;
}

.suggestion-btn:hover {
    background: #007bff;
    color: white;
}

.chat-input {
    padding: 15px;
    border-top: 1px solid #dee2e6;
    display: flex;
    gap: 10px;
}

.chat-input input {
    flex: 1;
    padding: 10px;
    border: 1px solid #dee2e6;
    border-radius: 20px;
    outline: none;
}

.chat-input button {
    background: #007bff;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 20px;
    cursor: pointer;
}

.typing-indicator {
    display: flex;
    gap: 4px;
    padding: 10px 15px;
}

.typing-indicator span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #007bff;
    animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
    animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
    animation-delay: 0.4s;
}

@keyframes typing {
    0%, 80%, 100% {
        transform: scale(0);
        opacity: 0.5;
    }
    40% {
        transform: scale(1);
        opacity: 1;
    }
}
`;

export default { useChatbot, ChatWidget, TeacherAllocationPage, SpaceOccupancyPage }; 