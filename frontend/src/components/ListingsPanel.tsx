import { useState, useEffect, ChangeEvent } from 'react';
import { Box, Paper, Typography, Card, CardMedia, CardContent, CircularProgress, IconButton, Link, Chip, Button, Pagination, LinearProgress } from '@mui/material';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import DeleteIcon from '@mui/icons-material/Delete';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import UndoIcon from '@mui/icons-material/Undo';
import type { Listing } from '../types';

const ITEMS_PER_PAGE = 5;

const LOADING_MESSAGES = [
  'Searching SpareRoom listings...',
  'Finding rooms that match your criteria...',
  'Analyzing listing photos...',
  'Checking locations and commute times...',
  'Scoring rooms based on your preferences...',
  'Ranking the best matches...',
];

function LoadingIndicator() {
  const [messageIndex, setMessageIndex] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    // Cycle through messages every 3 seconds
    const messageInterval = setInterval(() => {
      setMessageIndex(prev => (prev + 1) % LOADING_MESSAGES.length);
    }, 3000);

    // Update progress bar smoothly
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        // Slow down as we approach 90%
        if (prev >= 90) return prev;
        if (prev >= 70) return prev + 0.5;
        if (prev >= 50) return prev + 1;
        return prev + 2;
      });
    }, 200);

    return () => {
      clearInterval(messageInterval);
      clearInterval(progressInterval);
    };
  }, []);

  return (
    <Box sx={{ textAlign: 'center', py: 4 }}>
      <CircularProgress size={32} sx={{ mb: 2 }} />
      <Typography color="text.primary" variant="body2" sx={{ mb: 1, fontWeight: 500 }}>
        {LOADING_MESSAGES[messageIndex]}
      </Typography>
      <Box sx={{ width: '80%', mx: 'auto', mt: 2 }}>
        <LinearProgress
          variant="determinate"
          value={progress}
          sx={{
            height: 6,
            borderRadius: 3,
            bgcolor: 'grey.200',
            '& .MuiLinearProgress-bar': {
              borderRadius: 3,
            }
          }}
        />
      </Box>
      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
        This may take a moment...
      </Typography>
    </Box>
  );
}

export interface ListingWithScore extends Listing {
  score?: number;
  reasoning?: string;
  priceLabel?: string;
}

interface ListingsPanelProps {
  listings: ListingWithScore[];
  loading: boolean;
  blacklist: string[];
  shortlist: ListingWithScore[];
  onReject: (listingId: string) => void;
  onShortlist: (listing: ListingWithScore) => void;
  onUndo: () => void;
  mode?: 'matches' | 'shortlist';
}

export default function ListingsPanel({
  listings,
  loading,
  blacklist,
  shortlist,
  onReject,
  onShortlist,
  onUndo,
  mode = 'matches'
}: ListingsPanelProps) {
  const [page, setPage] = useState(1);

  const isShortlistMode = mode === 'shortlist';

  // Filter out blacklisted listings (only in matches mode) and sort by score (highest first)
  const filteredListings = isShortlistMode
    ? listings
    : listings.filter(l => !blacklist.includes(l.id)).sort((a, b) => (b.score || 0) - (a.score || 0));

  // Pagination
  const totalPages = Math.ceil(filteredListings.length / ITEMS_PER_PAGE);
  const startIndex = (page - 1) * ITEMS_PER_PAGE;
  const paginatedListings = filteredListings.slice(startIndex, startIndex + ITEMS_PER_PAGE);

  // Reset to page 1 if current page exceeds total pages
  useEffect(() => {
    if (page > totalPages && totalPages > 0) {
      setPage(1);
    }
  }, [page, totalPages]);

  const handlePageChange = (_event: ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };

  return (
    <Paper
      elevation={0}
      sx={{
        p: 3,
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 2,
      }}
    >
      {!isShortlistMode && (
        <>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <Typography variant="h6" sx={{ color: 'text.primary' }}>
                Top Matches
              </Typography>
              {filteredListings.length > 0 && !loading && (
                <Chip
                  label={filteredListings.length}
                  size="small"
                  color="primary"
                  variant="outlined"
                />
              )}
            </Box>
            {blacklist.length > 0 && (
              <IconButton size="small" onClick={onUndo} title="Undo last rejection">
                <UndoIcon fontSize="small" />
              </IconButton>
            )}
          </Box>

          {listings.length > 0 && !loading && (
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
              Based on your preferences
            </Typography>
          )}
        </>
      )}

      {loading ? (
        <LoadingIndicator />
      ) : filteredListings.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography color="text.secondary" variant="body2" sx={{ mb: 1 }}>
            {isShortlistMode
              ? 'No saved listings yet'
              : listings.length > 0
                ? 'No more listings to show'
                : 'Send a message to see matches'}
          </Typography>
          {isShortlistMode ? (
            <Typography color="text.secondary" variant="body2" sx={{ fontStyle: 'italic' }}>
              Click the thumbs up on listings you like to save them here
            </Typography>
          ) : listings.length > 0 && (
            <Typography color="text.secondary" variant="body2" sx={{ fontStyle: 'italic' }}>
              Share more details in the chat to search again
            </Typography>
          )}
        </Box>
      ) : (
        <>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {paginatedListings.map((listing, index) => {
              const globalIndex = startIndex + index;
              return (
                <Card
                  key={listing.id}
                  elevation={0}
                  sx={{
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 2,
                    overflow: 'hidden',
                    position: 'relative',
                  }}
                >
                  {/* Rank badge */}
                  <Box
                    sx={{
                      position: 'absolute',
                      top: 8,
                      left: 8,
                      bgcolor: 'primary.main',
                      color: 'white',
                      borderRadius: '50%',
                      width: 28,
                      height: 28,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 700,
                      fontSize: '0.875rem',
                      zIndex: 2,
                    }}
                  >
                    {globalIndex + 1}
                  </Box>

                  <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' } }}>
                    {/* Image */}
                    <CardMedia
                      component="img"
                      sx={{
                        width: { xs: '100%', sm: 140 },
                        height: { xs: 120, sm: 140 },
                        objectFit: 'cover',
                        flexShrink: 0,
                      }}
                      image={listing.imageUrl}
                      alt={listing.title}
                    />

                    {/* Content */}
                    <CardContent sx={{ p: 2, flex: 1, display: 'flex', flexDirection: 'column' }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 0.5 }}>
                        <Typography variant="subtitle2" fontWeight={600} sx={{ pr: 1 }}>
                          {listing.title}
                        </Typography>
                        {listing.score && (
                          <Chip
                            label={`${listing.score}%`}
                            size="small"
                            color={listing.score >= 70 ? 'success' : listing.score >= 50 ? 'warning' : 'default'}
                            sx={{ fontWeight: 600, fontSize: '0.7rem', height: 22 }}
                          />
                        )}
                      </Box>

                      <Typography variant="body1" color="primary" fontWeight={700} sx={{ mb: 0.5 }}>
                        {listing.priceLabel || `£${listing.price}/month`}
                      </Typography>

                      <Typography variant="caption" color="text.secondary" sx={{ mb: 1 }}>
                        {listing.location}
                      </Typography>

                      <Typography
                        variant="caption"
                        color="text.primary"
                        sx={{
                          lineHeight: 1.5,
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                          flex: 1,
                        }}
                      >
                        {listing.summary}
                      </Typography>

                      {/* Actions */}
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1.5 }}>
                        <Button
                          component={Link}
                          href={listing.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          variant="contained"
                          size="small"
                          startIcon={<OpenInNewIcon sx={{ fontSize: '1rem' }} />}
                          sx={{
                            textTransform: 'none',
                            fontWeight: 600,
                            fontSize: '0.75rem',
                            py: 0.5,
                            px: 1.5,
                          }}
                        >
                          View on SpareRoom
                        </Button>

                        <Box sx={{ display: 'flex', gap: 1 }}>
                          {isShortlistMode ? (
                            <IconButton
                              onClick={() => onReject(listing.id)}
                              size="small"
                              sx={{
                                bgcolor: '#fee2e2',
                                color: '#dc2626',
                                '&:hover': { bgcolor: '#fecaca' },
                              }}
                              title="Remove from shortlist"
                            >
                              <DeleteIcon sx={{ fontSize: '1rem' }} />
                            </IconButton>
                          ) : (
                            <>
                              <IconButton
                                onClick={() => onShortlist(listing)}
                                size="small"
                                disabled={shortlist.some(item => item.id === listing.id)}
                                sx={{
                                  bgcolor: shortlist.some(item => item.id === listing.id) ? '#d1fae5' : '#dcfce7',
                                  color: '#16a34a',
                                  '&:hover': { bgcolor: '#bbf7d0' },
                                  '&.Mui-disabled': { bgcolor: '#d1fae5', color: '#16a34a' },
                                }}
                                title={shortlist.some(item => item.id === listing.id) ? 'Already saved' : 'Save to shortlist'}
                              >
                                <ThumbUpIcon sx={{ fontSize: '1rem' }} />
                              </IconButton>
                              <IconButton
                                onClick={() => onReject(listing.id)}
                                size="small"
                                sx={{
                                  bgcolor: '#fee2e2',
                                  color: '#dc2626',
                                  '&:hover': { bgcolor: '#fecaca' },
                                }}
                                title="Not interested"
                              >
                                <ThumbDownIcon sx={{ fontSize: '1rem' }} />
                              </IconButton>
                            </>
                          )}
                        </Box>
                      </Box>
                    </CardContent>
                  </Box>
                </Card>
              );
            })}
          </Box>

          {/* Pagination */}
          {totalPages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={handlePageChange}
                color="primary"
                size="small"
              />
            </Box>
          )}
        </>
      )}

      {!isShortlistMode && blacklist.length > 0 && (
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2, textAlign: 'center' }}>
          {blacklist.length} listing{blacklist.length !== 1 ? 's' : ''} hidden
        </Typography>
      )}
    </Paper>
  );
}
