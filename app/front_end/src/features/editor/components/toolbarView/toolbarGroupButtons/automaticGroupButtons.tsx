import { ToolbarGroupItem, ToolbarGroupItemProps } from '@/features/editor/components/toolbarView';
import { useToolbarContext, useWorkspaceContext } from '@/features/editor/hooks';
import { defaultSaveTo } from '@/features/editor/stores';
import { findUniqueFileName, generateTimestamp, getFileExtension } from '@/features/editor/utils';
import { useStatusContext } from '@/hooks';
import { AutoMode as AutoModeIcon } from '@mui/icons-material';
import { useCallback, useMemo } from 'react';

export interface AutomaticGroupButtonsProps {}

export const AutomaticGroupButtons: React.FC<AutomaticGroupButtonsProps> = () => {
  const { blockedStateUpdate } = useStatusContext();
  const { fileTree } = useWorkspaceContext();
  const { saveTo, saveToErrorStateUpdate, override, gene } = useToolbarContext();

  const handlePerformAllClick = useCallback(async () => {
    blockedStateUpdate(true);

    try {
      const timestamp = generateTimestamp();
      const savePath = saveTo !== defaultSaveTo ? saveTo.id : findUniqueFileName(fileTree, `auto_${timestamp}.txt`);
      if (getFileExtension(savePath) !== 'txt') {
        saveToErrorStateUpdate('Select .txt');
        return;
      }
      saveToErrorStateUpdate('');

      // await axios.get(`${Endpoints.WORKSPACE_X}/${savePath}`, {
      //   params: {
      //     source: 'x',
      //     override,
      //     gene,
      //   },
      // });
    } catch (error) {
      console.error('Error downloading performing automatic task:', error);
    } finally {
      blockedStateUpdate(false);
    }
  }, [saveTo, override, gene]);

  const buttons: ToolbarGroupItemProps[] = useMemo(
    () => [
      {
        group: 'automatic',
        icon: AutoModeIcon,
        label: 'Perform All',
        onClick: handlePerformAllClick,
      },
    ],
    [handlePerformAllClick]
  );

  return (
    <>
      {buttons.map((button, index) => (
        <ToolbarGroupItem key={index} {...button} />
      ))}
    </>
  );
};
