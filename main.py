import os
import re
import json

def is_external_module(path):
    return not path.startswith((".", "/", "@/", "~/"))

import_regex = re.compile(r'^\s*import\s+(?:[^"\']+from\s+)?[\'"]([^\'"]+)[\'"]', re.MULTILINE)
require_regex = re.compile(r'^\s*const\s+\w+\s*=\s*require\([\'"]([^\'"]+)[\'"]\)', re.MULTILINE)
extensions = (".js", ".ts", ".jsx", ".tsx")

def scan_imports(directory):
    found_modules = set()

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(extensions):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                        imports = import_regex.findall(content) + require_regex.findall(content)
                        for imp in imports:
                            if is_external_module(imp):
                                base = imp.split("/")[0]
                                if base.startswith("@") and "/" in imp:
                                    base = "/".join(imp.split("/")[:2])
                                found_modules.add(base)
                except Exception as e:
                    print(f"warning {path} scan failed: {e}")

    return sorted(found_modules)

def generate_package_json(modules):
    package_json = {
        "name": "recover-json",
        "version": "1.0.0",
        "dependencies": {name: "*" for name in modules}
    }
    with open("package.json", "w", encoding="utf-8") as f:
        json.dump(package_json, f, indent=2)
    print("package.json generated")

if __name__ == "__main__":
    src_path = "./"
    if not os.path.exists(src_path):
        print("no dir")
        exit(1)

    modules = scan_imports(src_path)
    print(f"found modules: {modules}")
    generate_package_json(modules)
