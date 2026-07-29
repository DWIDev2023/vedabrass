import html, re

class BlogFormatter:
    # Converts simple markdown-like syntax into clean semantic HTML.
    @staticmethod
    def to_html(text: str) -> str:
        if not text:
            return ""

        text = text.replace("\r\n", "\n").strip()
        lines = text.split("\n")
        html_output = []
        paragraph = []

        in_ul = False
        in_ol = False

        def close_paragraph():
            nonlocal paragraph

            if paragraph:
                html_output.append(
                    "<p>{}</p>".format(
                        "<br>".join(paragraph)
                    )
                )
                paragraph = []

        def close_lists():
            nonlocal in_ul, in_ol

            if in_ul:
                html_output.append("</ul>")
                in_ul = False

            if in_ol:
                html_output.append("</ol>")
                in_ol = False

        for line in lines:
            line = line.rstrip()

            if not line.strip():
                close_paragraph()
                close_lists()
                continue

            # H1
            if line.startswith("# "):
                close_paragraph()
                close_lists()

                html_output.append(
                    f"<h1>{BlogFormatter.inline(line[2:])}</h1>"
                )

                continue

            # H2
            if line.startswith("## "):
                close_paragraph()
                close_lists()

                html_output.append(
                    f"<h2>{BlogFormatter.inline(line[3:])}</h2>"
                )

                continue

            # H3
            if line.startswith("### "):
                close_paragraph()
                close_lists()

                html_output.append(
                    f"<h3>{BlogFormatter.inline(line[4:])}</h3>"
                )

                continue

            # Horizontal Rule
            if line.strip() == "---":
                close_paragraph()
                close_lists()

                html_output.append("<hr>")

                continue

            # Blockquote
            if line.startswith("> "):
                close_paragraph()
                close_lists()

                html_output.append(
                    f"<blockquote>{BlogFormatter.inline(line[2:])}</blockquote>"
                )

                continue

            # UL
            if line.startswith("- "):
                close_paragraph()

                if not in_ul:
                    close_lists()
                    html_output.append("<ul>")
                    in_ul = True

                html_output.append(
                    f"<li>{BlogFormatter.inline(line[2:])}</li>"
                )

                continue

            # OL
            if re.match(r"^\d+\.\s", line):
                close_paragraph()

                if not in_ol:
                    close_lists()
                    html_output.append("<ol>")
                    in_ol = True

                item = re.sub(r"^\d+\.\s*", "", line)

                html_output.append(
                    f"<li>{BlogFormatter.inline(item)}</li>"
                )

                continue

            paragraph.append(
                BlogFormatter.inline(line)
            )

        close_paragraph()
        close_lists()

        return "\n".join(html_output)
    

    @staticmethod
    def inline(text):
        text = html.escape(text)

        # Bold
        text = re.sub(
            r"\*\*(.*?)\*\*",
            r"<strong>\1</strong>",
            text,
        )

        # Italic
        text = re.sub(
            r"\*(.*?)\*",
            r"<em>\1</em>",
            text,
        )

        # Links
        text = re.sub(
            r"\[(.*?)\]\((.*?)\)",
            r'<a href="\2">\1</a>',
            text,
        )

        return text
    
