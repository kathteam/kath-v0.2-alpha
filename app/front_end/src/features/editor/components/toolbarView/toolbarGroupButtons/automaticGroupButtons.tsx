import { ToolbarGroupItem, ToolbarGroupItemProps } from '@/features/editor/components/toolbarView';
import { useToolbarContext, useWorkspaceContext } from '@/features/editor/hooks';
import { defaultSaveTo } from '@/features/editor/stores';
import { findUniqueFileName, generateTimestamp, getFileExtension } from '@/features/editor/utils';
import { useStatusContext } from '@/hooks';
import { axios } from '@/lib';
import { Endpoints } from '@/types';
import { AutoMode as AutoModeIcon } from '@mui/icons-material';
import { useCallback, useMemo } from 'react';

export interface AutomaticGroupButtonsProps {}

export const AutomaticGroupButtons: React.FC<AutomaticGroupButtonsProps> = () => {
  const { blockedStateUpdate } = useStatusContext();
  const { fileTree } = useWorkspaceContext();
  const { saveTo, saveToErrorStateUpdate, override, gene } = useToolbarContext();

  const handlePerformAllClick = useCallback(async () => {
    try {
      // --- Download LOVD ---
      blockedStateUpdate(true);
      let lovdFilePath = '';
      try {
        const timestamp = generateTimestamp();
        const savePath = findUniqueFileName(fileTree, `lovd_${timestamp}.txt`);

        await axios.get(`${Endpoints.WORKSPACE_DOWNLOAD}/${savePath}`, {
          params: { source: 'lovd', override, gene },
        });
        lovdFilePath = savePath;
      } catch (error) {
        console.error('Error downloading LOVD file:', error);
      } finally {
        blockedStateUpdate(false);
      }

      // Simulated delay, because workspace structure needs time to update
      await new Promise((resolve) => setTimeout(resolve, 500));

      // --- Download ClinVar ---
      blockedStateUpdate(true);
      let clinvarFilePath = '';
      try {
        const timestamp = generateTimestamp();
        const savePath = findUniqueFileName(fileTree, `clinvar_${timestamp}.csv`);

        await axios.get(`${Endpoints.WORKSPACE_DOWNLOAD}/${savePath}`, {
          params: { source: 'clinvar', override, gene },
        });
        clinvarFilePath = savePath;
      } catch (error) {
        console.error('Error downloading ClinVar file:', error);
      } finally {
        blockedStateUpdate(false);
      }

      // Simulated delay, because workspace structure needs time to update
      await new Promise((resolve) => setTimeout(resolve, 500));

      // --- Download gnomAD ---
      blockedStateUpdate(true);
      let gnomadFilePath = '';
      try {
        const timestamp = generateTimestamp();
        const savePath = findUniqueFileName(fileTree, `gnomad_${timestamp}.csv`);

        await axios.get(`${Endpoints.WORKSPACE_DOWNLOAD}/${savePath}`, {
          params: { source: 'gnomad', override, gene },
        });
        gnomadFilePath = savePath;
      } catch (error) {
        console.error('Error downloading gnomAD file:', error);
      } finally {
        blockedStateUpdate(false);
      }

      await new Promise((resolve) => setTimeout(resolve, 500));
      // --- Merge ALL ---
      blockedStateUpdate(true);
      let mergeAllFilePath = '';
      try {
        const timestamp = generateTimestamp();
        const savePath = findUniqueFileName(fileTree, `all_merged_${timestamp}.csv`);

        await axios.get(`${Endpoints.WORKSPACE_MERGE}/all/${savePath}`, {
          params: {
            override,
            lovdFile: lovdFilePath,
            clinvarFile: clinvarFilePath,
            gnomadFile: gnomadFilePath,
            customFile: '',
          },
        });
        mergeAllFilePath = savePath;
      } catch (error) {
        console.error('Error merging all files:', error);
      } finally {
        blockedStateUpdate(false);
      }

      // Simulated delay, because workspace structure needs time to update
      await new Promise((resolve) => setTimeout(resolve, 500));

      // --- Apply All ---
      // (Last step for Automatic Task, so the file name is auto_X.csv)
      blockedStateUpdate(true);
      try {
        const timestamp = generateTimestamp();
        const savePath =
          saveTo.id !== defaultSaveTo.id ? saveTo.id : findUniqueFileName(fileTree, `auto_${timestamp}.csv`);
        if (getFileExtension(savePath) !== 'csv') {
          saveToErrorStateUpdate('Select .csv');
          return;
        }
        await axios.get(`${Endpoints.WORKSPACE_APPLY}/all/${savePath}`, {
          params: { override, applyTo: mergeAllFilePath },
        });
      } catch (error) {
        console.error('Error applying ALL:', error);
      } finally {
        blockedStateUpdate(false);
      }
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
