import { apiClient } from "./client";

export interface Message {
    role: "user" | "assistant" | "system";
    content: string;
}

export interface ChatResponse {
    assistantMessage: string;
    hardRules: any[];
    searchSuggested?: boolean;
}

export interface MatchResponse {
    idealListing: any;
    summary: string;
    matches: any[];
}

export const chatApi = {
    sendMessage: async (message: string, history: Message[], token: string): Promise<ChatResponse> => {
        return apiClient.post<ChatResponse>("/chat", {
            message,
            conversation_history: history,
        }, token);
    },



    findMatchesStream: async (
        conversation: Message[],
        onMessage: (data: any) => void,
        token: string
    ): Promise<void> => {
        return apiClient.streamPost("/find-matches-stream", { conversation }, onMessage, token);
    }
};
