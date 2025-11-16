import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const Chatbot = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isOpen, setIsOpen] = useState(false);
    const messagesEndRef = useRef();

    // Styles inline
    const styles = {
        toggle: {
            position: 'fixed', bottom: '20px', right: '20px',
            background: '#1e3c72', color: 'white', border: 'none',
            padding: '12px 20px', borderRadius: '25px', cursor: 'pointer'
        },
        container: {
            position: 'fixed', bottom: '80px', right: '20px',
            width: '350px', height: '400px', background: 'white',
            borderRadius: '10px', boxShadow: '0 5px 20px rgba(0,0,0,0.2)',
            display: 'flex', flexDirection: 'column', zIndex: 1000
        },
        header: {
            background: '#1e3c72', color: 'white', padding: '15px',
            borderRadius: '10px 10px 0 0', display: 'flex', justifyContent: 'space-between'
        },
        messages: {
            flex: 1, padding: '15px', overflowY: 'auto'
        },
        messageUser: {
            textAlign: 'right', marginBottom: '10px'
        },
        messageBot: {
            textAlign: 'left', marginBottom: '10px'
        },
        messageContentUser: {
            display: 'inline-block', padding: '8px 12px',
            background: '#1e3c72', color: 'white', borderRadius: '15px',
            maxWidth: '80%'
        },
        messageContentBot: {
            display: 'inline-block', padding: '8px 12px',
            background: '#f1f1f1', color: '#333', borderRadius: '15px',
            maxWidth: '80%'
        },
        quickReplies: {
            marginTop: '5px'
        },
        quickReplyBtn: {
            background: 'white', border: '1px solid #1e3c72',
            color: '#1e3c72', padding: '4px 8px', borderRadius: '12px',
            fontSize: '12px', margin: '2px', cursor: 'pointer'
        },
        inputContainer: {
            display: 'flex', padding: '10px', borderTop: '1px solid #ddd'
        },
        input: {
            flex: 1, padding: '8px', border: '1px solid #ddd',
            borderRadius: '15px'
        },
        sendBtn: {
            background: '#1e3c72', color: 'white', border: 'none',
            padding: '8px 15px', borderRadius: '15px', marginLeft: '5px',
            cursor: 'pointer'
        }
    };

    useEffect(() => {
        if (isOpen && messages.length === 0) {
            setMessages([{
                id: 1, type: 'bot',
                content: 'Bienvenue ! Comment puis-je vous aider ?',
                quick_replies: ['Réserver', 'Horaires', 'Contact']
            }]);
        }
    }, [isOpen]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const sendMessage = async (quickReply = null) => {
        const message = quickReply || input;
        if (!message.trim()) return;

        setMessages(prev => [...prev, { 
            id: Date.now(), type: 'user', content: message 
        }]);
        setInput('');

        try {
            const response = await axios.post('http://localhost:5000/api/chat', { 
                message: message,
                user_id: 'user'
            });
            
            setMessages(prev => [...prev, { 
                id: Date.now() + 1, type: 'bot',
                content: response.data.response.content,
                quick_replies: response.data.response.quick_replies
            }]);
        } catch {
            setMessages(prev => [...prev, { 
                id: Date.now() + 1, type: 'bot',
                content: 'Erreur. Contact: +216 75 758 063',
                quick_replies: ['Réessayer']
            }]);
        }
    };

    if (!isOpen) {
        return (
            <button style={styles.toggle} onClick={() => setIsOpen(true)}>
                💬 Assistant
            </button>
        );
    }

    return (
        <div style={styles.container}>
            <div style={styles.header}>
                <h3 style={{margin: 0}}>Holiday Beach</h3>
                <button 
                    onClick={() => setIsOpen(false)}
                    style={{background: 'none', border: 'none', color: 'white', fontSize: '20px', cursor: 'pointer'}}
                >
                    ×
                </button>
            </div>

            <div style={styles.messages}>
                {messages.map(msg => (
                    <div key={msg.id} style={msg.type === 'user' ? styles.messageUser : styles.messageBot}>
                        <div style={msg.type === 'user' ? styles.messageContentUser : styles.messageContentBot}>
                            {msg.content}
                            {msg.quick_replies && (
                                <div style={styles.quickReplies}>
                                    {msg.quick_replies.map((reply, i) => (
                                        <button 
                                            key={i} 
                                            onClick={() => sendMessage(reply)}
                                            style={styles.quickReplyBtn}
                                        >
                                            {reply}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>

            <div style={styles.inputContainer}>
                <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder="Votre message..."
                    style={styles.input}
                />
                <button onClick={() => sendMessage()} style={styles.sendBtn}>
                    ➤
                </button>
            </div>
        </div>
    );
};

export default Chatbot;