#!/usr/bin/env python3
"""
UPX Unpacker Script
Automated tool for unpacking UPX-compressed executables
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import hashlib

class UPXUnpacker:
    def __init__(self):
        self.upx_path = self.find_upx()
        self.verbose = False

    def find_upx(self):
        """Find UPX executable in system PATH or common locations"""
        # Check if upx is in PATH
        if shutil.which('upx'):
            return 'upx'

        # Common UPX installation paths
        common_paths = [
            '/usr/bin/upx',
            '/usr/local/bin/upx',
            'C:\\Program Files\\UPX\\upx.exe',
            'C:\\Program Files (x86)\\UPX\\upx.exe',
            './upx',
            './upx.exe'
        ]

        for path in common_paths:
            if os.path.exists(path):
                return path

        return None

    def is_upx_packed(self, file_path):
        """Check if a file is UPX-packed by examining headers"""
        try:
            with open(file_path, 'rb') as f:
                data = f.read(4096)  # Read first 4KB

                # Check for UPX signatures
                upx_signatures = [
                    b'UPX!',
                    b'UPX0',
                    b'UPX1',
                    b'UPX2',
                    b'UPX ',
                    b'$Id: UPX',
                    b'\x55\x50\x58\x21'  # UPX! in hex
                ]

                for sig in upx_signatures:
                    if sig in data:
                        return True

                return False
        except Exception as e:
            print(f"Error checking UPX signature: {e}")
            return False

    def get_file_hash(self, file_path):
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except:
            return None

    def unpack_file(self, input_file, output_file=None, force=False):
        """Unpack a single UPX-compressed file"""
        if not self.upx_path:
            return False, "UPX executable not found. Please install UPX or specify path."

        if not os.path.exists(input_file):
            return False, f"Input file not found: {input_file}"

        # Check if file is UPX-packed
        if not force and not self.is_upx_packed(input_file):
            return False, f"File does not appear to be UPX-packed: {input_file}"

        # Determine output file name
        if output_file is None:
            input_path = Path(input_file)
            output_file = str(input_path.with_name(f"{input_path.stem}_unpacked{input_path.suffix}"))

        # Copy input file to output location for unpacking
        try:
            shutil.copy2(input_file, output_file)
        except Exception as e:
            return False, f"Failed to copy file: {e}"

        # Get original file hash
        original_hash = self.get_file_hash(input_file)

        # Run UPX unpacker
        try:
            cmd = [self.upx_path, '-d', output_file]

            if self.verbose:
                print(f"Running command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                # Verify unpacking was successful
                unpacked_hash = self.get_file_hash(output_file)

                if unpacked_hash == original_hash:
                    return False, "File unchanged - may not have been UPX packed"

                return True, f"Successfully unpacked to: {output_file}"
            else:
                # Clean up failed output file
                if os.path.exists(output_file):
                    os.remove(output_file)

                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                return False, f"UPX unpacking failed: {error_msg}"

        except subprocess.TimeoutExpired:
            return False, "UPX unpacking timed out"
        except Exception as e:
            return False, f"Error running UPX: {e}"

    def unpack_directory(self, directory, recursive=False, extensions=None):
        """Unpack all UPX files in a directory"""
        if extensions is None:
            extensions = ['.exe', '.dll', '.sys', '.bin']

        results = []

        if recursive:
            pattern = '**/*'
        else:
            pattern = '*'

        for file_path in Path(directory).glob(pattern):
            if file_path.is_file():
                # Check file extension
                if file_path.suffix.lower() in extensions:
                    success, message = self.unpack_file(str(file_path))
                    results.append({
                        'file': str(file_path),
                        'success': success,
                        'message': message
                    })

        return results

    def batch_unpack(self, file_list):
        """Unpack multiple files from a list"""
        results = []

        for file_path in file_list:
            success, message = self.unpack_file(file_path)
            results.append({
                'file': file_path,
                'success': success,
                'message': message
            })

        return results

def main():
    import argparse

    parser = argparse.ArgumentParser(description='UPX Unpacker - Automated UPX decompression tool')
    parser.add_argument('input', help='Input file, directory, or file list')
    parser.add_argument('-o', '--output', help='Output file name (for single file)')
    parser.add_argument('-d', '--directory', action='store_true', 
                       help='Process directory')
    parser.add_argument('-r', '--recursive', action='store_true', 
                       help='Process directory recursively')
    parser.add_argument('-f', '--force', action='store_true', 
                       help='Force unpacking even if UPX signature not detected')
    parser.add_argument('-v', '--verbose', action='store_true', 
                       help='Verbose output')
    parser.add_argument('--upx-path', help='Path to UPX executable')
    parser.add_argument('--extensions', 
                       default='.exe,.dll,.sys,.bin',
                       help='File extensions to process (comma-separated)')

    args = parser.parse_args()

    # Initialize unpacker
    unpacker = UPXUnpacker()
    unpacker.verbose = args.verbose

    if args.upx_path:
        unpacker.upx_path = args.upx_path

    if not unpacker.upx_path:
        print("ERROR: UPX executable not found!")
        print("Please install UPX or specify path with --upx-path")
        print("Download UPX from: https://upx.github.io/")
        sys.exit(1)

    print(f"Using UPX: {unpacker.upx_path}")

    # Parse extensions
    extensions = [ext.strip() for ext in args.extensions.split(',')]
    extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in extensions]

    # Process input
    if args.directory:
        # Directory mode
        if not os.path.isdir(args.input):
            print(f"ERROR: Directory not found: {args.input}")
            sys.exit(1)

        print(f"Processing directory: {args.input}")
        print(f"Extensions: {', '.join(extensions)}")

        results = unpacker.unpack_directory(args.input, args.recursive, extensions)

        success_count = sum(1 for r in results if r['success'])
        total_count = len(results)

        print(f"\nResults: {success_count}/{total_count} files successfully unpacked")

        for result in results:
            status = "SUCCESS" if result['success'] else "FAILED"
            print(f"[{status}] {result['file']}: {result['message']}")

    else:
        # Single file mode
        if not os.path.exists(args.input):
            print(f"ERROR: File not found: {args.input}")
            sys.exit(1)

        print(f"Processing file: {args.input}")

        # Check if file appears to be UPX packed
        if unpacker.is_upx_packed(args.input):
            print("UPX signature detected")
        elif not args.force:
            print("WARNING: UPX signature not detected. Use --force to unpack anyway.")

        success, message = unpacker.unpack_file(args.input, args.output, args.force)

        if success:
            print(f"SUCCESS: {message}")
        else:
            print(f"FAILED: {message}")
            sys.exit(1)

if __name__ == "__main__":
    main()
