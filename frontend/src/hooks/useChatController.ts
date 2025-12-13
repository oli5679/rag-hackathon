import { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useConversation } from './useConversation';
import { useSavedListings } from './useSavedListings';
import { useRules } from './useRules';
import { chatApi, ChatResponse, MatchResponse } from '../api/chat';
import { normalizeRent } from '../utils/rent';
import type { ChatMessage } from '../types';
import { ListingWithScore } from '../components/ListingsPanel';

export function useChatController() {
    const { user, session, loading: authLoading, signOut } = useAuth();
    const {
        conversation,
        messages,
        createConversation,
        addMessages,
        clearConversation
    } = useConversation();
    const {
        shortlist,
        addToList,
        removeFromList,
        isShortlisted,
        blacklistedIds
    } = useSavedListings();
    const { rules, saveRules } = useRules(conversation?.id);

    const [listings, setListings] = useState<ListingWithScore[]>([]);
    const [chatLoading, setChatLoading] = useState(false);
    const [listingsLoading, setListingsLoading] = useState(false);
    const [activeTab, setActiveTab] = useState(0);
    const [scoringProgress, setScoringProgress] = useState<{ scored: number; total: number }>({ scored: 0, total: 0 });
    const [searchSuggested, setSearchSuggested] = useState(false);

    // AbortController refs to cancel in-flight requests
    const chatAbortRef = useRef<AbortController | null>(null);
    const matchAbortRef = useRef<AbortController | null>(null);

    // Create conversation on mount if needed
    useEffect(() => {
        if (user && !conversation) {
            createConversation();
        }
    }, [user, conversation, createConversation]);

    // Helper to get history for API calls
    const getConversationHistory = () => {
        return messages.map(m => ({ role: m.role, content: m.content }) as ChatMessage);
    };

    const handleStreamUpdate = (data: any) => {
        if (data.type === 'init') {
            setScoringProgress({ scored: 0, total: data.total });
            setListings([]); // Clear old listings
        } else if (data.type === 'score') {
            const match = data.match;
            const newListing: ListingWithScore = {
                ...normalizeRent(match.listing),
                score: match.score,
                reasoning: match.reasoning?.overall_reasoning
            };

            setListings(prev => {
                const updated = [...prev, newListing];
                // Sort by score descending
                return updated.sort((a, b) => (b.score || 0) - (a.score || 0));
            });

            setScoringProgress(prev => ({ ...prev, scored: prev.scored + 1 }));
        } else if (data.type === 'done') {
            setListingsLoading(false);
        }
    };

    const searchListings = async () => {
        if (!conversation || !session?.access_token) return;

        setListingsLoading(true);
        setScoringProgress({ scored: 0, total: 0 });

        try {
            await chatApi.findMatchesStream(
                getConversationHistory(),
                handleStreamUpdate,
                session.access_token
            );

            // Post-search feedback from assistant
            await addMessages([{
                role: 'assistant',
                content: "I've found some matches! 🏠 What do you think of them? Let me know if you'd like to refine your criteria."
            }]);

        } catch (err) {
            console.error('Search failed:', err);
            // Optionally notify user via a toast or message
        } finally {
            // Note: handleStreamUpdate handles loading=false on 'done' event, 
            // but we ensure it's reset on error too.
            // However, we don't want to conflict if the stream is still closing?
            // With await, the stream is done or errored.
            setListingsLoading(false);
            setSearchSuggested(false);
        }
    };

    const sendMessage = async (text: string) => {
        if (!conversation || !session?.access_token) {
            console.error('No conversation or session available');
            return;
        }

        // 1. Optimistic Update: Add user message immediately
        const userMsg: ChatMessage = { role: 'user', content: text };
        await addMessages([userMsg]); // This updates DB and local 'messages' state

        // 2. Prepare history for API (excluding the message we just added, 
        //    but wait - the backend expects history + current message separate)
        //    Actually `useConversation` updates state async. 
        //    The `messages` variable in this closure is the OLD one.
        //    So `conversationHistory` below is correct (it's the history *before* this new message).
        const conversationHistory = getConversationHistory();

        setChatLoading(true);

        try {
            // 3. Call API
            const chatData: ChatResponse = await chatApi.sendMessage(
                text,
                conversationHistory,
                session.access_token
            );

            // 4. Add assistant response
            await addMessages([
                { role: 'assistant', content: chatData.assistantMessage }
            ]);

            if (chatData.hardRules) {
                await saveRules(chatData.hardRules);
            }

            if (chatData.searchSuggested) {
                setSearchSuggested(true);
            }

            // AUTO-SEARCH REMOVED: Search is now manually triggered via searchListings
            // or we could prompt the user via UI state.

        } catch (err) {
            console.error('Error:', err);
            await addMessages([
                { role: 'assistant', content: 'Sorry, something went wrong.' }
            ]);
        } finally {
            setChatLoading(false);
        }
    };

    const deleteRule = async (field: string) => {
        if (!session?.access_token) return;

        const newRules = rules.filter(r => r.field !== field);

        try {
            await saveRules(newRules);

            if (messages.length > 0) {
                setListingsLoading(true);
                setScoringProgress({ scored: 0, total: 0 });

                await chatApi.findMatchesStream(
                    getConversationHistory(),
                    handleStreamUpdate,
                    session.access_token
                );
            }
        } catch (err) {
            console.error('Failed to update rules:', err);
            setListingsLoading(false);
        }
    };

    const handleReject = async (listingId: string) => {
        await addToList(listingId, 'blacklist');
        if (isShortlisted(listingId)) {
            await removeFromList(listingId);
            await addToList(listingId, 'blacklist');
        }
    };

    const handleShortlist = async (listing: ListingWithScore) => {
        if (!isShortlisted(listing.id)) {
            // We cast to Listing because ListingWithScore extends it and Supabase expects Listing-like structure
            await addToList(listing.id, 'shortlist', listing);
        }
    };

    const handleReset = async () => {
        clearConversation();
        setListings([]);
        await createConversation();
    };

    const handleSignOut = async () => {
        await signOut();
        clearConversation();
        setListings([]);
    };

    return {
        // State
        user,
        authLoading,
        messages,
        rules,
        listings,
        shortlist,
        activeTab,
        chatLoading,
        listingsLoading,
        scoringProgress,
        searchSuggested,
        blacklistedIds: blacklistedIds(),

        // Actions
        setActiveTab,
        sendMessage,
        searchListings,
        deleteRule,
        handleReject,
        handleShortlist,
        handleRemoveFromShortlist: removeFromList,
        handleNewConversation: handleReset,
        handleSignOut
    };
}
