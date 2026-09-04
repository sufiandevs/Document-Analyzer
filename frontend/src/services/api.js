import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json'
    }
})

export const uploadDocument = (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    })
}

export const getDocuments = () => api.get('/documents')
export const deleteDocument = (id) => api.delete(`/documents/${id}`)
export const sendMessage = (question, sessionId, documentIds = []) => api.post('/chat', { question, session_id: sessionId, document_ids: documentIds })
export const getChatHistory = (sessionId) => api.get(`/chat/history/${sessionId}`)
export const healthCheck = () => api.get('/health')
export const getChatSessions = () => api.get('/chat/sessions')

export default api