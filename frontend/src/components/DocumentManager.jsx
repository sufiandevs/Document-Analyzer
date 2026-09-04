import React, { useState, useEffect } from 'react'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function DocumentManager() {
    const [documents, setDocuments] = useState([])
    const [uploading, setUploading] = useState(false)
    const [message, setMessage] = useState(null)
    const [error, setError] = useState(null)

    useEffect(() => {
        fetchDocuments()
    }, [])

    const fetchDocuments = async () => {
        try {
            const response = await axios.get(`${API_URL}/documents`)
            setDocuments(response.data.documents)
        } catch (err) {
            setError('Failed to load documents')
        }
    }

    const handleUpload = async (e) => {
        const file = e.target.files[0]
        if (!file) return

        const allowedTypes = ['.pdf', '.txt', '.docx', '.doc']
        const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase()
        if (!allowedTypes.includes(ext)) {
            setError('Only PDF, TXT, and DOCX files are allowed')
            return
        }

        setUploading(true)
        setError(null)
        setMessage(null)

        const formData = new FormData()
        formData.append('file', file)

        try {
            const response = await axios.post(`${API_URL}/documents/upload`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            })

            setMessage(`Uploaded: ${response.data.filename} (${response.data.chunk_count} chunks indexed)`)
            fetchDocuments()
        } catch (err) {
            setError(err.response?.data?.detail || 'Upload failed')
        } finally {
            setUploading(false)
            e.target.value = ''
        }
    }

    const handleDelete = async (docId) => {
        if (!confirm('Are you sure you want to delete this document?')) return

        try {
            await axios.delete(`${API_URL}/documents/${docId}`)
            setMessage('Document deleted successfully')
            fetchDocuments()
        } catch (err) {
            setError('Delete failed')
        }
    }

    const getStatusClass = (status) => {
        switch (status) {
            case 'completed': return 'status-completed'
            case 'processing': return 'status-processing'
            case 'pending': return 'status-pending'
            case 'failed': return 'status-failed'
            default: return 'status-pending'
        }
    }

    return (
        <div className="document-manager">
            <div className="card">
                <h3>Upload Document</h3>
                <p style={{ color: '#666', marginBottom: '1rem' }}>
                    Supported formats: PDF, TXT, DOCX
                </p>
                <input
                    type="file"
                    accept=".pdf,.txt,.docx,.doc"
                    onChange={handleUpload}
                    disabled={uploading}
                    className="input"
                    style={{ marginBottom: '1rem' }}
                />
                {uploading && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <div className="spinner"></div>
                        <span>Processing document...</span>
                    </div>
                )}
                {message && <div className="success">{message}</div>}
                {error && <div className="error">{error}</div>}
            </div>

            <div className="card">
                <h3>Your Documents ({documents.length})</h3>
                {documents.length === 0 ? (
                    <p style={{ color: '#999', textAlign: 'center', padding: '2rem' }}>
                        No documents uploaded yet. Upload a document to get started!
                    </p>
                ) : (
                    <div className="document-list">
                        {documents.map(doc => (
                            <div key={doc.id} className="document-item" style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                padding: '1rem',
                                borderBottom: '1px solid #eee'
                            }}>
                                <div>
                                    <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>
                                        {doc.filename}
                                    </div>
                                    <div style={{ fontSize: '0.85rem', color: '#666' }}>
                                        <span className={`status-badge ${getStatusClass(doc.status)}`}>
                                            {doc.status}
                                        </span>
                                        {' '}
                                        {doc.chunk_count > 0 && `${doc.chunk_count} chunks`}
                                        {' '}
                                        {doc.file_type && `| ${doc.file_type.toUpperCase()}`}
                                    </div>
                                </div>
                                <button
                                    onClick={() => handleDelete(doc.id)}
                                    className="btn btn-danger"
                                    style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}
                                >
                                    Delete
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}

export default DocumentManager