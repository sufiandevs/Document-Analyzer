import React from 'react'

function Sidebar({
    isOpen,
    onToggle,
    conversations,
    activeConversationId,
    onSelectConversation,
    onNewChat,
    onDeleteConversation,
    documents,
    onDeleteDocument
}) {
    return (
        <div className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
            <div className="sidebar-header">
                <button className="sidebar-toggle" onClick={onToggle}>
                    {isOpen ? '◀' : '▶'}
                </button>
                {isOpen && <h2>AI Assistant</h2>}
            </div>

            {isOpen && (
                <>
                    <button className="new-chat-btn" onClick={onNewChat}>
                        + New Chat
                    </button>

                    <div className="sidebar-section">
                        <h3>Conversations</h3>
                        <div className="conversation-list">
                            {conversations.map(conv => (
                                <div
                                    key={conv.id}
                                    className={`conversation-item ${conv.id === activeConversationId ? 'active' : ''}`}
                                    onClick={() => onSelectConversation(conv.id)}
                                >
                                    <span className="conversation-title">{conv.title}</span>
                                    <button
                                        className="delete-conv-btn"
                                        onClick={(e) => { e.stopPropagation(); onDeleteConversation(conv.id); }}
                                    >
                                        🗑
                                    </button>
                                </div>
                            ))}
                            {conversations.length === 0 && (
                                <p style={{ opacity: 0.5, fontSize: '0.85rem', padding: '0.5rem' }}>No chats yet</p>
                            )}
                        </div>
                    </div>

                    <div className="sidebar-section">
                        <h3>Your Documents</h3>
                        <div className="document-list-sidebar">
                            {documents.length === 0 && (
                                <p style={{ opacity: 0.5, fontSize: '0.85rem' }}>No documents uploaded</p>
                            )}
                            {documents.map(doc => (
                                <div key={doc.id} className="sidebar-doc-item">
                                    <span className="doc-name" title={doc.filename}>{doc.filename}</span>
                                    <button
                                        className="delete-doc-btn"
                                        onClick={() => onDeleteDocument(doc.id)}
                                    >
                                        ✕
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}

export default Sidebar