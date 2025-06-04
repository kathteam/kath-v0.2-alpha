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
    // Last step is Revel, therefore we check for errors for Revel and use the save to path only for Revel file
    const revelTimestamp = generateTimestamp();
    const revelSavePath =
      saveTo.id !== defaultSaveTo.id ? saveTo.id : findUniqueFileName(fileTree, `auto_revel_${revelTimestamp}.csv`);
    if (getFileExtension(revelSavePath) !== 'csv') {
      saveToErrorStateUpdate('Select .csv');
      return;
    }

    blockedStateUpdate(true);

    try {
      // --- Download LOVD ---
      const lovdFilePath = findUniqueFileName(fileTree, `lovd_${generateTimestamp()}.txt`);
      await axios.get(`${Endpoints.WORKSPACE_DOWNLOAD}/${lovdFilePath}`, {
        params: { source: 'lovd', override, gene },
      });

      await new Promise((resolve) => setTimeout(resolve, 500)); // Simulated delay, because workspace structure needs time to update
      blockedStateUpdate(true); // Auto-Refreshing workspace unblocks the UI, need to reblock again

      // --- Download ClinVar ---
      const clinvarFilePath = findUniqueFileName(fileTree, `clinvar_${generateTimestamp()}.csv`);
      await axios.get(`${Endpoints.WORKSPACE_DOWNLOAD}/${clinvarFilePath}`, {
        params: { source: 'clinvar', override, gene },
      });

      await new Promise((resolve) => setTimeout(resolve, 500)); // Simulated delay, because workspace structure needs time to update
      blockedStateUpdate(true);

      // --- Download gnomAD ---
      const gnomadFilePath = findUniqueFileName(fileTree, `gnomad_${generateTimestamp()}.csv`);
      await axios.get(`${Endpoints.WORKSPACE_DOWNLOAD}/${gnomadFilePath}`, {
        params: { source: 'gnomad', override, gene },
      });

      await new Promise((resolve) => setTimeout(resolve, 500)); // Simulated delay, because workspace structure needs time to update
      blockedStateUpdate(true);

      // --- Merge ALL ---
      const mergeAllFilePath = findUniqueFileName(fileTree, `all_merged_${generateTimestamp()}.csv`);
      await axios.get(`${Endpoints.WORKSPACE_MERGE}/all/${mergeAllFilePath}`, {
        params: {
          override,
          lovdFile: lovdFilePath,
          clinvarFile: clinvarFilePath,
          gnomadFile: gnomadFilePath,
          customFile: '',
        },
      });

      await new Promise((resolve) => setTimeout(resolve, 500)); // Simulated delay, because workspace structure needs time to update
      blockedStateUpdate(true);

      // --- Apply SpliceAI ---
      const applySpliceAiFilePath = findUniqueFileName(fileTree, `spliceai_${generateTimestamp()}.csv`);
      await axios.get(`${Endpoints.WORKSPACE_APPLY}/spliceai/${applySpliceAiFilePath}`, {
        params: {
          override,
          applyTo: mergeAllFilePath,
        },
      });

      await new Promise((resolve) => setTimeout(resolve, 500)); // Simulated delay, because workspace structure needs time to update
      blockedStateUpdate(true);

      // --- Apply CADD ---
      const applyCaddFilePath = findUniqueFileName(fileTree, `cadd_${generateTimestamp()}.csv`);
      await axios.get(`${Endpoints.WORKSPACE_APPLY}/cadd/${applyCaddFilePath}`, {
        params: {
          override,
          applyTo: applySpliceAiFilePath,
        },
      });

      await new Promise((resolve) => setTimeout(resolve, 500)); // Simulated delay, because workspace structure needs time to update
      blockedStateUpdate(true);

      // --- Apply REVEL ---
      await axios.get(`${Endpoints.WORKSPACE_APPLY}/revel/${revelSavePath}`, {
        params: {
          override,
          applyTo: applyCaddFilePath,
        },
      });
    } catch (error) {
      console.error('Automated task failed:', error);
    } finally {
      blockedStateUpdate(false);
    }
  }, [fileTree, override, gene]);

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
