import re
import os
import json

node_core_modules = {
    "assert", "buffer", "child_process", "cluster", "console", "constants", "crypto",
    "dgram", "dns", "domain", "events", "fs", "http", "http2", "https", "inspector",
    "module", "net", "os", "path", "perf_hooks", "process", "punycode", "querystring",
    "readline", "repl", "stream", "string_decoder", "timers", "tls", "trace_events",
    "tty", "url", "util", "v8", "vm", "worker_threads", "zlib"
}

def is_valid_npm_package(name):
    if not isinstance(name, str):
        return False
    if name in node_core_modules:
        return False
    if name in {".", "..", "..."}:
        return False
    if name.startswith(("node:", "./", "../", "/", "#", "file:", "data:", "http")):
        return False
    if name.startswith("var_") or "${" in name or name == "":
        return False
    if name.startswith("private-"):
        return False
    npm_name_pattern = re.compile(
        r'^(?:@[\w-]+\/)?[a-z0-9._-]+$'
    )
    if not npm_name_pattern.match(name):
        return False
    return True

def extract_modules_from_code(code):
    imports = re.findall(r"import\s+(?:[^'\"]+)\s+from\s+['\"]([^'\"]+)['\"]", code)
    side_effect_imports = re.findall(r"import\s+['\"]([^'\"]+)['\"]", code)
    requires = re.findall(r"require\(['\"]([^'\"]+)['\"]\)", code)
    return imports + side_effect_imports + requires

def scan_directory_for_modules(directory):
    all_modules = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(('.js', '.ts', '.tsx')):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        code = f.read()
                        mods = extract_modules_from_code(code)
                        all_modules.extend(mods)
                except Exception as e:
                    print(f"⚠️ failed to read {path}: {e}")
    return all_modules

def get_scripts(project_type):
    common = {
        "lint": "next lint",
        "typecheck": "tsc --noEmit"
    }
    if project_type == "next-ts":
        return {
            **common,
            "dev": "next dev --turbopack -p 9002",
            "build": "next build",
            "start": "next start"
        }
    elif project_type == "node":
        return {
            "start": "node index.js"
        }
    elif project_type == "expo":
        return {
            "start": "expo start",
            "android": "expo start --android",
            "ios": "expo start --ios"
        }
    else:
        return {"start": "node index.js"}

if __name__ == "__main__":
    main_dir = "./"
    project_type = "next-ts"

    found_modules = scan_directory_for_modules(main_dir)
    valid_modules = sorted(set(m for m in found_modules if is_valid_npm_package(m)))
    print(f"📦 valid modules: {valid_modules}")

    package_json = {
        "name": "auto-generated",
        "version": "1.0.0",
        "private": True,
        "type": "module" if project_type != "node" else "commonjs",
        "scripts": get_scripts(project_type),
        "dependencies": {mod: "*" for mod in valid_modules}
    }

    with open("package.json", "w", encoding="utf-8") as f:
        json.dump(package_json, f, indent=2, ensure_ascii=False)
    print("✅ package.json generated successfully")
