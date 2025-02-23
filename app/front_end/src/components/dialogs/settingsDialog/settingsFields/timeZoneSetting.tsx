import { SettingsSelectField } from '@/components/dialogs/settingsDialog';
import { SelectChangeEvent } from '@mui/material';
import { useState } from 'react';

export const TimeZoneSetting = () => {
  // TODO: Implement time zone switching functionality and replace with correct values

  const [switchTimeZone, setSwitchTimeZone] = useState('local');

  const handleTimeZoneChange = (event: SelectChangeEvent<string>) => {
    const selectedValue = event.target.value;
    setSwitchTimeZone(selectedValue);
  };

  return (
    <SettingsSelectField
      title='Time zone'
      description='Change the time zone of the application'
      settings={[{ value: 'local', label: 'Local' }]}
      value={switchTimeZone}
      onChange={handleTimeZoneChange}
    />
  );
};
