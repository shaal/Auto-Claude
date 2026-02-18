/**
 * Web mode initializer.
 * In the web Vite build, this file replaces browser-mock via alias.
 * It sets up window.electronAPI with real HTTP/WS calls for core operations,
 * falling back to browser mock data for unimplemented methods.
 *
 * IMPORTANT: The fallbackMock MUST mirror browser-mock.ts exactly.
 * If browser-mock.ts adds new methods, they must be added here too,
 * otherwise the app will crash with "is not a function" errors.
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

// Build the full mock as fallback base (mirrors browser-mock.ts exactly)
const fallbackMock: ElectronAPI = {
  // Project Operations
  ...projectMock,

  // Task Operations
  ...taskMock,

  // Workspace Management
  ...workspaceMock,

  // Terminal Operations
  ...terminalMock,

  // Claude Profile Management
  ...claudeProfileMock,

  // Settings
  ...settingsMock,

  // Roadmap Operations
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

  // Roadmap Progress Persistence
  saveRoadmapProgress: async () => ({ success: true }),
  loadRoadmapProgress: async () => ({ success: true, data: null }),
  clearRoadmapProgress: async () => ({ success: true }),

  // Roadmap Event Listeners
  onRoadmapProgress: () => () => {},
  onRoadmapComplete: () => () => {},
  onRoadmapError: () => () => {},
  onRoadmapStopped: () => () => {},

  // Context Operations
  ...contextMock,

  // Environment Configuration & Integration Operations
  ...integrationMock,

  // Changelog & Release Operations
  ...changelogMock,

  // Insights Operations
  ...insightsMock,

  // Infrastructure & Docker Operations
  ...infrastructureMock,

  // API Profile Management
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

  // GitHub API
  github: {
    getGitHubRepositories: async () => ({ success: true, data: [] }),
    getGitHubIssues: async () => ({ success: true, data: { issues: [], hasMore: false } }),
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
    onGitHubAuthChanged: () => () => {},
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
    listPRs: async () => ({ prs: [], hasNextPage: false }),
    listMorePRs: async () => ({ prs: [], hasNextPage: false }),
    getPR: async () => null,
    runPRReview: () => {},
    cancelPRReview: async () => true,
    postPRReview: async () => true,
    postPRComment: async () => true,
    mergePR: async () => true,
    assignPR: async () => true,
    markReviewPosted: async () => true,
    getPRReview: async () => null,
    getPRReviewsBatch: async () => ({}),
    deletePRReview: async () => true,
    checkNewCommits: async () => ({ hasNewCommits: false, newCommitCount: 0 }),
    checkMergeReadiness: async () => ({
      isDraft: false,
      mergeable: 'UNKNOWN' as const,
      isBehind: false,
      ciStatus: 'none' as const,
      blockers: [],
    }),
    updatePRBranch: async () => ({ success: true }),
    runFollowupReview: () => {},
    getPRLogs: async () => null,
    getWorkflowsAwaitingApproval: async () => ({
      awaiting_approval: 0,
      workflow_runs: [],
      can_approve: false,
    }),
    approveWorkflow: async () => true,
    onPRReviewProgress: () => () => {},
    onPRReviewComplete: () => () => {},
    onPRReviewError: () => () => {},
    onPRLogsUpdated: () => () => {},
    batchAutoFix: () => {},
    getBatches: async () => [],
    onBatchProgress: () => () => {},
    onBatchComplete: () => () => {},
    onBatchError: () => () => {},
    // Analyze & Group Issues (proactive workflow)
    analyzeIssuesPreview: () => {},
    approveBatches: async () => ({ success: true, batches: [] }),
    onAnalyzePreviewProgress: () => () => {},
    onAnalyzePreviewComplete: () => () => {},
    onAnalyzePreviewError: () => () => {},
    // PR status polling
    startStatusPolling: async () => true,
    stopStatusPolling: async () => true,
    getPollingMetadata: async () => null,
    onPRStatusUpdate: () => () => {},
  },

  // Queue Routing API (rate limit recovery)
  queue: {
    getRunningTasksByProfile: async () => ({ success: true, data: { byProfile: {}, totalRunning: 0 } }),
    getBestProfileForTask: async () => ({ success: true, data: null }),
    getBestUnifiedAccount: async () => ({ success: true, data: null }),
    assignProfileToTask: async () => ({ success: true }),
    updateTaskSession: async () => ({ success: true }),
    getTaskSession: async () => ({ success: true, data: null }),
    onQueueProfileSwapped: () => () => {},
    onQueueSessionCaptured: () => () => {},
    onQueueBlockedNoProfiles: () => () => {},
  },

  // Claude Code Operations
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
  getClaudeCodeVersions: async () => ({
    success: true,
    data: { versions: ['1.0.5', '1.0.4', '1.0.3', '1.0.2', '1.0.1', '1.0.0'] },
  }),
  installClaudeCodeVersion: async (version: string) => ({
    success: true,
    data: { command: `npm install -g @anthropic-ai/claude-code@${version}`, version },
  }),
  getClaudeCodeInstallations: async () => ({
    success: true,
    data: {
      installations: [
        {
          path: '/usr/local/bin/claude',
          version: '1.0.0',
          source: 'system-path' as const,
          isActive: true,
        },
      ],
      activePath: '/usr/local/bin/claude',
    },
  }),
  setClaudeCodeActivePath: async (cliPath: string) => ({
    success: true,
    data: { path: cliPath },
  }),

  // Worktree Change Detection
  checkWorktreeChanges: async () => ({
    success: true,
    data: { hasChanges: false, changedFileCount: 0 },
  }),

  // Terminal Worktree Operations
  createTerminalWorktree: async () => ({
    success: false,
    error: 'Not available in web mode',
  }),
  listTerminalWorktrees: async () => ({
    success: true,
    data: [],
  }),
  removeTerminalWorktree: async () => ({
    success: false,
    error: 'Not available in web mode',
  }),
  listOtherWorktrees: async () => ({
    success: true,
    data: [],
  }),

  // MCP Server Health Check Operations
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

  // Screenshot capture operations
  getSources: async () => ({
    success: true,
    data: [],
  }),
  capture: async () => ({
    success: false,
    error: 'Screenshot capture not available in web mode',
  }),

  // Debug Operations
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
  'color: #4CAF50; font-weight: bold;',
);
(window as Window & { electronAPI: ElectronAPI }).electronAPI = mergedAPI;
