#!/usr/bin/env python3
import argparse
import json
from html.parser import HTMLParser


class NodeBuilder(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.root = None

    def handle_starttag(self, tag, attrs):
        node = {"type": tag}
        attr_map = dict(attrs)
        if "style" in attr_map:
            node["style"] = self.parse_style(attr_map["style"])
        if "class" in attr_map:
            node["class"] = " ".join(attr_map["class"].split())
        if "id" in attr_map:
            node["id"] = attr_map["id"]

        if self.stack:
            parent = self.stack[-1]
            parent.setdefault("children", []).append(node)
        else:
            self.root = node
        self.stack.append(node)

    def handle_endtag(self, tag):
        if self.stack:
            self.stack.pop()

    def handle_data(self, data):
        text = data.strip()
        if not text or not self.stack:
            return
        node = self.stack[-1]
        if "children" not in node and "text" not in node:
            node["text"] = text
        elif "children" in node:
            node["children"].append({"type": "text", "text": text})
        else:
            node["children"] = [{"type": "text", "text": text}]
            node.pop("text", None)

    @staticmethod
    def parse_style(style_str):
        out = {}
        for part in style_str.split(";"):
            part = part.strip()
            if not part or ":" not in part:
                continue
            k, v = part.split(":", 1)
            out[k.strip()] = v.strip()
        return out


def main():
    parser = argparse.ArgumentParser(description="Convert HTML snippet/file to nested JSON")
    parser.add_argument("--html", help="Raw HTML string")
    parser.add_argument("--input", help="Path to HTML file")
    parser.add_argument("--output", help="Path to output JSON file")
    args = parser.parse_args()

    if not args.html and not args.input:
        raise SystemExit("Provide --html or --input")

    html = args.html
    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            html = f.read()

    p = NodeBuilder()
    p.feed(html)
    result = p.root or {}

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
