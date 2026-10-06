using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text;

class LibreOfficeCliCompatibility {
    const string OriginalUri = "vnd.sun.star.script:Standard.Module1.RecalculateAndSave?language=Basic&location=application";
    const string CompatibilityUri = "macro:///Standard.Module1.RecalculateAndSave";
    // Windows CreateProcess quoting, including arguments containing spaces or quotes.
    static string Quote(string value) {
        var result = new StringBuilder("\"");
        int backslashes = 0;
        foreach (char c in value) {
            if (c == '\\') { backslashes++; continue; }
            if (c == '"') {
                result.Append('\\', backslashes * 2 + 1); result.Append(c); backslashes = 0;
            } else {
                result.Append('\\', backslashes); result.Append(c); backslashes = 0;
            }
        }
        result.Append('\\', backslashes * 2); result.Append('"');
        return result.ToString();
    }
    static int Main(string[] args) {
        string official = Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory,
            "..", "libreoffice_runtime", "program", "soffice.com"));
        if (!File.Exists(official)) { Console.Error.WriteLine("Project official soffice.com missing"); return 126; }
        var outgoing = new List<string>();
        bool macro = false;
        foreach (string arg in args) {
            if (arg == OriginalUri) { macro = true; continue; }
            outgoing.Add(arg);
        }
        // Document loading is listed before invoking the same global application macro.
        if (macro) outgoing.Add(CompatibilityUri);
        var quoted = new List<string>();
        foreach (string arg in outgoing) quoted.Add(Quote(arg));
        var start = new ProcessStartInfo(official, string.Join(" ", quoted.ToArray()));
        start.UseShellExecute = false;
        start.CreateNoWindow = true;
        using (Process child = Process.Start(start)) {
            if (!child.WaitForExit(80000)) {
                var stop = new ProcessStartInfo("C:\\WINDOWS\\system32\\taskkill.exe",
                    "/PID " + child.Id + " /T /F");
                stop.UseShellExecute = false; stop.CreateNoWindow = true;
                using (Process ownedStop = Process.Start(stop)) ownedStop.WaitForExit(10000);
                Console.Error.WriteLine("Project soffice.com child exceeded 80-second compatibility bound");
                return 124;
            }
            return child.ExitCode;
        }
    }
}
