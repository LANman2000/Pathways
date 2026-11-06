import { spawn } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const appDirectory = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const repositoryRoot = resolve(appDirectory, '../..');
const python = process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
const serveBuiltApp = process.argv.includes('--serve');
const pythonEnvironment = {
  ...process.env,
  PATHWAYS_ANALYSIS_PORT: process.env.PATHWAYS_ANALYSIS_PORT || '5000',
};
const children = [
  spawn(
    python,
    [
      resolve(appDirectory, 'server/auth.py'),
      ...(serveBuiltApp ? ['--serve'] : []),
    ],
    { cwd: repositoryRoot, env: pythonEnvironment, stdio: 'inherit' },
  ),
  spawn(python, ['-m', 'web.app'], {
    cwd: repositoryRoot,
    env: pythonEnvironment,
    stdio: 'inherit',
  }),
];

if (!serveBuiltApp) {
  children.push(
    spawn(
      process.execPath,
      [
        resolve(appDirectory, 'node_modules/vite/bin/vite.js'),
        '--host',
        '127.0.0.1',
        '--port',
        '5173',
        '--strictPort',
      ],
      { cwd: appDirectory, env: process.env, stdio: 'inherit' },
    ),
  );
}

let stopping = false;
function stop(code = 0) {
  if (stopping) return;
  stopping = true;
  for (const child of children) child.kill('SIGTERM');
  process.exitCode = code;
}

for (const child of children) {
  child.on('error', error => {
    console.error(error.message);
    stop(1);
  });
  child.on('exit', code => stop(code || 0));
}
process.on('SIGINT', () => stop());
process.on('SIGTERM', () => stop());
