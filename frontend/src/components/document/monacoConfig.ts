const EXTENSION_LANGUAGE_MAP: Record<string, string> = {
  '.py': 'python',
  '.js': 'javascript',
  '.jsx': 'javascript',
  '.mjs': 'javascript',
  '.ts': 'typescript',
  '.tsx': 'typescript',
  '.java': 'java',
  '.go': 'go',
  '.rb': 'ruby',
  '.php': 'php',
  '.c': 'c',
  '.h': 'c',
  '.cpp': 'cpp',
  '.hpp': 'cpp',
  '.cs': 'csharp',
  '.html': 'html',
  '.css': 'css',
  '.json': 'json',
  '.md': 'markdown',
  '.sql': 'sql',
  '.sh': 'shell',
  '.yml': 'yaml',
  '.yaml': 'yaml',
}

/** Maps a TaskCodeFile.file_extension to the Monaco Editor language id. */
export function getMonacoLanguage(extension: string | null): string {
  if (!extension) {
    return 'plaintext'
  }
  return EXTENSION_LANGUAGE_MAP[extension.toLowerCase()] ?? 'plaintext'
}
