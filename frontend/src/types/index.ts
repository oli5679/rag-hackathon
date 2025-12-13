// Re-export Supabase generated types
export type { Database, Tables, TablesInsert, TablesUpdate } from './supabase';

// Convenience type aliases from Supabase schema
import type { Database } from './supabase';

export type Conversation = Database['public']['Tables']['conversations']['Row'];
export type ConversationInsert = Database['public']['Tables']['conversations']['Insert'];

export type Message = Database['public']['Tables']['messages']['Row'];
export type MessageInsert = Database['public']['Tables']['messages']['Insert'];

export type Profile = Database['public']['Tables']['profiles']['Row'];

export type SavedListing = Database['public']['Tables']['saved_listings']['Row'];
export type SavedListingInsert = Database['public']['Tables']['saved_listings']['Insert'];

export type UserRules = Database['public']['Tables']['user_rules']['Row'];
export type UserRulesInsert = Database['public']['Tables']['user_rules']['Insert'];

// Application-specific types

export type MessageRole = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  role: MessageRole;
  content: string;
}

export interface Rule {
  field: string;
  value: string | number;
  unit?: string;
}

export interface Listing {
  id: string;
  title: string;
  price: number;
  priceLabel?: string;
  location: string;
  postcode?: string;
  summary: string;
  url: string;
  imageUrl?: string;
  image_urls?: string[];
  available?: string;
  bills_included?: string;
  couples_ok?: boolean | string;
  pets_ok?: boolean | string;
  parking?: boolean | string;
  property_type?: string;
  room_type?: string;
  furnishings?: string;
  vector_distance?: number;
}

export interface ScoredListing {
  listing: Listing;
  score: number;
  reasoning: ListingScore;
}

export interface ListingScore {
  location_match: number;
  price_match: number;
  amenities_match: number;
  visual_quality: number;
  overall_score: number;
}

export interface IdealListing {
  location?: string;
  target_location?: string;
  max_rent?: number;
  min_rent?: number;
  pets_ok?: string;
  couples_ok?: string;
  bills_included?: string;
  parking?: string;
  property_type?: string;
  furnishings?: string;
  max_commute?: number;
}

// API Request/Response types

export interface ChatRequest {
  message: string;
  conversation_history: ChatMessage[];
}

export interface ChatResponse {
  assistantMessage: string;
  hardRules: Rule[];
}

export interface FindMatchesRequest {
  conversation: ChatMessage[];
}

export interface FindMatchesResponse {
  idealListing: IdealListing;
  summary: string;
  matches: ScoredListing[];
}

// List types for saved listings
export type ListType = 'shortlist' | 'blacklist';
