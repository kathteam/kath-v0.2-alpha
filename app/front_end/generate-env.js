#!/usr/bin/env node
/**
 * Generate frontend environment files from network_config.yaml
 *
 * This script reads the network_config.yaml file and generates
 * appropriate .env.development and .env.production files with
 * the correct API endpoints based on the configuration.
 *
 * Usage:
 *   node generate-env.js [--config /path/to/network_config.yaml]
 */

import fs from 'fs';
import path from 'path';
import yaml from 'js-yaml';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Helper to find config file
function findConfigFile() {
  const configPaths = [
    process.env.NETWORK_CONFIG_PATH,
    '/config/network_config.yaml',
    path.join(__dirname, '../../config/network_config.yaml'),
    path.join(__dirname, '../../../config/network_config.yaml'),
    'config/network_config.yaml',
    './network_config.yaml',
  ];

  for (const configPath of configPaths) {
    if (configPath && fs.existsSync(configPath)) {
      return configPath;
    }
  }

  return null;
}

// Load YAML config
function loadConfig(configPath) {
  try {
    const fileContent = fs.readFileSync(configPath, 'utf8');
    return yaml.load(fileContent) || {};
  } catch (error) {
    console.error(`Error reading config file: ${configPath}`);
    console.error(error.message);
    return {};
  }
}

// Generate .env content
function generateEnvContent(config, isDevelopment = true) {
  const backend = config.backend || {};
  const backendHost = backend.host || 'localhost';
  const backendPort = backend.port || 8080;
  const domain = backend.domain || 'localhost';

  const apiUrl = `http://${domain}:${backendPort}/api/v1`;
  const socketUrl = `http://${domain}:${backendPort}`;

  return `# Auto-generated frontend environment configuration
# Generated from network_config.yaml
# Do not edit manually - changes will be overwritten

VITE_API_URL=${apiUrl}
VITE_SOCKET_URL=${socketUrl}
`;
}

// Main function
function main() {
  console.log('Generating frontend environment files from network configuration...');

  // Find config file
  const configPath = findConfigFile();
  if (!configPath) {
    console.warn('Warning: network_config.yaml not found. Using defaults.');
    console.warn('Create config/network_config.yaml to customize network settings.');
  }

  // Load config
  const config = configPath ? loadConfig(configPath) : {};

  // Generate .env files
  const envContent = generateEnvContent(config);
  const frontendDir = __dirname;

  // Write .env.development
  const devEnvPath = path.join(frontendDir, '.env.development');
  try {
    fs.writeFileSync(devEnvPath, envContent, 'utf8');
    console.log(`✓ Generated ${devEnvPath}`);
  } catch (error) {
    console.error(`✗ Failed to write ${devEnvPath}: ${error.message}`);
    process.exit(1);
  }

  // Write .env.production
  const prodEnvPath = path.join(frontendDir, '.env.production');
  try {
    fs.writeFileSync(prodEnvPath, envContent, 'utf8');
    console.log(`✓ Generated ${prodEnvPath}`);
  } catch (error) {
    console.error(`✗ Failed to write ${prodEnvPath}: ${error.message}`);
    process.exit(1);
  }

  // Display current configuration
  console.log('\nCurrent network configuration:');
  const backend = config.backend || {};
  const backendHost = backend.host || 'localhost';
  const backendPort = backend.port || 8080;
  const domain = backend.domain || 'localhost';
  console.log(`  Backend: http://${domain}:${backendPort}`);
  console.log(`  API URL: http://${domain}:${backendPort}/api/v1`);
}

main();
