import { useState } from 'react'
import { Box, Paper, Typography, Card, CardMedia, CardContent, CircularProgress, IconButton, Link, Chip, Button, Pagination } from '@mui/material'
import ThumbDownIcon from '@mui/icons-material/ThumbDown'
import OpenInNewIcon from '@mui/icons-material/OpenInNew'
import UndoIcon from '@mui/icons-material/Undo'

const ITEMS_PER_PAGE = 5

function ListingsPanel({ listings, loading, onReject, blacklist, onUndo }) {
  const [page, setPage] = useState(1)

  // Filter out blacklisted listings and sort by score (highest first)
  const filteredListings = listings
    .filter(l => !blacklist.includes(l.id))
    .sort((a, b) => (b.score || 0) - (a.score || 0))

  // Pagination
  const totalPages = Math.ceil(filteredListings.length / ITEMS_PER_PAGE)
  const startIndex = (page - 1) * ITEMS_PER_PAGE
  const paginatedListings = filteredListings.slice(startIndex, startIndex + ITEMS_PER_PAGE)

  // Reset to page 1 if current page exceeds total pages
  if (page > totalPages && totalPages > 0) {
    setPage(1)
  }

  const handlePageChange = (event, value) => {
    setPage(value)
  }

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
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Typography variant="h6" sx={{ color: 'text.primary' }}>
            Top Matches
          </Typography>
          {filteredListings.length > 0 && (
            <Chip
              label={filteredListings.length}
              size="small"
              color="primary"
              variant="outlined"
            />
          )}
          {loading && <CircularProgress size={20} />}
        </Box>
        {blacklist.length > 0 && (
          <IconButton size="small" onClick={onUndo} title="Undo last rejection">
            <UndoIcon fontSize="small" />
          </IconButton>
        )}
      </Box>

      {listings.length > 0 && (
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
          Based on your preferences
        </Typography>
      )}

      {filteredListings.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography color="text.secondary" variant="body2" sx={{ mb: 1 }}>
            {loading ? 'Finding matches...' : listings.length > 0
              ? 'No more listings to show'
              : 'Send a message to see matches'}
          </Typography>
          {!loading && listings.length > 0 && (
            <Typography color="text.secondary" variant="body2" sx={{ fontStyle: 'italic' }}>
              Share more details in the chat to search again
            </Typography>
          )}
        </Box>
      ) : (
        <>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {paginatedListings.map((listing, index) => {
              const globalIndex = startIndex + index
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
                      </Box>
                    </CardContent>
                  </Box>
                </Card>
              )
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

      {blacklist.length > 0 && (
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2, textAlign: 'center' }}>
          {blacklist.length} listing{blacklist.length !== 1 ? 's' : ''} hidden
        </Typography>
      )}
    </Paper>
  )
}

export default ListingsPanel
