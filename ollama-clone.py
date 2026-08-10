#!/usr/bin/env python3
import os
import sys
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- WINDOWS ANSI & ENCODING FIXES ---
if sys.platform == "win32":
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    sys.stdout.reconfigure(encoding='utf-8')

# ANSI Terminal Styling Constants
CLR_G = "\033[92m"  # Green
CLR_B = "\033[94m"  # Blue
CLR_Y = "\033[93m"  # Yellow
CLR_R = "\033[91m"  # Red
CLR_C = "\033[96m"  # Cyan
CLR_N = "\033[0m"   # Reset
T_BOLD = "\033[1m"
T_DIM  = "\033[2m"

# 16 Megabyte I/O block buffer size (Optimizes both local SSD and network transfers)
STREAM_BUFFER_SIZE = 16 * 1024 * 1024  

def print_status(status_type, message, color=CLR_B):
    print(f"{T_BOLD}{color}[{status_type.upper()}]{CLR_N} {message}")

def discover_all_local_models(src_root):
    src_root = os.path.expanduser(src_root)
    manifest_base = os.path.join(src_root, "manifests", "registry.ollama.ai")
    
    if not os.path.isdir(manifest_base):
        print_status("error", f"Source manifest folder missing at {manifest_base}", CLR_R)
        return []
        
    discovered = []
    for root, dirs, files in os.walk(manifest_base):
        if files:
            rel_dir = os.path.relpath(root, manifest_base)
            parts = rel_dir.split(os.sep)
            
            if len(parts) == 2 and parts == "library":
                model_name = parts
                for version in files:
                    discovered.append((model_name, version))
            elif len(parts) == 2 and parts != "library":
                model_name = f"{parts}/{parts}"
                for version in files:
                    discovered.append((model_name, version))
                    
    return discovered

def get_manifest_paths(root_path, model, version):
    root_path = os.path.expanduser(root_path)
    base_manifest_dir = os.path.join(root_path, "manifests", "registry.ollama.ai")
    
    if "/" in model:
        rel_path = os.path.join(*model.split("/"), version)
    else:
        rel_path = os.path.join("library", model, version)
        
    return base_manifest_dir, rel_path

def extract_digests(manifest_file_path):
    if not os.path.isfile(manifest_file_path):
        print_status("error", f"Manifest missing at {T_DIM}{manifest_file_path}{CLR_N}", CLR_R)
        return None
    
    try:
        with open(manifest_file_path, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print_status("error", f"Failed to parse manifest JSON: {e}", CLR_R)
        return None
    
    digests = []
    def find_digests(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "digest":
                    digests.append(value)
                else:
                    find_digests(value)
        elif isinstance(obj, list):
            for item in obj:
                find_digests(item)
    
    find_digests(data)
    return list(set(digests))

def optimized_storage_copy(src, dst, dry_run=False):
    """Executes high-performance streaming transfer between any drive paths."""
    if os.path.exists(dst):
        if os.path.getsize(src) == os.path.getsize(dst):
            return f"{CLR_Y}Existing (Skipped){CLR_N}"
        elif dry_run:
            return f"{CLR_C}Will Overwrite (Size Mismatch){CLR_N}"
            
    if dry_run:
        return f"{CLR_G}Will Copy{CLR_N}"

    try:
        with open(src, 'rb') as fsrc:
            with open(dst, 'wb') as fdst:
                while True:
                    buf = fsrc.read(STREAM_BUFFER_SIZE)
                    if not buf:
                        break
                    fdst.write(buf)
        return f"{CLR_G}Transferred{CLR_N}"
    except OSError as e:
        return f"{CLR_R}Storage Error ({e}){CLR_N}"

def copy_blob_worker(args):
    src_file, dest_file, file_name, dry_run = args
    if not os.path.exists(src_file):
        return file_name, f"{CLR_R}Missing Source{CLR_N}"
    
    result_status = optimized_storage_copy(src_file, dest_file, dry_run)
    return file_name, result_status

def process_pipeline(src_root, dest_root, model, version, workers, dry_run=False):
    mode_tag = f" [{CLR_Y}DRY-RUN MODE{CLR_N}]" if dry_run else ""
    print_status("init", f"Targeting {T_BOLD}{model}:{version}{CLR_N}{mode_tag}")
    
    src_base_manifest, rel_manifest_path = get_manifest_paths(src_root, model, version)
    dest_base_manifest, _ = get_manifest_paths(dest_root, model, version)
    
    src_manifest_file = os.path.join(src_base_manifest, rel_manifest_path)
    dest_manifest_file = os.path.join(dest_base_manifest, rel_manifest_path)
    
    digests = extract_digests(src_manifest_file)
    if not digests:
        return False
        
    src_blobs = os.path.join(os.path.expanduser(src_root), "blobs")
    dest_blobs = os.path.join(os.path.expanduser(dest_root), "blobs")
    
    tasks = []
    for digest in digests:
        file_name = digest.replace("sha256:", "sha256-")
        tasks.append((
            os.path.join(src_blobs, file_name),
            os.path.join(dest_blobs, file_name),
            file_name,
            dry_run
        ))
        
    print_status("queue", f"Evaluating {T_BOLD}{len(tasks)}{CLR_N} blobs using {workers} parallel execution tracks...")
    
    if dry_run:
        for task in tasks:
            file_name, status = copy_blob_worker(task)
            short_hash = f"{file_name[:14]}...{file_name[-8:]}"
            print(f"  +-- {T_DIM}{short_hash:<25}{CLR_N} := [{status}]")
    else:
        os.makedirs(dest_blobs, exist_ok=True)
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(copy_blob_worker, task): task for task in tasks}
            for future in as_completed(futures):
                file_name, status = future.result()
                short_hash = f"{file_name[:14]}...{file_name[-8:]}"
                print(f"  +-- {T_DIM}{short_hash:<25}{CLR_N} := [{status}]")

    if not dry_run:
        os.makedirs(os.path.dirname(dest_manifest_file), exist_ok=True)
    
    manifest_status = optimized_storage_copy(src_manifest_file, dest_manifest_file, dry_run)
    print(f"  +-- {T_DIM}{'Manifest File':<25}{CLR_N} := [{manifest_status}]")
    
    completion_text = "Evaluated" if dry_run else "Completed"
    print_status("success", f"{completion_text}: {T_BOLD}{CLR_G}{model}:{version}{CLR_N}\n", CLR_G)
    return True

def main():
    usage_examples = f"""
Examples of Execution:
  1. Standard Sync Everything (Auto-scan source path and mirror to target destination):
     python ollama-clone.py -s C:\\Users\\Name\\.ollama\\models -d D:\\OllamaBackup

  2. Safe Test Run (Dry-Run verification of files without writing to storage):
     python ollama-clone.py -s Z:\\OllamaModels -d D:\\Ollama -n

  3. Sync Selective Custom Model Arrays with custom concurrent worker limit:
     python ollama-clone.py -s E:\\Ollama -d V:\\OllamaModels -m "qwen3.5, sam860/LFM2" -w 8
"""

    parser = argparse.ArgumentParser(
        description="🔥 Ultra-Fast Concurrent Universal Ollama Model Replicator & Batch Migrator",
        epilog=usage_examples,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("-s", "--src", default="~/.ollama/models", 
                        help="Root path folder directory containing your source Ollama models.")
    parser.add_argument("-d", "--dest", required=True, 
                        help="Target destination directory where the models will be replicated.")
    parser.add_argument("-m", "--model", 
                        help="Target model name identifier. Supports single entries or comma-separated lists. Leave blank to auto-scan and replicate ALL available models.")
    parser.add_argument("-v", "--version", default="latest", 
                        help="Target version size/tag (e.g. 8b, 2.6b, latest). (Ignored when running a full folder auto-scan).")
    parser.add_argument("-w", "--workers", type=int, default=4, 
                        help="Total allocation count of parallel file worker pipelines.")
    parser.add_argument("-n", "--dry-run", action="store_true", 
                        help="Simulates data scanning pipelines without performing physical storage modifications.")
    
    args = parser.parse_args()
    
    targets = []
    if args.model:
        input_models = [m.strip() for m in args.model.split(",")]
        for m in input_models:
            targets.append((m, args.version))
    else:
        print_status("scan", f"No model specified. Crawling {T_BOLD}{args.src}{CLR_N} for targets...")
        targets = discover_all_local_models(args.src)
        if not targets:
            print_status("error", "No local models discovered in source directory.", CLR_R)
            sys.exit(1)
        print_status("scan", f"Discovered {T_BOLD}{len(targets)}{CLR_N} total unique model versions.\n", CLR_G)

    if args.dry_run:
        print(f"{T_BOLD}{CLR_Y}== DRY-RUN ENABLED: Operational pipelines are simulated only =={CLR_N}\n")

    successful_runs = 0
    for idx, (model, version) in enumerate(targets, 1):
        print(f"{T_BOLD}{CLR_Y}[JOB {idx}/{len(targets)}]{CLR_N} Preparing pipeline step...")
        if process_pipeline(args.src, args.dest, model, version, args.workers, args.dry_run):
            successful_runs += 1
            
    summary_text = "simulated" if args.dry_run else "synchronized"
    print_status("done", f"All jobs processed. Successfully {summary_text} {successful_runs}/{len(targets)} models.", CLR_G)

if __name__ == "__main__":
    main()
