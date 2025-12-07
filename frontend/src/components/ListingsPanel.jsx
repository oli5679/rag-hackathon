import { Box, Paper, Typography, Card, CardMedia, CardContent, CircularProgress } from '@mui/material'

function ListingsPanel({ listings, loading }) {
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
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
        <Typography variant="h6" sx={{ color: 'text.primary' }}>
          Top Listings
        </Typography>
        {loading && <CircularProgress size={20} />}
      </Box>

      {listings.length === 0 ? (
        <Typography color="text.secondary" variant="body2">
          {loading ? 'Finding listings...' : 'Send a message to see matching listings'}
        </Typography>
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
          {listings.map((listing) => (
            <Card
              key={listing.id}
              elevation={0}
              sx={{
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 2,
                overflow: 'hidden',
                transition: 'all 0.2s ease',
                '&:hover': {
                  borderColor: 'primary.main',
                  transform: 'translateY(-2px)',
                  boxShadow: '0 4px 12px rgba(99, 102, 241, 0.15)',
                }
              }}
            >
              <CardMedia
                component="img"
                height="140"
                image={listing.imageUrl}
                alt={listing.title}
                sx={{ objectFit: 'cover' }}
              />
              <CardContent sx={{ p: 2.5 }}>
                <Typography variant="subtitle1" fontWeight={600} sx={{ mb: 1 }}>
                  {listing.title}
                </Typography>
                <Typography variant="h6" color="primary" fontWeight={700} sx={{ mb: 0.5 }}>
                  £{listing.price}/month
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                  📍 {listing.location}
                </Typography>
                <Typography variant="body2" color="text.primary" sx={{ lineHeight: 1.6 }}>
                  {listing.summary}
                </Typography>
              </CardContent>
            </Card>
          ))}
        </Box>
      )}
    </Paper>
  )
}

export default ListingsPanel
