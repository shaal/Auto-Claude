/**
 * Web mode initializer.
 * In the web Vite build, this file replaces browser-mock via alias.
 * It sets up window.electronAPI with real HTTP/WS calls for core operations,
 * falling back to browser mock data for unimplemented methods.
 */
import type { ElectronAPI } from '../../shared/types';
import { createWebAPI } from './web-api-client';
import {
  projectMock,
  taskMock,
  workspaceMock,
  terminalMock,
  claudeProfileMock,
  contextMock,
  integrationMock,
  changelogMock,
  insightsMock,
  infrastructureMock,
  settingsMock,
} from './mocks';

// Build the full mock as fallback base (same structure as browser-mock.ts)
const fallbackMock: ElectronAPI = {
  ...projectMock,
  ...taskMock,
  ...workspaceMock,
  ...terminalMock,
  ...claudeProfileMock,
  ...settingsMock,

  // Roadmap stubs
  getRoadmap: async () => ({ success: true, data: null }),
  getRoadmapStatus: async () => ({ success: true, data: { isRunning: false } }),
  saveRoadmap: async () => ({ success: true }),
  generateRoadmap: () => {},
  refreshRoadmap: () => {},
  updateFeatureStatus: async () => ({ success: true }),
  convertFeatureToSpec: async (projectId: string) => ({
    success: true,
    data: {
      id: `task-${Date.now()}`,
      specId: '',
      projectId,
      title: 'Converted Feature',
      description: '',
      status: 'backlog' as const,
      subtasks: [],
      logs: [],
      createdAt: new Date(),
      updatedAt: new Date(),
    },
  }),
  stopRoadmap: async () => ({ success: true }),
  onRoadmapProgress: () => () => {},
  onRoadmapComplete: () => () => {},
  onRoadmapError: () => () => {},
  onRoadmapStopped: () => () => {},

  ...contextMock,
  ...integrationMock,
  ...changelogMock,
  ...insightsMock,
  ...infrastructureMock,

  // API Profile stubs
  getAPIProfiles: async () => ({
    success: true,
    data: { profiles: [], activeProfileId: null, version: 1 },
  }),
  saveAPIProfile: async (profile: any) => ({
    success: true,
    data: { id: `mock-${Date.now()}`, ...profile, createdAt: Date.now(), updatedAt: Date.now() },
  }),
  updateAPIProfile: async (profile: any) => ({
    success: true,
    data: { ...profile, updatedAt: Date.now() },
  }),
  deleteAPIProfile: async () => ({ success: true }),
  setActiveAPIProfile: async () => ({ success: true }),
  testConnection: async () => ({
    success: true,
    data: { success: true, message: 'Mock' },
  }),
  discoverModels: async () => ({ success: true, data: { models: [] } }),

  // GitHub stubs
  github: {
    getGitHubRepositories: async () => ({ success: true, data: [] }),
    getGitHubIssues: async () => ({ success: true, data: [] }),
    getGitHubIssue: async () => ({ success: true, data: null as any }),
    getIssueComments: async () => ({ success: true, data: [] }),
    checkGitHubConnection: async () => ({
      success: true,
      data: { connected: false, repoFullName: undefined, error: undefined },
    }),
    investigateGitHubIssue: () => {},
    importGitHubIssues: async () => ({
      success: true,
      data: { success: true, imported: 0, failed: 0, issues: [] },
    }),
    createGitHubRelease: async () => ({ success: true, data: { url: '' } }),
    suggestReleaseVersion: async () => ({
      success: true,
      data: {
        suggestedVersion: '1.0.0',
        currentVersion: '0.0.0',
        bumpType: 'minor' as const,
        commitCount: 0,
        reason: 'Initial',
      },
    }),
    checkGitHubCli: async () => ({ success: true, data: { installed: false } }),
    checkGitHubAuth: async () => ({ success: true, data: { authenticated: false } }),
    startGitHubAuth: async () => ({ success: true, data: { success: false } }),
    getGitHubToken: async () => ({ success: true, data: { token: '' } }),
    getGitHubUser: async () => ({ success: true, data: { username: '' } }),
    listGitHubUserRepos: async () => ({ success: true, data: { repos: [] } }),
    detectGitHubRepo: async () => ({ success: true, data: '' }),
    getGitHubBranches: async () => ({ success: true, data: [] }),
    createGitHubRepo: async () => ({ success: true, data: { fullName: '', url: '' } }),
    addGitRemote: async () => ({ success: true, data: { remoteUrl: '' } }),
    listGitHubOrgs: async () => ({ success: true, data: { orgs: [] } }),
    onGitHubAuthDeviceCode: () => () => {},
    onGitHubInvestigationProgress: () => () => {},
    onGitHubInvestigationComplete: () => () => {},
    onGitHubInvestigationError: () => () => {},
    getAutoFixConfig: async () => null,
    saveAutoFixConfig: async () => true,
    getAutoFixQueue: async () => [],
    checkAutoFixLabels: async () => [],
    checkNewIssues: async () => [],
    startAutoFix: () => {},
    onAutoFixProgress: () => () => {},
    onAutoFixComplete: () => () => {},
    onAutoFixError: () => () => {},
    listPRs: async () => [],
    runPRReview: () => {},
    cancelPRReview: async () => true,
    postPRReview: async () => true,
    postPRComment: async () => true,
    mergePR: async () => true,
    assignPR: async () => true,
    getPRReview: async () => null,
    deletePRReview: async () => true,
    checkNewCommits: async () => ({ hasNewCommits: false, newCommitCount: 0 }),
    runFollowupReview: () => {},
    getPRLogs: async () => null,
    onPRReviewProgress: () => () => {},
    onPRReviewComplete: () => () => {},
    onPRReviewError: () => () => {},
    batchAutoFix: () => {},
    getBatches: async () => [],
    onBatchProgress: () => () => {},
    onBatchComplete: () => () => {},
    onBatchError: () => () => {},
    analyzeIssuesPreview: () => {},
    approveBatches: async () => ({ success: true, batches: [] }),
    onAnalyzePreviewProgress: () => () => {},
    onAnalyzePreviewComplete: () => () => {},
    onAnalyzePreviewError: () => () => {},
  },

  // System stubs
  checkClaudeCodeVersion: async () => ({
    success: true,
    data: {
      installed: '1.0.0',
      latest: '1.0.0',
      isOutdated: false,
      path: '/usr/local/bin/claude',
      detectionResult: {
        found: true,
        version: '1.0.0',
        path: '/usr/local/bin/claude',
        source: 'system-path' as const,
        message: 'Found',
      },
    },
  }),
  installClaudeCode: async () => ({
    success: true,
    data: { command: 'npm install -g @anthropic-ai/claude-code' },
  }),
  checkMcpHealth: async (server: any) => ({
    success: true,
    data: {
      serverId: server.id,
      status: 'unknown' as const,
      message: 'Not available in web mode',
      checkedAt: new Date().toISOString(),
    },
  }),
  testMcpConnection: async (server: any) => ({
    success: true,
    data: { serverId: server.id, success: false, message: 'Not available in web mode' },
  }),
  getDebugInfo: async () => ({
    systemInfo: { appVersion: '0.0.0-web', platform: 'web', isPackaged: 'false' },
    recentErrors: [],
    logsPath: '/web/logs',
    debugReport: 'Web mode - debug report not available',
  }),
  openLogsFolder: async () => ({ success: false, error: 'Not available in web mode' }),
  copyDebugInfo: async () => ({ success: false, error: 'Not available in web mode' }),
  getRecentErrors: async () => [],
  listLogFiles: async () => [],
} as ElectronAPI;

// Create the real web API (overrides core methods with real backend calls)
const webAPI = createWebAPI();

// Merge: real web API methods override mock fallbacks
const mergedAPI: ElectronAPI = {
  ...fallbackMock,
  ...webAPI,
} as ElectronAPI;

// Install on window
console.info(
  '%c[Web Mode] API client initialized with real backend connection',
  'color: #4CAF50; font-weight: bold;'
);
(window as Window & { electronAPI: ElectronAPI }).electronAPI = mergedAPI;
