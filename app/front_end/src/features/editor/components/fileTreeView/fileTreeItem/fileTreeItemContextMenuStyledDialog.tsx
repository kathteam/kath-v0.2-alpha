import { Dialog, styled } from '@mui/material';
import type { DialogProps } from '@mui/material';

export const FileTreeItemContextMenuStyledDialog: React.ComponentType<DialogProps> = styled(Dialog)(({ theme }) => ({
  '& .MuiDialogActions-root': {
    padding: '1.5rem',
  },
  '& .MuiDialog-paper': {
    borderRadius: '1.5rem',
    minWidth: '20%',
    backgroundColor: theme.palette.background.paper,
    backgroundImage: 'none',
  },
}));
