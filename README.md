# 🔥 Ultra-Fast Concurrent Universal Ollama Model Replicator & Bulk Migrator

A blazing-fast, dependency-free Python CLI utility designed to seamlessly back up, replicate, or migrate [Ollama](https://ollama.com) models across different storage paths. Whether you are transferring gigabytes of weights between local NVMe SSDs, external USB drives, or local network shares (NAS/SMB), this script automates the process with zero friction.

---

## 🚀 Key Features

*   **⚡ High-Performance Parallel Streaming Engine**: Utilizes multi-threaded asynchronous workers (`ThreadPoolExecutor`) and a massive, custom system-level I/O block buffer allocation ($16\text{MB}$) to maximize drive bus saturation and network cards bandwidth.
*   **📂 Multi-Model Automation & Auto-Scanning**: Leave the model option blank to automatically crawl and scan your entire source manifest registry directory. It automatically structures, detects, and batches **all** available official models and custom user-namespace configurations (`user/model:tag`).
*   **🎯 Smart Deduplication-Aware Synchronization**: It perfectly honors Ollama's inner content-addressable storage layer architectures. If a target blob layer payload already matches by byte-size size parameters exactly on the destination, it instantly skips it to avoid redundant transfers.
*   **🛡️ Non-Destructive Dry-Run Mode**: Validate data pipelines, parse complex nested manifests, and evaluate storage deltas cleanly without executing mutations or writing a single byte to disk.
*   **🎨 Cross-Platform Formatted Interface**: Built-in automated Windows kernel hook layers to safely render ANSI colors, alongside clean universal ASCII layouts perfectly formatted for PowerShell, Command Prompt, and Bash shells.

---

## 📦 Requirements

*   **Python**: Version `3.6` or higher.
*   **Dependencies**: `0` (Zero external packages needed. Runs entirely on standard Python system frameworks).

---

## 🛠️ Usage Syntax

```bash
python ollama-clone.py -d <destination_path> [options]
```

### Options Configuration Matrix

| Flag | Full Identifier | Default Fallback | Functional Description |
| :--- | :--- | :--- | :--- |
| `-h` | `--help` | *N/A* | Prints out the system self-documenting interface manual and use cases. |
| `-s` | `--src` | `~/.ollama/models` | The absolute path directory pointing to your active source Ollama installation. |
| `-d` | `--dest` | *[REQUIRED]* | The target destination directory where the model system environment will mirror. |
| `-m` | `--model` | *None (Auto)* | Specific model name or comma-separated listing array string. Leave blank to auto-scan **all**. |
| `-v` | `--version` | `latest` | Tag variant size descriptor. *(Automatically bypassed when doing full folder folder auto-scans)*. |
| `-w` | `--workers` | `4` | Total explicit number of parallel worker pipelines allocated to stream files concurrently. |
| `-n` | `--dry-run` | *False* | Simulates directory paths, extracts manifests, and prints state maps without transferring files. |

---

## 🏎️ Execution Examples

### 1. Auto-Scan & Synchronize All Models
Automatically crawls through your custom source directory (`Z:\OllamaModels`), identifies all active configurations, and mirrors them into your active boot volume path (`D:\Ollama`):
```powershell
python ollama-clone.py -s Z:\OllamaModels -d D:\Ollama\ollama
```

### 2. Verify Deployments with a Safe Dry-Run
Preview which layer digests exist, what files will be copied, and track size mismatches without transferring bytes:
```powershell
python ollama-clone.py -s Z:\OllamaModels -d D:\Ollama\ollama --dry-run
```

### 3. Move a Specific List of Models with High Concurrency
Explicitly target an array containing a mixture of library models and custom usernames, cranking up the engine to use 8 background tracks:
```powershell
python ollama-clone.py -s E:\Ollama -d V:\OllamaModels -m "qwen3.5, sam860/LFM2" -w 8
```

---

## 💡 Why this script is necessary

Ollama handles storage differently than simple, flat model file managers. Instead of pointing directly to single standalone `.gguf` weights, it stores files as an open-container architecture using split **manifest layer blueprints** and **hashed binary data blobs**. 

Manually tracking down which raw hashes correspond to which model layers inside the `manifests/registry.ollama.ai` tree is slow and prone to errors. This tool instantly stitche those structures together, maps their deep dependency values, and safely packages them for replication anywhere on your machine or local infrastructure.

---

## 📄 License
Distributed entirely under the **MIT License**. Feel free to modify, optimize, or integrate it into any local system engineering setup.
