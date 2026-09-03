import React, { useState, useRef, useEffect, useCallback } from 'react'

function getFileIcon(filename) {
    if (!filename) return '📄'
    const ext = filename.split('.').pop().toLowerCase()
    if (ext === 'pdf') return '📕'
    if (['doc', 'docx'].includes(ext)) return '📘'
    if (['txt', 'text'].includes(ext)) return '📃'
    return '📄'
}

function stripSourcesFromContent(content) {
    if (!content) return content
    // Remove "Sources:" and everything after it (AI-generated duplicate)
    return content.replace(/\n?\n?Sources:[\s\S]*$/i, '').trim()
}

function ChatInterface({
    messages,
    sessionId,
    onSendMessage,
    onUploadDocument,
    isUploading,
    uploadError,
    documents
}) {
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [dragActive, setDragActive] = useState(false)
    const messagesEndRef = useRef(null)
    const fileInputRef = useRef(null)

    const hasStarted = messages.length > 0

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!input.trim() || loading) return

        const question = input.trim()
        setInput('')
        setLoading(true)

        try {
            await onSendMessage(question)
        } finally {
            setLoading(false)
        }
    }

    const handleDrag = useCallback((e) => {
        e.preventDefault()
        e.stopPropagation()
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true)
        } else if (e.type === 'dragleave') {
            setDragActive(false)
        }
    }, [])

    const handleDrop = useCallback(async (e) => {
        e.preventDefault()
        e.stopPropagation()
        setDragActive(false)

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            const file = e.dataTransfer.files[0]
            const allowed = ['.pdf', '.txt', '.docx', '.doc']
            const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase()
            if (allowed.includes(ext)) {
                try {
                    await onUploadDocument(file)
                } catch (err) {
                    // error handled in parent
                }
            }
        }
    }, [onUploadDocument])

    const handleFileSelect = async (e) => {
        const file = e.target.files[0]
        if (!file) return
        try {
            await onUploadDocument(file)
        } catch (err) {
            // error handled in parent
        }
        e.target.value = ''
    }

    return (
        <div className="chat-interface" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            {!hasStarted && (
                <div
                    className={`upload-dropzone ${dragActive ? 'active' : ''}`}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                    onClick={() => document.getElementById('dropzone-file').click()}
                >
                    <input
                        type="file"
                        id="dropzone-file"
                        style={{ display: 'none' }}
                        accept=".pdf,.txt,.docx,.doc"
                        onChange={handleFileSelect}
                    />
                    <div className="dropzone-content">
                        <div className="dropzone-icon">📄</div>
                        <h3>Drag & drop your file here</h3>
                        <p>or click to browse</p>
                        <p className="dropzone-formats">Supported: PDF, TXT, DOCX</p>
                        {isUploading && <div className="spinner" style={{ marginTop: '1rem' }}></div>}
                        {uploadError && <div className="error" style={{ marginTop: '1rem' }}>{uploadError}</div>}
                        {documents.length > 0 && (
                            <div className="uploaded-docs-preview" style={{ marginTop: '1rem', color: '#667eea' }}>
                                <p>{documents.length} document(s) ready</p>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {hasStarted && (
                <div className="messages" style={{
                    flex: 1,
                    overflowY: 'auto',
                    padding: '1rem',
                    background: 'white',
                    borderRadius: '12px',
                    marginBottom: '1rem',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                }}>
                    {messages.map((msg, idx) => (
                        msg.role === 'document' ? (
                            <div key={idx} style={{
                                marginBottom: '1rem',
                                display: 'flex',
                                justifyContent: 'center'
                            }}>
                                <div style={{
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    gap: '0.5rem',
                                    padding: '0.5rem 1rem',
                                    borderRadius: '20px',
                                    background: '#f0f0f0',
                                    color: '#555',
                                    fontSize: '0.85rem',
                                    border: '1px solid #ddd'
                                }}>
                                    <span>{getFileIcon(msg.content)}</span>
                                    <span>{msg.content}</span>
                                </div>
                            </div>
                        ) : (
                            <div key={idx} style={{
                                marginBottom: '1.5rem',
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start'
                            }}>
                                <div style={{
                                    maxWidth: '80%',
                                    padding: '1rem',
                                    borderRadius: '12px',
                                    background: msg.role === 'user'
                                        ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                                        : '#e9ecef',
                                    color: msg.role === 'user' ? 'white' : '#212529',
                                    border: msg.role === 'user' ? '1px solid rgba(102,126,234,0.4)' : '1px solid #adb5bd',
                                    boxShadow: '0 2px 6px rgba(0,0,0,0.12)'
                                }}>
                                    <div style={{ fontWeight: 600, marginBottom: '0.5rem', fontSize: '0.85rem', opacity: 0.8 }}>
                                        {msg.role === 'user' ? 'You' : 'AI Assistant'}
                                    </div>
                                    <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
                                        {msg.role === 'assistant' ? stripSourcesFromContent(msg.content) : msg.content}
                                    </div>

                                    {msg.citations && msg.citations.length > 0 && (
                                        <div style={{
                                            marginTop: '1rem',
                                            paddingTop: '1rem',
                                            borderTop: msg.role === 'user' ? '1px solid rgba(255,255,255,0.3)' : '1px solid #e0e0e0'
                                        }}>
                                            <div style={{ fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                                                Sources:
                                            </div>
                                            {[...new Map(msg.citations.map(c => [c.document + '|' + (c.page || ''), c])).values()].map((cite, cidx) => (
                                                <div key={cidx} style={{
                                                    fontSize: '0.8rem',
                                                    marginBottom: '0.25rem',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: '0.5rem'
                                                }}>
                                                    <span>{getFileIcon(cite.document)}</span>
                                                    <span>{cite.document}</span>
                                                    {cite.page && <span>— Page {cite.page}</span>}
                                                </div>
                                            ))}
                                        </div>
                                    )}

                                    {msg.retrievalScore !== undefined && (
                                        <div style={{
                                            marginTop: '0.5rem',
                                            fontSize: '0.75rem',
                                            opacity: 0.7
                                        }}>
                                            Score: {msg.retrievalScore} {msg.queryRewritten && '| Query rewritten'} {msg.retryCount > 0 && `| Retries: ${msg.retryCount}`}
                                        </div>
                                    )}
                                </div>
                            </div>
                        )
                    ))}
                    {loading && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '1rem' }}>
                            <div className="spinner"></div>
                            <span style={{ color: '#666' }}> Thinking...</span>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>
            )}

            <form onSubmit={handleSubmit} style={{
                display: 'flex',
                gap: '0.5rem',
                alignItems: 'center',
                background: '#f8f9fa',
                marginBottom: '1rem',
                borderRadius: '12px',
                border: '1px solid #dee2e6',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
            }}>
                <input
                    type="file"
                    ref={fileInputRef}
                    style={{ display: 'none' }}
                    accept=".pdf,.txt,.docx,.doc"
                    onChange={handleFileSelect}
                />
                <button
                    type="button"
                    className="attach-btn"
                    onClick={() => fileInputRef.current?.click()}
                    title="Attach document"
                    disabled={isUploading}
                >
                    +
                </button>

                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder={documents.length > 0
                        ? "Ask a question about your documents..."
                        : "Upload a document first, then ask questions..."}
                    className="input"
                    style={{ flex: 1 }}
                    disabled={loading}
                />
                <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={loading || !input.trim()}
                >
                    {loading ? '...' : 'Send'}
                </button>
            </form>
        </div>
    )
}

export default ChatInterface