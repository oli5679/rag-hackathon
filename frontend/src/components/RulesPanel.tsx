import { Paper, Typography, Chip, Box, CircularProgress } from '@mui/material';
import type { Rule } from '../types';

interface RulesPanelProps {
  rules: Rule[];
  onDelete: (field: string) => void;
  loading: boolean;
}

function formatRule(rule: Rule): string {
  const { field, value, unit } = rule;
  switch (field) {
    case 'max_budget': return `Max ${unit === 'GBP' ? '£' : ''}${value}`;
    case 'min_budget': return `Min ${unit === 'GBP' ? '£' : ''}${value}`;
    case 'location': return `Location: ${value}`;
    case 'pets_allowed': return 'Pets allowed';
    case 'bills_included': return 'Bills included';
    default: return `${field}: ${value}`;
  }
}

export default function RulesPanel({ rules, onDelete, loading }: RulesPanelProps) {
  return (
    <Paper
      elevation={0}
      sx={{
        p: 3,
        mb: 3,
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 2,
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
        <Typography variant="h6" sx={{ color: 'text.primary' }}>
          Filters
        </Typography>
        {loading && <CircularProgress size={16} />}
      </Box>

      {rules.length === 0 ? (
        <Typography color="text.secondary" variant="body2">
          {loading ? 'Extracting filters...' : 'No filters applied yet'}
        </Typography>
      ) : (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {rules.map((rule) => (
            <Chip
              key={rule.field}
              label={formatRule(rule)}
              onDelete={() => onDelete(rule.field)}
              color="primary"
              variant="filled"
              disabled={loading}
              sx={{
                fontWeight: 500,
                '& .MuiChip-deleteIcon': {
                  color: 'rgba(255, 255, 255, 0.7)',
                  '&:hover': {
                    color: 'white',
                  }
                }
              }}
            />
          ))}
        </Box>
      )}
    </Paper>
  );
}
