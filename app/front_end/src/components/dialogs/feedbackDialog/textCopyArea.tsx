import { Check as CheckIcon, ContentCopy as ContentCopyIcon } from '@mui/icons-material';
import { Box, IconButton, Typography, useTheme } from '@mui/material';
import { useState } from 'react';

interface TextCopyAreaProps {
  value: string;
}

export const TextCopyArea = ({ value }: TextCopyAreaProps) => {
  const Theme = useTheme();

  const [isCopied, setIsCopied] = useState(false);

  const onValueCopy = () => {
    navigator.clipboard.writeText(value);
    if (!isCopied) {
      setIsCopied(true);
      setTimeout(() => {
        setIsCopied(false);
      }, 1500);
    }
  };

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        border: '1px solid',
        borderRadius: '1rem',
        pl: '0.75rem',
        pr: '0.5rem',
        py: '0.25rem',
        borderColor: Theme.palette.primary.main,
      }}
    >
      <Typography sx={{ fontWeight: '700', fontSize: '1rem', pr: '0.25rem' }}>{value}</Typography>
      <IconButton
        aria-label='copy'
        onClick={onValueCopy}
        sx={{
          color: Theme.palette.primary.main,
        }}
      >
        {isCopied ? <CheckIcon sx={{ fontSize: '1rem' }} /> : <ContentCopyIcon sx={{ fontSize: '1rem' }} />}
      </IconButton>
    </Box>
  );
};
