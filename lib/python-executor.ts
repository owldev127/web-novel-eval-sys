import { spawn, ChildProcess } from "child_process";
import * as path from "path";
import * as fs from "fs";
import os from "os";

export interface ExecutionResult {
  stdout: string;
  stderr: string;
  exitCode: number | null;
  success: boolean;
  scriptPath: string;
  params: string[];
  executionTime: number;
  data?: any;
}

export interface ExecutionOptions {
  timeout?: number;
  workingDirectory?: string;
}

export class PythonExecutor {
  private pythonCommand: string;
  private defaultTimeout: number;
  private workingDirectory: string;

  constructor(options: ExecutionOptions = {}) {
    const isWindows = os.platform() === "win32";
    this.pythonCommand = path.resolve(
      process.cwd(),
      "py-eval-tool",
      "venv",
      isWindows ? "Scripts" : "bin",
      isWindows ? "python.exe" : "python3"
    );
    this.defaultTimeout = options.timeout || 30000; // 30 seconds
    this.workingDirectory = options.workingDirectory || process.cwd();
  }

  async execute(
    scriptPath: string,
    params: string[] = [],
    options: ExecutionOptions = {}
  ): Promise<string> {
    const {
      timeout = this.defaultTimeout,
      workingDirectory = this.workingDirectory,
    } = options;

    return new Promise((resolve, reject) => {
      const fullScriptPath = path.resolve(workingDirectory, scriptPath);
      if (!fs.existsSync(fullScriptPath)) {
        reject(new Error(`Python script not found: ${fullScriptPath}`));
        return;
      }

      const python: ChildProcess = spawn(
        this.pythonCommand,
        ['-u', fullScriptPath, ...params],
        {
          cwd: workingDirectory,
        }
      );

      let stdout = "";
      let stderr = "";
      let isCompleted = false;
      const startTime = Date.now();

      const timeoutId = setTimeout(() => {
        if (!isCompleted) {
          isCompleted = true;
          python.kill("SIGTERM");
          reject(
            new Error(`Python script execution timed out after ${timeout}ms`)
          );
        }
      }, timeout);

      python.stdout?.on("data", (data: Buffer) => {
        const output = data.toString()
        stdout += output;
        console.log(`[PYTHON]: ${output.trim()}`);
      });

      python.stderr?.on("data", (data: Buffer) => {
        const error = data.toString();
        stderr += error;
        console.error(`[PYTHON ERROR]: ${error.trim()}`);
      });

      python.on("close", (code: number | null) => {
        if (isCompleted) return;
        isCompleted = true;
        clearTimeout(timeoutId);
        
        if (code !== 0) {
          reject(
            new Error(
              `Python script exited with code ${code}\nError:\n${stderr}`
            )
          );
          return;
        }

        // ✅ Extract JSON block between markers if present
        const match = stdout.match(/###JSON-BEGIN###([\s\S]*?)###JSON-END###/);
        if (match) {
          try {
            const parsed = JSON.parse(match[1].trim());
            resolve(parsed); // return JSON directly
          } catch (err) {
            reject(
              new Error(
                `Failed to parse Python JSON output.\nExtracted:\n${match[1]}\nError:\n${err}`
              )
            );
          }
        } else {
          // If no JSON markers, return raw output
          reject(
            new Error(`No JSON ouput returned`)
          );
        }
      });

      python.on("error", (error: Error) => {
        if (isCompleted) return;
        isCompleted = true;
        clearTimeout(timeoutId);
        reject(new Error(`Failed to start Python process: ${error.message}`));
      });
    });
  }
}
