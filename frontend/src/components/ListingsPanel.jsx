import { useState } from 'react'
import { Box, Paper, Typography, Card, CardMedia, CardContent, CircularProgress, IconButton, Link, Chip } from '@mui/material'
import ThumbUpIcon from '@mui/icons-material/ThumbUp'
import ThumbDownIcon from '@mui/icons-material/ThumbDown'
import OpenInNewIcon from '@mui/icons-material/OpenInNew'
import UndoIcon from '@mui/icons-material/Undo'

function ListingsPanel({ listings, loading, onReject, onAccept, blacklist, onUndo }) {
  const [currentIndex, setCurrentIndex] = useState(0)

  // Filter out blacklisted listings
  const filteredListings = listings.filter(l => !blacklist.includes(l.id))

  const currentListing = filteredListings[currentIndex]
  const hasMore = currentIndex < filteredListings.length - 1

  const handleReject = () => {
    if (currentListing) {
      onReject(currentListing.id)
      if (!hasMore) setCurrentIndex(Math.max(0, currentIndex - 1))
    }
  }

  const handleAccept = () => {
    if (currentListing) {
      onAccept(currentListing.id)
      if (hasMore) setCurrentIndex(currentIndex + 1)
    }
  }

  const handleUndo = () => {
    onUndo()
  }

  // Reset index when listings change
  if (currentIndex >= filteredListings.length && filteredListings.length > 0) {
    setCurrentIndex(0)
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
            Top Listings
          </Typography>
          {filteredListings.length > 0 && (
            <Chip
              label={`${currentIndex + 1} / ${filteredListings.length}`}
              size="small"
              color="primary"
              variant="outlined"
            />
          )}
          {loading && <CircularProgress size={20} />}
        </Box>
        {blacklist.length > 0 && (
          <IconButton size="small" onClick={handleUndo} title="Undo last rejection">
            <UndoIcon fontSize="small" />
          </IconButton>
        )}
      </Box>

      {filteredListings.length === 0 ? (
        <Typography color="text.secondary" variant="body2">
          {loading ? 'Finding listings...' : listings.length > 0 ? 'All listings reviewed!' : 'Send a message to see matching listings'}
        </Typography>
      ) : currentListing && (
        <Card
          elevation={0}
          sx={{
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 2,
            overflow: 'hidden',
          }}
        >
          <Box sx={{ position: 'relative' }}>
            <CardMedia
              component="img"
              height="200"
              image={currentListing.imageUrl}
              alt={currentListing.title}
              sx={{ objectFit: 'cover' }}
            />
            <Link
              href={currentListing.url}
              target="_blank"
              rel="noopener noreferrer"
              sx={{
                position: 'absolute',
                top: 8,
                right: 8,
                bgcolor: 'rgba(255,255,255,0.9)',
                borderRadius: 1,
                p: 0.5,
                display: 'flex',
                '&:hover': { bgcolor: 'white' }
              }}
            >
              <OpenInNewIcon fontSize="small" color="primary" />
            </Link>
          </Box>
          <CardContent sx={{ p: 2.5 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
              <Link
                href={currentListing.url}
                target="_blank"
                rel="noopener noreferrer"
                underline="hover"
                color="inherit"
              >
                <Typography variant="subtitle1" fontWeight={600}>
                  {currentListing.title}
                </Typography>
              </Link>
              {currentListing.score && (
                <Chip
                  label={`${currentListing.score}%`}
                  size="small"
                  color={currentListing.score >= 70 ? 'success' : currentListing.score >= 50 ? 'warning' : 'default'}
                  sx={{ fontWeight: 600 }}
                />
              )}
            </Box>
            <Typography variant="h6" color="primary" fontWeight={700} sx={{ mb: 0.5 }}>
              {currentListing.priceLabel || `£${currentListing.price}/month`}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
              {currentListing.location}
            </Typography>
            <Typography
              variant="body2"
              color="text.primary"
              sx={{
                lineHeight: 1.6,
                display: '-webkit-box',
                WebkitLineClamp: 4,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden'
              }}
            >
              {currentListing.summary}
            </Typography>

            {/* Accept/Reject buttons */}
            <Box sx={{ display: 'flex', justifyContent: 'center', gap: 4, mt: 3 }}>
              <IconButton
                onClick={handleReject}
                sx={{
                  bgcolor: '#fee2e2',
                  color: '#dc2626',
                  width: 56,
                  height: 56,
                  '&:hover': { bgcolor: '#fecaca', transform: 'scale(1.1)' },
                  transition: 'all 0.2s ease'
                }}
              >
                <ThumbDownIcon />
              </IconButton>
              <IconButton
                onClick={handleAccept}
                sx={{
                  bgcolor: '#dcfce7',
                  color: '#16a34a',
                  width: 56,
                  height: 56,
                  '&:hover': { bgcolor: '#bbf7d0', transform: 'scale(1.1)' },
                  transition: 'all 0.2s ease'
                }}
              >
                <ThumbUpIcon />
              </IconButton>
            </Box>
          </CardContent>
        </Card>
      )}

      {blacklist.length > 0 && (
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2, textAlign: 'center' }}>
          {blacklist.length} listing{blacklist.length !== 1 ? 's' : ''} rejected
        </Typography>
      )}
    </Paper>
  )
}

export default ListingsPanel
