import React, { useState, useEffect, useCallback } from 'react'
import ChatInterface from './components/ChatInterface'
import Sidebar from './components/Sidebar'
import { getDocuments, uploadDocument, deleteDocument, sendMessage } from './services/api'
import './App.css'

function generateId() {
    return Math.random().toString(36).substring(2, 9)
}

function generateTitle(firstMessage, documents) {
    if (firstMessage) {
        const clean = firstMessage.replace(/["']/g, '').trim()
        return clean.length > 30 ? clean.substring(0, 30) + '...' : clean
    }
    if (documents && documents.length === 1) {
        return documents[0].filename
    }
    return 'New Chat'
}

function App() {
    const [sidebarOpen, setSidebarOpen] = useState(true)
    const [conversations, setConversations] = useState(() => {
        const saved = localStorage.getItem('rag_conversations')
        return saved ? JSON.parse(saved) : []
    })
    const [activeConversationId, setActiveConversationId] = useState(null)
    const [documents, setDocuments] = useState([])
    const [isUploading, setIsUploading] = useState(false)
    const [uploadError, setUploadError] = useState(null)

    const activeConversation = conversations.find(c => c.id === activeConversationId)

    useEffect(() => {
        localStorage.setItem('rag_conversations', JSON.stringify(conversations))
    }, [conversations])

    useEffect(() => {
        fetchDocuments()
    }, [])

    const fetchDocuments = async () => {
        try {
            const res = await getDocuments()
            setDocuments(res.data.documents || [])
        } catch (err) {
            console.error('Failed to fetch documents', err)
        }
    }

    const handleNewChat = useCallback(() => {
        const newConv = {
            id: generateId(),
            title: 'New Chat',
            sessionId: null,
            messages: [],
            documentIds: [],
            createdAt: Date.now()
        }
        setConversations(prev => [newConv, ...prev])
        setActiveConversationId(newConv.id)
    }, [])

    useEffect(() => {
        if (conversations.length === 0) {
            handleNewChat()
        } else if (!activeConversationId) {
            setActiveConversationId(conversations[0].id)
        }
    }, [conversations.length, activeConversationId, handleNewChat])

    const handleSelectConversation = (id) => {
        setActiveConversationId(id)
    }

    const handleDeleteConversation = (id) => {
        setConversations(prev => prev.filter(c => c.id !== id))
        if (activeConversationId === id) {
            const remaining = conversations.filter(c => c.id !== id)
            setActiveConversationId(remaining.length > 0 ? remaining[0].id : null)
        }
    }

    const handleUploadDocument = async (file) => {
        setIsUploading(true)
        setUploadError(null)
        try {
            const res = await uploadDocument(file)
            await fetchDocuments()
            // Show uploaded document as a chat bubble
            setConversations(prev => prev.map(c => {
                if (c.id !== activeConversationId) return c
                return {
                    ...c,
                    messages: [...c.messages, { role: 'document', content: res.data.filename, documentId: res.data.id }]
                }
            }))
            // Track document ID in this conversation
            setConversations(prev => prev.map(c => {
                if (c.id !== activeConversationId) return c
                return {
                    ...c,
                    documentIds: [...(c.documentIds || []), res.data.id]
                }
            }))
            if (activeConversation?.title === 'New Chat' && activeConversation?.messages.length === 0) {
                const newTitle = generateTitle(null, [{ filename: res.data.filename }])
                setConversations(prev => prev.map(c =>
                    c.id === activeConversationId ? { ...c, title: newTitle } : c
                ))
            }

            setIsUploading(false)
            return res.data
        } catch (err) {
            setUploadError(err.response?.data?.detail || 'Upload failed')
            setIsUploading(false)
            throw err
        }
    }

    const handleDeleteDocument = async (docId) => {
        try {
            await deleteDocument(docId)
            await fetchDocuments()
        } catch (err) {
            console.error('Delete failed', err)
        }
    }

    const handleSendMessage = async (question) => {
        if (!activeConversation) return

        setConversations(prev => prev.map(c => {
            if (c.id !== activeConversationId) return c
            const updatedMessages = [...c.messages, { role: 'user', content: question, citations: [] }]
            const newTitle = (c.title === 'New Chat' && c.messages.length === 0)
                ? generateTitle(question, documents)
                : c.title
            return { ...c, messages: updatedMessages, title: newTitle }
        }))

        try {
            const res = await sendMessage(question, activeConversation.sessionId, activeConversation.documentIds || [])
            const data = res.data

            const aiMsg = {
                role: 'assistant',
                content: data.answer,
                citations: data.citations || [],
                retrievalScore: data.retrieval_score,
                queryRewritten: data.query_rewritten,
                retryCount: data.retry_count
            }

            setConversations(prev => prev.map(c => {
                if (c.id !== activeConversationId) return c
                return {
                    ...c,
                    messages: [...c.messages, aiMsg],
                    sessionId: data.session_id || c.sessionId
                }
            }))
        } catch (err) {
            setConversations(prev => prev.map(c => {
                if (c.id !== activeConversationId) return c
                return {
                    ...c,
                    messages: [...c.messages, {
                        role: 'assistant',
                        content: 'Sorry, I encountered an error. Please try again.',
                        citations: [],
                        isError: true
                    }]
                }
            }))
        }
    }

    return (
        <div className="app">
            <Sidebar
                isOpen={sidebarOpen}
                onToggle={() => setSidebarOpen(!sidebarOpen)}
                conversations={conversations}
                activeConversationId={activeConversationId}
                onSelectConversation={handleSelectConversation}
                onNewChat={handleNewChat}
                onDeleteConversation={handleDeleteConversation}
                documents={documents}
                onDeleteDocument={handleDeleteDocument}
            />
            <div className={`main-content ${sidebarOpen ? 'sidebar-open' : ''}`}>
                {activeConversation && (
                    <ChatInterface
                        messages={activeConversation.messages}
                        sessionId={activeConversation.sessionId}
                        onSendMessage={handleSendMessage}
                        onUploadDocument={handleUploadDocument}
                        isUploading={isUploading}
                        uploadError={uploadError}
                        documents={documents}
                    />
                )}
            </div>
        </div>
    )
}

export default App