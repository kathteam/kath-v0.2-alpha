import { FilterAlt as FilterAltIcon, FilterAltOff as FilterAltOffIcon } from '@mui/icons-material';
import { Box, Button, FormControl, InputLabel, MenuItem, OutlinedInput, Select, SelectChangeEvent, Typography, useTheme } from '@mui/material';
import { FilterEnum } from '@/features/editor/types';
import { useState, MouseEvent as MouseEventReact } from 'react';

export interface EditorColumnMenuFilterItemProps {
    initialOperator: FilterEnum;
    initialValue: string;
    onClick: (event: MouseEventReact<HTMLButtonElement, MouseEvent>) => void;
    onFilter: (operator: FilterEnum, value: string) => void;
    onFilterClear: () => void;
}

export const EditorColumnMenuFilterItem: React.FC<EditorColumnMenuFilterItemProps> = ({ initialOperator, initialValue, onClick, onFilter, onFilterClear}) => {
  const Theme = useTheme();

  const [operator, setOperator] = useState<FilterEnum>(initialOperator);
  const [value, setValue] = useState<string>(initialValue);

  const handleOperatorChange = (event: SelectChangeEvent) => {
    const operator = event.target.value as FilterEnum;
    setOperator(operator);
  };

  const handleValueChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setValue(event.target.value);
  };

  const handleClick = (event: MouseEventReact<HTMLButtonElement, MouseEvent>) => {
    onClick(event);
    onFilter(operator, value);
  }

  const handleClearClick = (event: MouseEventReact<HTMLButtonElement, MouseEvent>) => {
    onClick(event);
    onFilterClear();
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
          alignItems: 'center',
          px: '0.85rem',
          py: '1rem',
          bgcolor: Theme.palette.background.default,
        }}
      >
        <FormControl fullWidth size='small'>
          <InputLabel>
            <Box 
              sx={{
                bgcolor: Theme.palette.background.default,
                pr: '0.5rem',
              }}
            >
              <Typography>Filter Operator</Typography>
            </Box>
          </InputLabel>
          <Select
            id='filter-operator'
            label='Operator'
            value={operator}
            onChange={handleOperatorChange}
            size='small'
            sx={{
              fontSize: '0.8rem',
            }}
          >
            <MenuItem value={FilterEnum.CONTAINS}>
              contains
            </MenuItem>
            <MenuItem value={FilterEnum.NOT_CONTAINS}>
              does not contain
            </MenuItem>
            <MenuItem value={FilterEnum.EQUALS}>
              equals
            </MenuItem>
            <MenuItem value={FilterEnum.NOT_EQUALS}>
              does not equal
            </MenuItem>
            <MenuItem value={FilterEnum.STARTS}>
              starts with
            </MenuItem>
            <MenuItem value={FilterEnum.ENDS}>
              ends with
            </MenuItem>
            <MenuItem value={FilterEnum.EMPTY}>
              is empty
            </MenuItem>
            <MenuItem value={FilterEnum.NOT_EMPTY}>
              is not empty
            </MenuItem>
          </Select>
        </FormControl>
        <FormControl fullWidth size='small'>
          <InputLabel shrink>
            <Box 
              sx={{
                bgcolor: Theme.palette.background.default,
                pr: '0.5rem',
              }}
            >
              <Typography>Filter Value</Typography>
            </Box>
          </InputLabel>
          <OutlinedInput
            notched
            id='filter-value'
            label="Value"
            value={value}
            onChange={handleValueChange}
            size='small'
            sx={{
              fontSize: '0.8rem',
              color: Theme.palette.text.secondary,
              '.MuiOutlinedInput-notchedOutline': {
                  borderColor: '#404040',
              },
              '&:hover .MuiOutlinedInput-notchedOutline': {
                borderColor: '#4C7380',
              },
            }}
          >
          </OutlinedInput>
        </FormControl>
      </Box>

      <Button
        onClick={handleClick}
        sx={{ justifyContent: 'left', px: '0.85rem', borderRadius: '0' }}
      >
        <Box sx={{ display: 'flex', flexDirection: 'row', gap: '1rem', alignItems: 'center' }}>
          <FilterAltIcon sx={{ color: Theme.palette.text.secondary }} />
          <Typography>Filter</Typography>
        </Box>
      </Button>
      <Button
        onClick={handleClearClick}
        sx={{ justifyContent: 'left', px: '0.85rem', borderRadius: '0' }}
      >
        <Box sx={{ display: 'flex', flexDirection: 'row', gap: '1rem', alignItems: 'center' }}>
          <FilterAltOffIcon sx={{ color: Theme.palette.text.secondary }} />
          <Typography>Clear Filter</Typography>
        </Box>
      </Button>
    </Box>
  );
};
