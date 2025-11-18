import { InputLabel, ListSubheader, MenuItem, Select, Typography, styled } from '@mui/material';
import type { InputLabelProps, ListSubheaderProps, MenuItemProps, SelectProps, TypographyProps } from '@mui/material';

export const StyledGroupParamsTypography: React.ComponentType<TypographyProps> = styled(Typography)({
  fontSize: '0.875rem',
  transition: 'color 0.3s ease',
});

export const StyledGroupParamsInputLabel: React.ComponentType<InputLabelProps> = styled(InputLabel)({
  transition: 'color 0.3s ease',
});

export const StyledGroupParamsSelect: React.ComponentType<SelectProps> = styled(Select)({
  height: '80%',
  transition: 'color 0.3s ease, border-color 0.3s ease',
});

export const StyledGroupParamsMenuItem: React.ComponentType<MenuItemProps> = styled(MenuItem)({
  whiteSpace: 'normal',
});

export const StyledGroupParamsListSubheader: React.ComponentType<ListSubheaderProps> = styled(ListSubheader)(
  ({ theme }) => ({
    backgroundColor: theme.palette.background.default,
    whiteSpace: 'normal',
  })
);

export const StyledGroupParamsMenuItemTypography: React.ComponentType<TypographyProps> = styled(Typography)({
  fontSize: '1rem',
  overflowWrap: 'break-word',
});

export const StyledGroupParamsMenuItemTypographyBold: React.ComponentType<TypographyProps> = styled(Typography)({
  fontSize: '0.875rem',
  fontWeight: 'bold',
  overflowWrap: 'break-word',
});
