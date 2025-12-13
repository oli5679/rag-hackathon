import { useState, useCallback } from 'react';
import { supabase } from '../lib/supabase';
import { useAuth } from '../auth/AuthContext';
import type { Conversation, Message, MessageInsert, ChatMessage } from '../types';

interface UseConversationReturn {
  conversation: Conversation | null;
  messages: Message[];
  loading: boolean;
  createConversation: (title?: string | null) => Promise<{ data: Conversation | null; error: Error | null }>;
  loadConversation: (conversationId: string) => Promise<{ conversation: Conversation | null; messages: Message[]; error: Error | null }>;
  addMessage: (role: ChatMessage['role'], content: string) => Promise<{ data: Message | null; error: Error | null }>;
  addMessages: (messagePairs: ChatMessage[]) => Promise<{ data: Message[] | null; error: Error | null }>;
  listConversations: () => Promise<{ data: Conversation[] | null; error: Error | null }>;
  updateTitle: (title: string) => Promise<{ data: Conversation | null; error: Error | null }>;
  deleteConversation: (conversationId: string) => Promise<{ error: Error | null }>;
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

  const loadConversation = useCallback(async (conversationId: string) => {
    if (!user) return { conversation: null, messages: [], error: new Error('Not authenticated') };

    setLoading(true);

    const [convResult, msgsResult] = await Promise.all([
      supabase
        .from('conversations')
        .select('*')
        .eq('id', conversationId)
        .single(),
      supabase
        .from('messages')
        .select('*')
        .eq('conversation_id', conversationId)
        .order('created_at', { ascending: true })
    ]);

    if (!convResult.error && convResult.data) {
      setConversation(convResult.data);
    }
    if (!msgsResult.error && msgsResult.data) {
      setMessages(msgsResult.data);
    }

    setLoading(false);
    return {
      conversation: convResult.data,
      messages: msgsResult.data || [],
      error: convResult.error || msgsResult.error
    };
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

  const listConversations = useCallback(async () => {
    if (!user) return { data: null, error: new Error('Not authenticated') };

    const { data, error } = await supabase
      .from('conversations')
      .select('*')
      .eq('user_id', user.id)
      .order('updated_at', { ascending: false });

    return { data, error };
  }, [user]);

  const updateTitle = useCallback(async (title: string) => {
    if (!conversation) return { data: null, error: new Error('No active conversation') };

    const { data, error } = await supabase
      .from('conversations')
      .update({ title })
      .eq('id', conversation.id)
      .select()
      .single();

    if (!error && data) {
      setConversation(data);
    }
    return { data, error };
  }, [conversation]);

  const deleteConversation = useCallback(async (conversationId: string) => {
    const { error } = await supabase
      .from('conversations')
      .delete()
      .eq('id', conversationId);

    if (!error && conversation?.id === conversationId) {
      setConversation(null);
      setMessages([]);
    }
    return { error };
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
    loadConversation,
    addMessage,
    addMessages,
    listConversations,
    updateTitle,
    deleteConversation,
    clearConversation,
  };
}
