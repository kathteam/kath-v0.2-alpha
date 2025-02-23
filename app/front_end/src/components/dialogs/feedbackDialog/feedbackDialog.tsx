import { TextCopyArea } from '@/components/dialogs/feedbackDialog/textCopyArea';
import { Close as CloseIcon } from '@mui/icons-material';
import {
  alpha,
  Box,
  Dialog,
  DialogContent,
  DialogTitle,
  Grid,
  IconButton,
  styled,
  Typography,
  useTheme,
} from '@mui/material';

const BootstrapDialog = styled(Dialog)(({ theme }) => ({
  backdropFilter: 'blur(5px)',
  '& .MuiDialogContent-root': {
    padding: '1.5rem',
  },
  '& .MuiDialogActions-root': {
    padding: '1.5rem',
  },
  '& .MuiDialog-paper': {
    borderRadius: '1.5rem',
    minWidth: '25%',
    backgroundColor: theme.palette.background.paper,
    backgroundImage: 'none',
  },
}));

interface FeedbackDialogProps {
  open: boolean;
  onClose: () => void;
}

export const FeedbackDialog = ({ open, onClose }: FeedbackDialogProps) => {
  const Theme = useTheme();

  const email = 'kathteam@outlook.com';

  return (
    <BootstrapDialog onClose={onClose} open={open}>
      <Grid container spacing={2} justifyContent='center' alignItems='center'>
        <Grid item xs={8}>
          <DialogTitle
            sx={{
              color: Theme.palette.primary.main,
              pl: '1.5rem',
              pt: '1.5rem',
              fontWeight: '700',
              fontSize: '1.2rem',
            }}
          >
            Feedback
          </DialogTitle>
        </Grid>
        <Grid item xs={4}>
          <Box display='flex' justifyContent='flex-end'>
            <IconButton
              aria-label='close'
              onClick={onClose}
              sx={{
                color: Theme.palette.primary.main,
                mt: '0.5rem',
                mr: '1.5rem',
              }}
            >
              <CloseIcon />
            </IconButton>
          </Box>
        </Grid>
      </Grid>
      <DialogContent sx={{ borderTop: `1px solid ${alpha(Theme.palette.text.secondary, 0.3)}` }}>
        <Grid container display='flex' alignItems='center' pb='1rem' mt='-0.5rem' rowGap={2.5}>
          <Grid item xs={12}>
            <Typography sx={{ fontWeight: '500', fontSize: '1rem', width: '100%' }}>
              Have any feedback, suggestions, or feature requests? We would love to hear from you! Email us at:
            </Typography>
          </Grid>
          <Grid item xs={12} sx={{ display: 'flex', justifyContent: 'center' }}>
            <TextCopyArea value={email} />
          </Grid>
        </Grid>
      </DialogContent>
    </BootstrapDialog>
  );
};
