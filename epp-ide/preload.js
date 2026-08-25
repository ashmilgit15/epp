const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('eppAPI', {
    readFile: (filePath) => ipcRenderer.invoke('read-file', filePath),
    writeFile: (filePath, content) => ipcRenderer.invoke('write-file', filePath, content),
    listFiles: (dirPath) => ipcRenderer.invoke('list-files', dirPath),
    createFile: (filePath) => ipcRenderer.invoke('create-file', filePath),
    createDirectory: (dirPath) => ipcRenderer.invoke('create-directory', dirPath),
    deleteFile: (filePath) => ipcRenderer.invoke('delete-file', filePath),
    renameFile: (oldPath, newPath) => ipcRenderer.invoke('rename-file', oldPath, newPath),
    runEpp: (filePath) => ipcRenderer.invoke('run-epp', filePath),
    stopRun: () => ipcRenderer.invoke('stop-run'),
    onRunOutput: (callback) => ipcRenderer.on('run-output', (event, data) => callback(data)),
    onRunComplete: (callback) => ipcRenderer.on('run-complete', (event, code) => callback(code)),
    getHomePath: () => ipcRenderer.invoke('get-home-path'),
    pathJoin: (...parts) => ipcRenderer.invoke('path-join', ...parts),
    pathDirname: (filePath) => ipcRenderer.invoke('path-dirname', filePath),
    showSaveDialog: (options) => ipcRenderer.invoke('show-save-dialog', options),
    showOpenDialog: (options) => ipcRenderer.invoke('show-open-dialog', options),
    chatWithAI: (messages) => ipcRenderer.invoke('chat-with-ai', messages),
    getAiStatus: () => ipcRenderer.invoke('get-ai-status'),
    onAiStreamChunk: (callback) => ipcRenderer.on('ai-stream-chunk', (event, chunk) => callback(chunk))
});