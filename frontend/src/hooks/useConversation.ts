import { useState, useCallback } from 'react';
import { supabase } from '../lib/supabase';
import { useAuth } from '../contexts/AuthContext';
import type { Conversation, Message, MessageInsert, ChatMessage } from '../types';

interface UseConversationReturn {
  conversation: Conversation | null;
  messages: Message[];
  loading: boolean;
  createConversation: (title?: string | null) => Promise<{ data: Conversation | null; error: Error | null }>;
  addMessage: (role: ChatMessage['role'], content: string) => Promise<{ data: Message | null; error: Error | null }>;
  addMessages: (messagePairs: ChatMessage[]) => Promise<{ data: Message[] | null; error: Error | null }>;
  clearConversation: () => void;
}

export function useConversation(): UseConversationReturn {
  const { user } = useAuth();
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  const createConversation = useCallback(async (title: string | null = null) => {
    if (!user) return { data: null, error: new Error('Not authenticated') };

    const { data, error } = await supabase
      .from('conversations')
      .insert({ user_id: user.id, title })
      .select()
      .single();

    if (!error && data) {
      setConversation(data);
      setMessages([]);
    }
    return { data, error };
  }, [user]);

  const addMessage = useCallback(async (role: ChatMessage['role'], content: string) => {
    if (!conversation) return { data: null, error: new Error('No active conversation') };

    const messageInsert: MessageInsert = {
      conversation_id: conversation.id,
      role,
      content
    };

    const { data, error } = await supabase
      .from('messages')
      .insert(messageInsert)
      .select()
      .single();

    if (!error && data) {
      setMessages(prev => [...prev, data]);
    }
    return { data, error };
  }, [conversation]);

  const addMessages = useCallback(async (messagePairs: ChatMessage[]) => {
    if (!conversation) return { data: null, error: new Error('No active conversation') };

    const toInsert: MessageInsert[] = messagePairs.map(({ role, content }) => ({
      conversation_id: conversation.id,
      role,
      content
    }));

    const { data, error } = await supabase
      .from('messages')
      .insert(toInsert)
      .select();

    if (!error && data) {
      setMessages(prev => [...prev, ...data]);
    }
    return { data, error };
  }, [conversation]);

  const clearConversation = useCallback(() => {
    setConversation(null);
    setMessages([]);
  }, []);

  return {
    conversation,
    messages,
    loading,
    createConversation,
    addMessage,
    addMessages,
    clearConversation,
  };
}
