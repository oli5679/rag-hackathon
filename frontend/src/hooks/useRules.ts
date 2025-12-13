import { useState, useEffect, useCallback } from 'react';
import { supabase } from '../lib/supabase';
import { useAuth } from '../auth/AuthContext';
import type { Rule } from '../types';

interface UseRulesReturn {
  rules: Rule[];
  loading: boolean;
  saveRules: (newRules: Rule[]) => Promise<{ data: unknown; error: Error | null }>;
  addRule: (rule: Rule) => Promise<{ data: unknown; error: Error | null }>;
  removeRule: (index: number) => Promise<{ data: unknown; error: Error | null }>;
  updateRule: (index: number, updatedRule: Rule) => Promise<{ data: unknown; error: Error | null }>;
  clearRules: () => Promise<{ data: unknown; error: Error | null }>;
  refreshRules: () => Promise<void>;
}

export function useRules(conversationId: string | null | undefined): UseRulesReturn {
  const { user } = useAuth();
  const [rules, setRules] = useState<Rule[]>([]);
  const [loading, setLoading] = useState(false);

  const loadRules = useCallback(async () => {
    if (!user || !conversationId) return;

    setLoading(true);
    console.log('[useRules] Loading rules for user:', user.id, 'conversation:', conversationId);

    const { data, error } = await supabase
      .from('user_rules')
      .select('*')
      .eq('user_id', user.id)
      .eq('conversation_id', conversationId)
      .single();

    if (error) {
      console.log('[useRules] Error:', error.code, error.message, error);
    }

    if (!error && data) {
      setRules((data.rules as Rule[]) || []);
    } else if (error?.code === 'PGRST116') {
      // No rules found - that's okay
      console.log('[useRules] No rules found (PGRST116), setting empty array');
      setRules([]);
    } else if (error) {
      console.error('[useRules] Unexpected error loading rules:', error);
      setRules([]);
    }
    setLoading(false);
  }, [user, conversationId]);

  // Load rules when conversation changes
  useEffect(() => {
    if (user && conversationId) {
      loadRules();
    } else {
      setRules([]);
    }
  }, [user, conversationId, loadRules]);

  const saveRules = useCallback(async (newRules: Rule[]) => {
    if (!user || !conversationId) {
      return { data: null, error: new Error('Not authenticated or no conversation') };
    }

    const { data, error } = await supabase
      .from('user_rules')
      .upsert({
        user_id: user.id,
        conversation_id: conversationId,
        rules: newRules as unknown as Record<string, unknown>[],
        updated_at: new Date().toISOString()
      }, {
        onConflict: 'user_id,conversation_id'
      })
      .select()
      .single();

    if (!error) {
      setRules(newRules);
    }
    return { data, error };
  }, [user, conversationId]);

  const addRule = useCallback(async (rule: Rule) => {
    const newRules = [...rules, rule];
    return saveRules(newRules);
  }, [rules, saveRules]);

  const removeRule = useCallback(async (index: number) => {
    const newRules = rules.filter((_, i) => i !== index);
    return saveRules(newRules);
  }, [rules, saveRules]);

  const updateRule = useCallback(async (index: number, updatedRule: Rule) => {
    const newRules = rules.map((rule, i) => i === index ? updatedRule : rule);
    return saveRules(newRules);
  }, [rules, saveRules]);

  const clearRules = useCallback(async () => {
    return saveRules([]);
  }, [saveRules]);

  return {
    rules,
    loading,
    saveRules,
    addRule,
    removeRule,
    updateRule,
    clearRules,
    refreshRules: loadRules,
  };
}
