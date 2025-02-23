import { IconTitleButton } from '@/components/buttons/IconTitleButton';
import { ExternalLinks, Paths } from '@/types';
import {
  AutoStories as AutoStoriesIcon,
  ErrorOutline as BugReportIcon,
  Home as HomeIcon,
  SettingsOutlined as SettingsOutlinedIcon,
} from '@mui/icons-material';
import { Box } from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';

interface SidebarProps {
  settingsDialogOpen: () => void;
  feedbackDialogOpen: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ settingsDialogOpen, feedbackDialogOpen }) => {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <Box sx={{ width: '4.2vw', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box
        sx={{
          width: '100%',
          height: '50%',
          paddingTop: '0.625rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.625rem',
          alignItems: 'center',
        }}
      >
        <IconTitleButton
          icon={
            <HomeIcon
              sx={{
                width: '1.5rem',
                height: '1.5rem',
              }}
            />
          }
          title={'Home'}
          isActive={location.pathname === Paths.HOME}
          onClick={() => navigate(Paths.HOME)}
        />
        <IconTitleButton
          icon={
            <AutoStoriesIcon
              sx={{
                width: '1.4rem',
                height: '1.4rem',
              }}
            />
          }
          title={'Manual'}
          isActive={false}
          onClick={() => window.open(ExternalLinks.MANUAL, '_blank', 'noopener,noreferrer')}
        />
        {/* <IconTitleButton
          icon={
            <AutoModeIcon
              sx={{
                width: '1.5rem',
                height: '1.5rem',
              }}
            />
          }
          title={'Macros'}
          isActive={location.pathname === Paths.MACROS}
          onClick={() => navigate(Paths.MACROS)}
          disabled
        /> */}
      </Box>
      <Box
        sx={{
          width: '100%',
          height: '50%',
          paddingBottom: '0.625rem',
          display: 'flex',
          flexDirection: 'column-reverse',
          gap: '0.625rem',
          alignItems: 'center',
        }}
      >
        <IconTitleButton
          icon={<SettingsOutlinedIcon sx={{ width: '1.5rem', height: '1.5rem' }} />}
          onClick={settingsDialogOpen}
        />
        <IconTitleButton
          icon={<BugReportIcon sx={{ width: '1.5rem', height: '1.5rem' }} />}
          onClick={feedbackDialogOpen}
        />
      </Box>
    </Box>
  );
};
