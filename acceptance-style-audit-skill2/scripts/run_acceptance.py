#!/usr/bin/env python3
import argparse
import os
import subprocess
import tempfile


def main():
    p = argparse.ArgumentParser(description="Run style acceptance from implementation JSON and design HTML")
    p.add_argument("--impl-json", required=True, help="Path to implementation JSON")
    p.add_argument("--design-html", required=True, help="Path to design HTML file")
    p.add_argument("--format", default="markdown", choices=["markdown", "json"])
    p.add_argument("--no-ignore-adaptive", action="store_true")
    p.add_argument("--no-ignore-shell", action="store_true")
    args = p.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    html2json = os.path.join(script_dir, "html_to_json.py")
    compare = os.path.join(script_dir, "compare_style_json.py")

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        design_json = tf.name

    try:
        subprocess.run([
            "python3", html2json,
            "--input", args.design_html,
            "--output", design_json,
        ], check=True)

        cmd = [
            "python3", compare,
            "--design", design_json,
            "--impl", args.impl_json,
            "--format", args.format,
        ]
        if args.no_ignore_adaptive:
            cmd.append("--no-ignore-adaptive")
        if args.no_ignore_shell:
            cmd.append("--no-ignore-shell")

        subprocess.run(cmd, check=True)
    finally:
        if os.path.exists(design_json):
            os.remove(design_json)


if __name__ == "__main__":
    main()
