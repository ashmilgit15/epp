const { app, BrowserWindow, ipcMain, net } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

let mainWindow;
let runningProcess = null;
let eppPath;

function getEppPath() {
    // Try multiple locations
    const possiblePaths = [
        path.join(process.resourcesPath, 'dist', 'epp'),
        path.join(__dirname, 'dist', 'epp'),
        path.join(__dirname, '..', 'dist', 'epp'),
        path.join(__dirname, 'resources', 'dist', 'epp')
    ];
    
    if (process.platform === 'win32') {
        possiblePaths.push(
            path.join(process.resourcesPath, 'dist', 'epp.exe'),
            path.join(__dirname, 'dist', 'epp.exe')
        );
    }
    
    for (const p of possiblePaths) {
        if (fs.existsSync(p)) {
            return p;
        }
    }
    
    // Fallback
    return path.join(process.resourcesPath, 'dist', 'epp');
}

eppPath = getEppPath();

app.disableHardwareAcceleration();
app.commandLine.appendSwitch('disable-gpu');
app.commandLine.appendSwitch('disable-software-rasterizer');

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 800,
        minHeight: 600,
        backgroundColor: '#1e1e1e',
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        }
    });

    mainWindow.maximize();

    mainWindow.loadFile('index.html');
    mainWindow.setMenuBarVisibility(false);
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

ipcMain.handle('read-file', async (event, filePath) => {
    try {
        const content = fs.readFileSync(filePath, 'utf-8');
        return { success: true, content };
    } catch (error) {
        return { success: false, error: error.message };
    }
});

ipcMain.handle('write-file', async (event, filePath, content) => {
    try {
        fs.writeFileSync(filePath, content, 'utf-8');
        return { success: true };
    } catch (error) {
        return { success: false, error: error.message };
    }
});

ipcMain.handle('list-files', async (event, dirPath) => {
    try {
        const files = fs.readdirSync(dirPath).map(name => {
            const fullPath = path.join(dirPath, name);
            const stat = fs.statSync(fullPath);
            return {
                name,
                path: fullPath,
                isDirectory: stat.isDirectory(),
                isFile: stat.isFile()
            };
        });
        return { success: true, files };
    } catch (error) {
        return { success: false, error: error.message };
    }
});

ipcMain.handle('create-file', async (event, filePath) => {
    try {
        fs.writeFileSync(filePath, '', 'utf-8');
        return { success: true };
    } catch (error) {
        return { success: false, error: error.message };
    }
});

ipcMain.handle('create-directory', async (event, dirPath) => {
    try {
        fs.mkdirSync(dirPath, { recursive: true });
        return { success: true };
    } catch (error) {
        return { success: false, error: error.message };
    }
});

ipcMain.handle('delete-file', async (event, filePath) => {
    try {
        if (fs.statSync(filePath).isDirectory()) {
            fs.rmSync(filePath, { recursive: true });
        } else {
            fs.unlinkSync(filePath);
        }
        return { success: true };
    } catch (error) {
        return { success: false, error: error.message };
    }
});

ipcMain.handle('run-epp', async (event, filePath) => {
    return new Promise((resolve) => {
        const output = [];
        
        if (runningProcess) {
            runningProcess.kill();
            runningProcess = null;
        }

        runningProcess = spawn(eppPath, [filePath], {
            cwd: path.dirname(filePath)
        });

        runningProcess.stdout.on('data', (data) => {
            const text = data.toString();
            output.push(text);
            mainWindow.webContents.send('run-output', text);
        });

        runningProcess.stderr.on('data', (data) => {
            const text = data.toString();
            output.push(text);
            mainWindow.webContents.send('run-output', text);
        });

        runningProcess.on('close', (code) => {
            runningProcess = null;
            resolve({ success: true, output: output.join(''), code });
            mainWindow.webContents.send('run-complete', code);
        });

        runningProcess.on('error', (err) => {
            runningProcess = null;
            resolve({ success: false, error: err.message });
        });
    });
});

ipcMain.handle('stop-run', async () => {
    if (runningProcess) {
        runningProcess.kill();
        runningProcess = null;
        return { success: true };
    }
    return { success: false, error: 'No process running' };
});

ipcMain.handle('rename-file', async (event, oldPath, newPath) => {
    try {
        fs.renameSync(oldPath, newPath);
        return { success: true };
    } catch (error) {
        return { success: false, error: error.message };
    }
});

ipcMain.handle('get-home-path', async () => {
    return app.getPath('home');
});

ipcMain.handle('path-join', async (event, ...parts) => {
    return path.join(...parts);
});

ipcMain.handle('path-dirname', async (event, filePath) => {
    return path.dirname(filePath);
});

ipcMain.handle('show-save-dialog', async (event, options) => {
    const { dialog } = require('electron');
    return dialog.showSaveDialog(mainWindow, options);
});

ipcMain.handle('show-open-dialog', async (event, options) => {
    const { dialog } = require('electron');
    return dialog.showOpenDialog(mainWindow, options);
});

// AI Chat Integration with Nvidia API (Streaming)
ipcMain.handle('chat-with-ai', async (event, messages) => {
    try {
        // Construct the system prompt for e++
        const systemPrompt = {
            role: "system",
            content: `You are the E++ IDE AI Agent (powered by Llama 3.1 405B).
Your primary role is to write correct, executable E++ code. E++ is an English-like language without braces.
Blocks are delimited by indentation and colons.
Comments start with \`#\` or \`//\`.

### KEY SYNTAX & STDLIB:
- Math/Comparisons: \`==\`, \`!=\`, \`>\`, \`<\`, \`>=\`, \`<=\`, \`+\`, \`-\`, \`*\`, \`/\`, \`and\`, \`or\`, \`not\`.
- Standard Library: \`fetch(url)\`, \`parse_json(str)\`, \`read_file\`, \`write_file\`, \`append_file\`, \`len\`, \`range\`, \`push\`, \`pop\`, \`split\`, \`join\`, \`replace\`, \`trim\`, \`type\`, \`str\`, \`int\`, \`float\`, \`random\`, \`time\`, \`sleep\`.

### STRICT GUI SYNTAX DICTIONARY:
You are ONLY allowed to use the following exact parameters for GUI keywords. Do NOT invent parameters like "background_color", "font_color", "font", "align", etc. Use ONLY the literal words shown below in brackets.

1. window: \`window "Title" width 400 height 300 [color "bg_color"] [resizable true|false]\`
2. label: \`label "text" at X Y [font_size N] [color "text_color"] [id "name"]\`
3. button: \`button "text" at X Y [width W] [height H] [on_click function_name] [color "bg_color"] [id "name"]\`
4. input: \`input "id" at X Y [width W] [placeholder "text"] [password]\`
5. image: \`image "path.png" at X Y [width W] [height H]\`
6. textbox: \`textbox "id" at X Y width W height H\`
7. checkbox: \`checkbox "id" text "label" at X Y [on_change function_name]\`
8. dropdown: \`dropdown "id" options ["A", "B"] at X Y [on_change function_name]\`

### GUI COMMANDS:
- \`set_text "id" to "value"\`
- \`value = get_text "id"\`
- \`set_color "id" to "red"\`
- \`set_visible "id" false\`
- \`alert "Message"\`
- \`show_window\`

### CRITICAL RULES:
1. E++ CANNOT BUILD PAINT APPS OR GAMES. There is NO canvas, NO draw_circle, NO get_mouse_x. If asked to build a paint app, gracefully refuse and explain E++ is for form-based GUI apps only.
2. ALWAYS output full, complete files wrapped in markdown \`\`\`epp blocks. 
Example:
\`\`\`epp
window "App" width 400 height 300 color "black"
label "Welcome" at 20 20 font_size 24 color "white"
button "Close" at 20 100 on_click close_func

func close_func():
    alert "Goodbye"
show_window
\`\`\`
DO NOT output raw code as plain text. You MUST use the markdown block, otherwise the IDE auto-apply engine will fail.`
        };

        const apiMessages = [systemPrompt, ...messages];

        const response = await net.fetch("https://integrate.api.nvidia.com/v1/chat/completions", {
            method: "POST",
            headers: {
                "Authorization": "Bearer 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",
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                model: "meta/llama-3.1-405b-instruct",
                messages: apiMessages,
                temperature: 0.2,
                top_p: 0.7,
                max_tokens: 1024,
                stream: true
            })
        });

        if (!response.ok) {
            const errBody = await response.text();
            throw new Error(`Nvidia API error: ${response.status} - ${errBody}`);
        }

        let fullContent = "";
        
        // Use an async iterator to read chunks
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');
            for (const line of lines) {
                if (line.startsWith('data: ') && line !== 'data: [DONE]') {
                    try {
                        const data = JSON.parse(line.substring(6));
                        if (data.choices && data.choices[0].delta && data.choices[0].delta.content) {
                            const text = data.choices[0].delta.content;
                            fullContent += text;
                            event.sender.send('ai-stream-chunk', text);
                        }
                    } catch (e) {
                        // ignore parse errors for partial chunks
                    }
                }
            }
        }
        
        return { success: true, reply: fullContent };
    } catch (error) {
        return { success: false, error: error.message };
    }
});