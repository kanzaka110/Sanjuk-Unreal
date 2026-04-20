#!/usr/bin/env node
'use strict';

/**
 * UserPromptSubmit hook: 10분 쿨다운으로 GCP 메모리를 로컬에 자동 다운로드
 *
 * 사용자가 프롬프트를 보낼 때마다 호출되며, 마지막 다운로드가 10분 이상 전이면
 * 백그라운드로 claude-sync.sh download를 실행해 GCP 최신본을 가져온다.
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const COOLDOWN_MS = 10 * 60 * 1000;
const PROJECT_DIR = path.resolve(__dirname, '..', '..');
const SYNC_SCRIPT = path.join(PROJECT_DIR, 'scripts', 'claude-sync.sh');
const STATE_FILE = path.join(os.tmpdir(), 'sanjuk-unreal-last-download');

let stdinData = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => { stdinData += chunk; });
process.stdin.on('end', () => {
  try {
    const cwd = process.cwd().toLowerCase().replace(/\\/g, '/');
    const projectCheck = PROJECT_DIR.toLowerCase().replace(/\\/g, '/');
    if (!cwd.startsWith(projectCheck)) {
      process.stdout.write(stdinData);
      return;
    }

    const now = Date.now();
    let lastRun = 0;
    try { lastRun = fs.statSync(STATE_FILE).mtimeMs; } catch {}

    if (now - lastRun >= COOLDOWN_MS) {
      fs.writeFileSync(STATE_FILE, String(now));
      console.error('[pre-prompt-gcp-download] 쿨다운 경과 — GCP 다운로드 트리거');

      const child = spawn('bash', [SYNC_SCRIPT, 'download'], {
        cwd: PROJECT_DIR,
        detached: true,
        stdio: 'ignore'
      });
      child.unref();
    }
  } catch (err) {
    console.error(`[pre-prompt-gcp-download] 오류: ${err.message}`);
  }
  process.stdout.write(stdinData);
});
