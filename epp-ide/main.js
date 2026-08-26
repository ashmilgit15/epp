const { app, BrowserWindow, ipcMain, net } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

let mainWindow;
let runningProcess = null;

function findBundledBinary() {
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
        try {
            fs.accessSync(p, fs.constants.X_OK);
            return p;
        } catch (e) {
            // keep looking
        }
    }
    return null;
}

// Resolve how to run .epp files:
//   1. A bundled native binary (PyInstaller dist/epp)
//   2. The interpreter package next to this app (python3 -m interpreter.epp)
function resolveRunner() {
    const binary = findBundledBinary();
    if (binary) {
        return { command: binary, args: [] };
    }
    const pkgDir = path.join(__dirname, '..', 'interpreter');
    if (fs.existsSync(path.join(pkgDir, 'epp.py'))) {
        return { command: 'python3', args: ['-m', 'interpreter.epp'], cwd: path.dirname(pkgDir) };
    }
    if (process.platform === 'win32') {
        return { command: 'py', args: ['-3', '-m', 'interpreter.epp'], cwd: path.dirname(pkgDir) };
    }
    return { command: 'python3', args: ['-m', 'interpreter.epp'], cwd: null };
}

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

ipcMain.handle('check-epp', async (event, filePath) => {
    return new Promise((resolve) => {
        const runner = resolveRunner();
        const child = spawn(runner.command,
            [...(runner.args || []), '--check', filePath, '--json'],
            { cwd: runner.cwd || path.dirname(filePath) });

        let out = '';
        let err = '';
        const timeout = setTimeout(() => {
            child.kill();
            resolve({ success: false, error: 'Check timed out' });
        }, 10000);

        child.stdout.on('data', (d) => { out += d.toString(); });
        child.stderr.on('data', (d) => { err += d.toString(); });
        child.on('close', () => {
            clearTimeout(timeout);
            try {
                // The interpreter may print unrelated warnings; find the JSON line
                const jsonLine = out.split('\n').reverse().find(l => l.trim().startsWith('{'));
                if (!jsonLine) throw new Error(err || 'No output from checker');
                resolve({ success: true, result: JSON.parse(jsonLine) });
            } catch (e) {
                resolve({ success: false, error: e.message });
            }
        });
        child.on('error', (err2) => {
            clearTimeout(timeout);
            resolve({ success: false, error: err2.message });
        });
    });
});

ipcMain.handle('run-epp', async (event, filePath) => {
    return new Promise((resolve) => {
        const output = [];

        if (runningProcess) {
            runningProcess.kill();
            runningProcess = null;
        }

        const runner = resolveRunner();
        runningProcess = spawn(runner.command, [...(runner.args || []), filePath], {
            cwd: runner.cwd || path.dirname(filePath),
            env: { ...process.env, PYTHONUNBUFFERED: '1' }
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

// AI Chat Integration (Streaming) — any OpenAI-compatible endpoint.
//
// Configuration (env vars or a config.json next to this file):
//   EPP_AI_BASE_URL  default: https://ai.hackclub.com/proxy/v1 (Hack Club AI)
//   EPP_AI_API_KEY   your provider API key (NEVER commit this!)
//   EPP_AI_MODEL     default: google/gemini-3.7-flash
function getAiConfig() {
    let fileConfig = {};
    try {
        const cfgPath = path.join(__dirname, 'config.json');
        if (fs.existsSync(cfgPath)) {
            fileConfig = JSON.parse(fs.readFileSync(cfgPath, 'utf-8'));
        }
    } catch (e) {
        console.error('Could not read config.json:', e.message);
    }
    return {
        baseUrl: process.env.EPP_AI_BASE_URL || fileConfig.baseUrl
            || 'https://ai.hackclub.com/proxy/v1',
        apiKey: process.env.EPP_AI_API_KEY || fileConfig.apiKey || '',
        model: process.env.EPP_AI_MODEL || fileConfig.model
            || 'google/gemini-3.7-flash'
    };
}

let activeAiRequest = null;  // AbortController for the in-flight completion

ipcMain.handle('stop-ai', async () => {
    if (activeAiRequest) {
        activeAiRequest.abort();
        activeAiRequest = null;
        return { success: true };
    }
    return { success: false, error: 'No AI request running' };
});

ipcMain.handle('get-ai-status', async () => {
    const cfg = getAiConfig();
    return { configured: Boolean(cfg.apiKey), baseUrl: cfg.baseUrl, model: cfg.model };
});

ipcMain.handle('chat-with-ai', async (event, messages, editorContext) => {
    try {
        // Construct the system prompt for e++
        const systemPrompt = {
            role: "system",
            content: `You are the E++ IDE AI Agent. Your primary role is to write correct, executable E++ code.
E++ is an English-like language without braces. Blocks are delimited by indentation (4 spaces) and colons.
Comments start with \`#\` or \`//\`.

### CORE SYNTAX:
- Variables: \`x = 10\`, \`name = "Alice"\` (compound: \`+=\`, \`-=\`, \`*=\`, \`/=\`)
- Say: \`say "Hello"\` or \`say("Hello")\`
- String interpolation: \`say "Hello {name}, {age + 1} years"\`
- Input: \`name = input("Your name? ")\`
- Comparisons: \`is\`, \`is not\`, \`is equal to\`, \`is not equal to\`, \`is greater than\`, \`is less than\`, \`>=\`, \`<=\`, \`==\`, \`!=\`
- Math: \`+\`, \`-\`, \`*\`, \`/\`, \`%\` (modulo), \`^\` (power), \`and\`, \`or\`, \`not\`
- Conditionals: if/elif/else with colons and indentation
- Loops: \`for i in range(10):\`, \`while x < 10:\`, \`repeat 5 times:\` plus \`break\` / \`continue\`
- Switch:
\`\`\`epp
switch day:
    case "Sat", "Sun":
        say "weekend"
    default:
        say "weekday"
\`\`\`
- Functions: \`func add(a, b): return a + b\`
- Classes: \`class Dog:\` with \`func init(name):\` using \`self.name = name\`; methods can take arguments
- Lists & dicts with indexing from 0 and negative indexing: \`items[0]\`, \`items[-1]\`, \`user["name"]\`, \`matrix[1][2]\`
- Error handling: \`try:\` ... \`catch err:\` ...
- Imports: \`import "utils.epp"\`

### STDLIB:
\`len\`, \`range\`, \`push\`, \`pop\`, \`keys\`, \`values\`, \`contains\`, \`index_of\`, \`sort\`, \`reversed\`, \`sum\`, \`slice\`,
\`split\`, \`join\`, \`trim\`, \`replace\`, \`upper\`, \`lower\`, \`type\`, \`str\`, \`int\`, \`float\`, \`bool\`,
\`abs\`, \`round\`, \`floor\`, \`ceil\`, \`pow\`, \`sqrt\`, \`min\`, \`max\`, \`random\`, \`random_int(a, b)\`, \`shuffle\`,
\`time\`, \`clock\`, \`sleep\`, \`read_file\`, \`write_file\`, \`append_file\`, \`exists\`, \`delete_file\`,
\`fetch(url)\`, \`fetch_json(url)\`, \`parse_json(str)\`, \`to_json(obj)\`

### GUI SYNTAX (desktop apps):
1. window: \`window "Title" width 400 height 300 [color "bg"] [resizable true] [id "win"]\`
2. label: \`label "text" at X Y [font_size N] [color "c"] [id "name"]\`
3. button: \`button "text" at X Y [width W] [height H] [on_click func] [color "c"] [id "name"]\`
4. input: \`input "id" at X Y [width W] [placeholder "text"] [password]\`
5. image: \`image "path.png" at X Y [width W] [height H]\`
6. textbox: \`textbox "id" at X Y width W height H\`
7. checkbox: \`checkbox "id" text "label" at X Y [on_change func]\`
8. dropdown: \`dropdown "id" options ["A", "B"] at X Y [on_change func]\`
9. slider: \`slider "id" from 0 to 100 at X Y [on_change func]\`
10. progress: \`progress "id" at X Y width W\` + \`set_progress "id" to 50\`

### CANVAS & ANIMATION (great for games/drawings):
- \`canvas "cv" width 400 height 300 color "white"\`
- \`draw line on "cv" from X1 Y1 to X2 Y2 [color "red"] [width 2]\`
- \`draw rectangle on "cv" from X1 Y1 to X2 Y2 [color "c"] [fill "c"]\`
- \`draw circle on "cv" at CX CY size R [color "c"] [fill "c"]\`
- \`draw dot on "cv" at X Y [color "c"]\`
- \`draw text on "cv" at X Y text "hi" [color "c"]\`
- \`clear_canvas "cv"\`
- Animation loop: \`every 50 milliseconds call tick\` (repeating) or \`after 2000 milliseconds call boom\` (once)

### GUI COMMANDS:
- \`set_text "id" to value\` · \`value = get_text "id"\` · \`set_color "id" to "red"\`
- \`set_visible "id" false\` · \`alert "msg"\` · \`show_window\` · \`beep\` or \`beep 880 150\`

### TESTING (built into the language):
\`\`\`epp
test "addition":
    expect add(2, 2) to_be 4
    expect 1 / 0 to_throw
\`\`\`
Matchers: \`to_be\`, \`to_be_true\`, \`to_be_false\`, \`to_throw\`.

### KEYBOARD:
\`window ... on_key handle\` — handler receives the key name (\`"Left"\`, \`"Right"\`, \`"Up"\`, \`"Down"\`, \`"a"\`, \`"space"\`...). Also available on canvas, input, textbox and button.

### CRITICAL RULES:
1. ALWAYS output full, complete files wrapped in markdown \`\`\`epp blocks.
Example:
\`\`\`epp
window "App" width 400 height 300 color "black"
label "Welcome" at 20 20 font_size 24 color "white"
button "Close" at 20 100 on_click close_func

func close_func():
    alert "Goodbye"
show_window
\`\`\`
DO NOT output raw code as plain text — use markdown blocks so the IDE auto-apply works.
2. GUI callbacks are functions defined with \`func name():\` and referenced by NAME only (no quotes, no parentheses) in on_click/on_change.
3. Every program that opens widgets should end with \`show_window\`.
4. Prefer string interpolation \`"{x}"\` over concatenation for readability.`
        };

        const cfg = getAiConfig();
        if (!cfg.apiKey) {
            return {
                success: false,
                error: 'No AI API key configured. Set the EPP_AI_API_KEY environment variable '
                    + 'or create epp-ide/config.json with {"apiKey": "...", "baseUrl": "...", "model": "..."}. '
                    + 'Any OpenAI-compatible provider works. '
                    + 'For Hack Club AI, use https://ai.hackclub.com/proxy/v1 with your sk-hc-... key.'
            };
        }

        // Keep history bounded; inject editor context as a preceding user message
        const trimmedHistory = Array.isArray(messages) ? messages.slice(-12) : [];
        const contextMessages = [];
        if (typeof editorContext === 'string' && editorContext.trim().length > 0) {
            const clipped = editorContext.slice(0, 6000);
            contextMessages.push({
                role: "user",
                content: `Current editor content (for context — don't repeat unless asked to edit it):\n\`\`\`epp\n${clipped}\n\`\`\``
            });
        }
        const apiMessages = [systemPrompt, ...contextMessages, ...trimmedHistory];

        activeAiRequest = new AbortController();

        const response = await net.fetch(cfg.baseUrl.replace(/\/$/, '') + "/chat/completions", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${cfg.apiKey}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                model: cfg.model,
                messages: apiMessages,
                temperature: 0.2,
                top_p: 0.7,
                max_tokens: 2048,
                stream: true
            }),
            signal: activeAiRequest.signal
        });

        if (!response.ok) {
            const errBody = await response.text();
            activeAiRequest = null;
            throw new Error(`AI API error ${response.status}: ${errBody.slice(0, 400)}`);
        }

        let fullContent = "";
        let sseBuffer = "";

        // Use an async iterator to read chunks
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        try {
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                sseBuffer += decoder.decode(value, { stream: true });
                const lines = sseBuffer.split('\n');
                sseBuffer = lines.pop();  // keep the (possibly) partial last line
                for (const line of lines) {
                    const trimmed = line.trim();
                    if (trimmed.startsWith('data: ') && trimmed !== 'data: [DONE]') {
                        try {
                            const data = JSON.parse(trimmed.substring(6));
                            if (data.choices && data.choices[0] && data.choices[0].delta
                                    && data.choices[0].delta.content) {
                                const text = data.choices[0].delta.content;
                                fullContent += text;
                                event.sender.send('ai-stream-chunk', text);
                            }
                        } catch (e) {
                            // ignore malformed events
                        }
                    }
                }
            }
        } catch (readError) {
            // Aborted via stop-ai → return what we have so far
            if (readError.name === 'AbortError' || (activeAiRequest && activeAiRequest.signal.aborted)) {
                activeAiRequest = null;
                return { success: true, reply: fullContent, aborted: true };
            }
            throw readError;
        }
        activeAiRequest = null;
        
        return { success: true, reply: fullContent };
    } catch (error) {
        activeAiRequest = null;
        if (error.name === 'AbortError') {
            return { success: false, error: 'aborted' };
        }
        return { success: false, error: error.message };
    }
});