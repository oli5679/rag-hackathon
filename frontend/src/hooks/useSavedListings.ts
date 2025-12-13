import { useState, useEffect, useCallback } from 'react';
import { supabase } from '../lib/supabase';
import { useAuth } from '../auth/AuthContext';
import type { SavedListing, ListType, Listing } from '../types';

interface UseSavedListingsReturn {
  shortlist: SavedListing[];
  blacklist: SavedListing[];
  loading: boolean;
  addToList: (listingId: string, listType: ListType, listingData?: Listing | null) => Promise<{ data: SavedListing | null; error: Error | null }>;
  removeFromList: (listingId: string) => Promise<{ error: Error | null }>;
  isShortlisted: (listingId: string) => boolean;
  isBlacklisted: (listingId: string) => boolean;
  shortlistedIds: () => Set<string>;
  blacklistedIds: () => Set<string>;
  refreshLists: () => Promise<void>;
}

export function useSavedListings(): UseSavedListingsReturn {
  const { user } = useAuth();
  const [shortlist, setShortlist] = useState<SavedListing[]>([]);
  const [blacklist, setBlacklist] = useState<SavedListing[]>([]);
  const [loading, setLoading] = useState(true);

  const loadSavedListings = useCallback(async () => {
    if (!user) return;

    setLoading(true);
    const { data, error } = await supabase
      .from('saved_listings')
      .select('*')
      .eq('user_id', user.id);

    if (!error && data) {
      setShortlist(data.filter(l => l.list_type === 'shortlist'));
      setBlacklist(data.filter(l => l.list_type === 'blacklist'));
    }
    setLoading(false);
  }, [user]);

  // Load saved listings on mount and when user changes
  useEffect(() => {
    if (user) {
      loadSavedListings();
    } else {
      setShortlist([]);
      setBlacklist([]);
      setLoading(false);
    }
  }, [user, loadSavedListings]);

  const addToList = useCallback(async (
    listingId: string,
    listType: ListType,
    listingData: Listing | null = null
  ) => {
    if (!user) return { data: null, error: new Error('Not authenticated') };

    const { data, error } = await supabase
      .from('saved_listings')
      .upsert({
        user_id: user.id,
        listing_id: listingId,
        list_type: listType,
        listing_data: listingData as unknown as Record<string, unknown>
      }, {
        onConflict: 'user_id,listing_id'
      })
      .select()
      .single();

    if (!error) {
      await loadSavedListings();
    }
    return { data, error };
  }, [user, loadSavedListings]);

  const removeFromList = useCallback(async (listingId: string) => {
    if (!user) return { error: new Error('Not authenticated') };

    const { error } = await supabase
      .from('saved_listings')
      .delete()
      .eq('user_id', user.id)
      .eq('listing_id', listingId);

    if (!error) {
      await loadSavedListings();
    }
    return { error };
  }, [user, loadSavedListings]);

  const isShortlisted = useCallback((listingId: string) => {
    return shortlist.some(l => l.listing_id === listingId);
  }, [shortlist]);

  const isBlacklisted = useCallback((listingId: string) => {
    return blacklist.some(l => l.listing_id === listingId);
  }, [blacklist]);

  const shortlistedIds = useCallback(() => {
    return new Set(shortlist.map(l => l.listing_id));
  }, [shortlist]);

  const blacklistedIds = useCallback(() => {
    return new Set(blacklist.map(l => l.listing_id));
  }, [blacklist]);

  return {
    shortlist,
    blacklist,
    loading,
    addToList,
    removeFromList,
    isShortlisted,
    isBlacklisted,
    shortlistedIds,
    blacklistedIds,
    refreshLists: loadSavedListings,
  };
}
