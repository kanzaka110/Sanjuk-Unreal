#!/usr/bin/env node
'use strict';

/**
 * PostToolUse(Write|Edit) hook: 메모리 파일 변경 시 GCP에 자동 업로드
 *
 * Write/Edit이 ~/.claude/projects/C--Dev-Sanjuk-Unreal/memory/ 경로를 건드리면
 * 백그라운드로 claude-sync.sh upload를 실행한다. 쿨다운 30초로 연쇄 편집 시 합친다.
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const COOLDOWN_MS = 30 * 1000;
const PROJECT_DIR = path.resolve(__dirname, '..', '..');
const SYNC_SCRIPT = path.join(PROJECT_DIR, 'scripts', 'claude-sync.sh');
const STATE_FILE = path.join(os.tmpdir(), 'sanjuk-unreal-last-upload');

const MEMORY_FRAGMENT = path.join('.claude', 'projects', 'C--Dev-Sanjuk-Unreal', 'memory').toLowerCase();

let stdinData = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => { stdinData += chunk; });
process.stdin.on('end', () => {
  try {
    const input = JSON.parse(stdinData);
    const toolName = input.tool_name || input.toolName || '';
    const ti = input.tool_input || input.toolInput || {};
    const filePath = String(ti.file_path || ti.filePath || '').toLowerCase().replace(/\\/g, '/');

    const isWriteEdit = /^(Write|Edit)$/.test(toolName);
    const fragment = MEMORY_FRAGMENT.replace(/\\/g, '/');

    if (isWriteEdit && filePath.includes(fragment)) {
      const now = Date.now();
      let lastRun = 0;
      try { lastRun = fs.statSync(STATE_FILE).mtimeMs; } catch {}

      if (now - lastRun >= COOLDOWN_MS) {
        fs.writeFileSync(STATE_FILE, String(now));
        console.error('[post-edit-memory-upload] 메모리 변경 감지 — GCP 업로드 트리거');

        const child = spawn('bash', [SYNC_SCRIPT, 'upload'], {
          cwd: PROJECT_DIR,
          detached: true,
          stdio: 'ignore'
        });
        child.unref();
      }
    }
  } catch (err) {
    console.error(`[post-edit-memory-upload] 오류: ${err.message}`);
  }
  process.stdout.write(stdinData);
});
