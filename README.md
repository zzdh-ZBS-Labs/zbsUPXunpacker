# UPXunpack - Automated UPX Unpacker

UPXunpack is a command-line utility that automates unpacking of UPX-compressed executables. It wraps the official UPX tool with additional checks, hash verification, directory recursion, and batch processing to make unpacking more convenient and safer for malware analysis, reverse engineering, and incident response workflows.

---

## Features

- Automatically locates the UPX executable in `PATH` or common installation directories (both Linux and Windows).
- Detects UPX-packed files by scanning the first 4KB of the file for common UPX signatures (e.g., `UPX!`, `UPX0`, `UPX1`, `UPX2`).
- Unpacks single files, entire directories, or a list of files using a consistent interface.
- Supports recursive directory walking with extension filtering (default: `.exe`, `.dll`, `.sys`, `.bin`).
- Computes SHA-256 hashes of original and unpacked binaries for basic change verification.
- Provides a `--force` mode to unpack files even when no UPX signature is detected.
- Verbose mode for detailed logging of UPX commands and unpacking results.
- Clean error handling and timeouts for stuck or long-running UPX processes.

---

## Requirements

- Python 3.8 or newer
- UPX installed and accessible:
  - Either in the system `PATH`
  - Or at a known path passed via `--upx-path`

Python standard library modules used:
- `os`
- `sys`
- `subprocess`
- `shutil`
- `pathlib`
- `hashlib`
- `argparse`

No third-party Python packages are required.

---

## Installation

1. Clone the repository:

       git clone https://github.com/zzdh-ZBS-Labs/zbsUPXunpacker.git
       cd UPXunpack

2. Ensure UPX is installed:

   - Download from: https://upx.github.io/
   - Place `upx` / `upx.exe` in your `PATH` or in a known directory.

3. (Optional) Make the script executable on Unix-like systems:

       chmod +x UPXunpack.py

You can then run it via:

    ./UPXunpack.py
or

    python UPXunpack.py

---

## Usage

The tool supports both single-file and directory-based unpacking.

### Basic syntax

    python UPXunpack.py [options] <input>

Where `<input>` can be:
- A single file (default mode).
- A directory (when combined with `-d` / `--directory`).

### Command-line options

- `input`  
  Required positional argument. File or directory to process.

- `-o, --output`  
  Output file name for single-file mode.  
  If omitted, the script creates `<name>_unpacked<ext>` next to the original.

- `-d, --directory`  
  Treat `input` as a directory and process all matching files.

- `-r, --recursive`  
  Recursively process subdirectories in directory mode.

- `-f, --force`  
  Force unpacking even if a UPX signature is not detected in the file.

- `-v, --verbose`  
  Enable verbose output (prints UPX commands, extra debug info).

- `--upx-path PATH`  
  Explicit path to the UPX executable (overrides auto-detection).

- `--extensions EXT_LIST`  
  Comma-separated list of file extensions to process in directory mode.  
  Default: `.exe,.dll,.sys,.bin`

---

## Examples

### Single file

1. Standard unpack of a UPX-packed file:

       python UPXunpack.py sample_packed.exe

2. Unpack to a specific output file:

       python UPXunpack.py sample_packed.exe -o sample_unpacked.exe

3. Force unpack even if no UPX signature is detected:

       python UPXunpack.py suspicious.bin --force

4. Verbose mode to see underlying UPX command and output:

       python UPXunpack.py sample_packed.exe -v

### Directory mode

1. Unpack all default extensions in a directory:

       python UPXunpack.py ./samples -d

2. Recursively unpack across subdirectories:

       python UPXunpack.py ./samples -d -r

3. Restrict to specific extensions:

       python UPXunpack.py ./samples -d -r --extensions .exe,.dll

4. Use a custom UPX path:

       python UPXunpack.py ./samples -d --upx-path "C:\Tools\UPX\upx.exe"

---

## How It Works

- `UPXUnpacker.find_upx()`  
  - Checks `shutil.which("upx")` first.  
  - Falls back to several common installation paths on Linux and Windows.  
  - Returns `None` if UPX is not found.

- `UPXUnpacker.is_upx_packed(file_path)`  
  - Reads the first 4096 bytes of the file.  
  - Searches for known UPX markers such as `b"UPX!"`, `b"UPX0"`, `b"UPX1"`, `b"UPX2"`, `b"$Id: UPX"`, etc.  
  - Returns `True` if any signature is present, otherwise `False`.

- `UPXUnpacker.get_file_hash(file_path)`  
  - Computes the SHA-256 hash of the file in chunks.  
  - Used to verify that unpacking actually changed the file contents.

- `UPXUnpacker.unpack_file(input_file, output_file=None, force=False)`  
  - Validates UPX availability and file existence.  
  - Optionally checks for UPX signatures unless `force` is set.  
  - Copies the original file to an output path and runs `upx -d` on it.  
  - On success, compares original and unpacked hashes to ensure the file changed.  
  - Returns `(success: bool, message: str)`.

- `UPXUnpacker.unpack_directory(directory, recursive=False, extensions=None)`  
  - Walks through a directory, optionally recursively.  
  - Filters files by extension list.  
  - Calls `unpack_file()` for each matching file and aggregates results.

- `UPXUnpacker.batch_unpack(file_list)`  
  - Accepts an iterable of file paths.  
  - Unpacks each file and returns a list of result dictionaries.

- `main()`  
  - Parses command-line arguments.  
  - Initializes `UPXUnpacker` and sets verbosity / UPX path.  
  - Dispatches to either single-file or directory-processing mode.  
  - Prints a summary of successes/failures for directory mode.

---

## Exit Codes

- `0` – Single-file unpack succeeded.  
- `1` – Error conditions such as:
  - UPX executable not found.
  - Input file or directory does not exist.
  - Unpacking failure or timeout.
  - Non-UPX file without `--force` (treated as failure).

---

## Use Cases

- Malware analysis: Quickly unpack UPX-protected samples before static or dynamic analysis.
- Reverse engineering: Automate stripping UPX layers from binaries before loading into IDA/Ghidra.
- Incident response: Batch-process large collections of binaries collected from endpoints or sandboxes.

---

## Disclaimer

Use this tool responsibly and only on files you have the legal right to analyze. Bypassing protections on software you do not own or have permission to examine may violate licenses, terms of service, or local laws. The author assumes no liability for misuse.
