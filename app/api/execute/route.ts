import { NextRequest, NextResponse } from "next/server";
import { PythonExecutor } from "@/lib/python-executor";
import * as path from "path";

const pythonExecutor = new PythonExecutor({
  timeout: 60000 * 5, // 60 seconds * X timeout
  workingDirectory: "py-eval-tool",
});

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { job, params } = body;

    if (!job) {
      return NextResponse.json(
        { error: "Missing job type", success: false },
        { status: 400 }
      );
    }

    // Handle `scrap` job
    if (job === "scrap") {
      const { source, workId, episodes } = params;

      if (!source || !workId) {
        return NextResponse.json(
          { error: "source and workId are required", success: false },
          { status: 400 }
        );
      }

      const scriptPath = path.join(process.cwd(), "py-eval-tool", "scrap.py");
      const _params = [source, workId, episodes];
      const result = await pythonExecutor.execute(scriptPath, _params);
      return NextResponse.json(result);
    }

    // Handle `eval` job
    if (job === "eval") {
      const { agent, workId } = params;

      if (!agent || !workId) {
        return NextResponse.json(
          { error: "agent, source and workId are required", success: false },
          { status: 400 }
        );
      }

      const scriptPath = path.join(process.cwd(), "py-eval-tool", "evaluation.py");
      const _params = [agent, workId, 1];
      const result = await pythonExecutor.execute(scriptPath, _params);

      return NextResponse.json(result);
    }

    // Unknown job
    return NextResponse.json(
      { error: "Unknown job", success: false },
      { status: 400 }
    );
  } catch (error: any) {
    console.error("Python execution error:", error);

    if (error.result) {
      const { stdout, stderr, exitCode, scriptPath, params, executionTime } =
        error.result;

      return NextResponse.json(
        {
          success: false,
          error: "Python script execution failed",
          data: { stdout, stderr, exitCode, scriptPath, params, executionTime },
        },
        { status: 422 }
      );
    }

    // Generic error handler
    return NextResponse.json(
      {
        error: "Internal server error",
        success: false,
        details: error.message,
      },
      { status: 500 }
    );
  }
}

// Handle unsupported methods
export async function GET() {
  return NextResponse.json(
    {
      error: "Method not allowed. Use POST to execute Python scripts.",
      success: false,
    },
    { status: 405 }
  );
}
