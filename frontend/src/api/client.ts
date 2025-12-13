const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8001/api";

export interface ApiResponse<T = any> {
    data: T;
    error?: string;
}

export const apiClient = {
    baseUrl: API_URL,



    async post<T>(endpoint: string, body: any, token?: string): Promise<T> {
        const headers: HeadersInit = {
            "Content-Type": "application/json",
        };
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_URL}${endpoint}`, {
            method: "POST",
            headers,
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `API Error: ${response.statusText}`);
        }
        return response.json();
    },

    async streamPost(endpoint: string, body: any, onMessage: (data: any) => void, token?: string): Promise<void> {
        const headers: HeadersInit = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        };
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_URL}${endpoint}`, {
            method: "POST",
            headers,
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `API Error: ${response.statusText}`);
        }

        if (!response.body) {
            return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');

            // Keep the last incomplete chunk in the buffer
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const jsonStr = line.slice(6).trim();
                    if (!jsonStr || jsonStr === '[DONE]') continue;

                    try {
                        const data = JSON.parse(jsonStr);
                        onMessage(data);
                    } catch (e) {
                        // Silent failure for malformed chunks is safer to avoid log spam
                    }
                }
            }
        }
    }
};
